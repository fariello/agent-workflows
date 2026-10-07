# IPD: Audit the five setdisp children together and run the Set-level checks

- Date: 2026-10-07
- Kind: child
- Concern: Orchestrator `63zo2f` (Set `setdisp`) lists Set-level checks that no single child can make: that each of the eight expected-difference assertions child 02 (`afdmn6`) records is flipped by exactly one later child; that no backlog carrier closed by children 03 and 05 was closed on a partial fix; that child 04's spec amendment landed in the same commit as its behavior; that the three retrospective parity files passed after every child; that no added test reads production source; the bare-suite failure set compared by name with the pre-Set baseline; and `aw check release-gates`. On 2026-10-06 the coverage probe refused `63zo2f` (sent back to `draft` by `gradcover` `52opph`) because those checks sat on the orchestrator, where a runner retirement marks them complete without anyone performing them. This plan performs them, after the last child.
- Scope: Measurement and reporting only. IN: run and record each Set-level check named in `63zo2f`'s Completion criteria and Cross-IPD validation, against the tree after children 01 to 05 have executed; report any failure plainly and stop the Set from being reported complete. OUT: fixing anything a check finds (a failure is reported, and the fix is a new plan); closing or editing any backlog item; editing any child plan.
- Scope-Paths: .aw/records/plans/pending/20261007-setdisp-06-7zb4ny-audit-the-five-setdisp-children-together-and-run-the-set-lev.ipd.md
- Item-Dependencies: executed:afdmn6, executed:m1jlwm, executed:m94eht, executed:vhiqo6
- Status: to-review
- From-Spec: none
- Work-Kind: chore
- Priority: medium
- From-Backlog: fcnz1r
- Set: setdisp
- Order: 6
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 7zb4ny

## Workflow history
- 2026-10-07 to-review (aw set): returned to review: Set-level checks now owned by new Order 06 7zb4ny; coverage pass recorded; open questions are non-blocking executor measurements

- 2026-10-07 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored so the Set-level checks orchestrator `63zo2f` carried have an owner; the coverage probe quoted each of them as work no child covers.
- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Perform, after the last `setdisp` child executes, every Set-level check the orchestrator `63zo2f` lists, so the Set is declared complete only when each has been run and its evidence pasted.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the child evidence

- [ ] E-01 For each of children `c6f6sj`, `afdmn6`, `m1jlwm`, `m94eht` and `vhiqo6`, confirm the plan is under `.aw/records/plans/executed/`, `aw ipd lint --phase post-transition` (run with `AW_NO_REEXEC=1`) reports conforming, and every `V-*` has non-empty `Observed evidence` and `Result: pass`. A `V-*` whose evidence is empty or only says it passed fails this check.
  - Depends on: none
  - Expected outcome: a five-row table (child, executed path, lint result, count of `V-*` with pasted evidence out of total), every row complete.
  - Execution state: pending

### Task group 2: the cross-child checks

- [ ] E-02 NO AXIS FIXED TWICE OR BY NOBODY. List the eight expected-difference assertions `afdmn6` recorded in `tests/test_set_dispatch_parity.py`, and for each the child (03 `m1jlwm`, 04 `m94eht` or 05 `vhiqo6`) whose evidence shows it flipped. Each must be flipped by exactly one child; any still unflipped must correspond to a spec `wy9aru` Section 7 axis with a live carrier (name it).
  - Depends on: E-01
  - Expected outcome: an eight-row table with exactly one flipping child or a named live carrier per row.
  - Execution state: pending

- [ ] E-03 NO CARRIER CLOSED ON A PARTIAL FIX. For each backlog item children 03 and 05 closed `done`, quote the item's own stated scope and confirm the evidence covers all of it (for the clock items, all five local-clock call sites in `backlog.py`, not one). Confirm release-gated carriers `h4fiwa` and `fv4b6s` are `done` through the evidence route and still carry their `- Blocks-Release:` line.
  - Depends on: E-02
  - Expected outcome: per closed item, its scope quoted beside the evidence covering it; `h4fiwa` and `fv4b6s` `done` with the gate line intact. Any partial close is reported as a failure.
  - Execution state: pending

- [ ] E-04 THE SPEC AMENDMENT TRAVELLED WITH ITS BEHAVIOR, AND NO TEST READS SOURCE. Show that child 04's amendment to spec `1525-02` R2 and its sidecar behavior change are in the same commit (`git show --stat <commit>` listing both), and that child 05's commits touch no `.spec.md`. Grep every test file the five children added for `inspect`, `ast.parse`, reads of `agent_workflows/*.py` and caller counting, and confirm none.
  - Depends on: E-03
  - Expected outcome: one commit listing both the spec and the behavior file; no `.spec.md` in child 05's commits; the source-read grep returns nothing.
  - Execution state: pending

### Task group 3: the whole tree

- [ ] E-05 THE THREE RETROSPECTIVE PARITY FILES PASSED AFTER EVERY CHILD. From each child's own pasted evidence, show the three files passing at that child's boundary; then run them once more now, both in the local timezone and under `TZ=UTC`, and paste both runs.
  - Depends on: E-04
  - Expected outcome: five per-child pass records plus two current passing runs (local and `TZ=UTC`).
  - Execution state: pending

- [ ] E-06 THE BARE SUITE AND THE RELEASE GATES. Run `python3 -m pytest` bare, paste the `N passed` line, and compare its failure SET by test id with the baseline the first child recorded before the Set began; any new id not named in advance by a child is a failure. Run `AW_NO_REEXEC=1 python3 -m agent_workflows check release-gates` and paste it.
  - Depends on: E-05
  - Expected outcome: the failure-set comparison by test id, with no unexplained new id; `check release-gates` with no new finding.
  - Execution state: pending

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR CARRIES NO WORK OF ITS OWN (`AGENTS.md`); a whole-Set check needs a child that runs after the others, which is this plan.
- RUN THE SUITE BARE (`AGENTS.md` execution contract).
- `AW_NO_REEXEC=1` keeps the measured package the one in the tree under test.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The checks were on the orchestrator, with no owner. | `63zo2f`'s Completion criteria and Cross-IPD validation; its 2026-10-06 coverage record quoting them as uncovered |
| F-02 | Only a plan that runs after all five children can make them. | each check compares or audits two or more children's results |

## Proposed changes (ordered, validatable)

1. Audit each child's evidence (E-01).
2. The three cross-child checks (E-02 to E-04).
3. Parity files and the whole suite (E-05, E-06).

## Deferred / out of scope (with reason)

- FIXING WHAT A CHECK FINDS. This plan reports; a failure needs its own plan.
  - Carrier-Declined: measurement-only by design; a fix inside an audit would audit its own work

## Scope check

- Over-scope: none. Only this plan's own file is edited (its evidence).
- Under-scope: none.

## Required tests / validation

Each E-item's commands, run and pasted as its V-item requires. No new test is written.

## Spec / documentation sync

None. This plan edits no spec or document.

## Open questions

### OQ-01: Should this be a child rather than the orchestrator's own checklist?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: a child. When the runner retires an orchestrator it skips the orchestrator's own checks, so they would be marked done without being run (`AGENTS.md`, spec `77tr3o` R-12). A child is executed and verified like any other plan.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the five-row table and, for each child, the lint command and its output.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the eight-row table with, per row, the quoted assertion and the evidence line from the flipping child (or the live carrier's id6 and status).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste, per closed item, its quoted scope and the covering evidence; paste `grep -n '^- Status:\|^- Blocks-Release:'` for `h4fiwa` and `fv4b6s`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `git show --stat` for child 04's amendment commit, the list of child 05's commits with their changed paths, and the source-read grep returning nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the five per-child pass records and the two current runs with their pass counts.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the bare `python3 -m pytest` summary line, the baseline and current failure sets by id with their difference, and the `check release-gates` output. Paste `aw ipd lint` on this plan conforming and `git diff --cached --name-only` before committing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Measurement only: commit only this plan's own file (its evidence) through `aw commit <plan> -- <path>`; never push. Paste actual output for every `V-*`. A failed check is reported and the plan is NOT finalized as passing. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.
