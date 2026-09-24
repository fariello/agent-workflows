# IPD: Make a run status name its refusing authority, and make an answerable refusal a question

- Date: 2026-09-24
- Kind: orchestrator
- Concern: AN OPERATOR READING A RUN SUMMARY CANNOT TELL SUCCESS FROM WORK THAT IS NOWHERE, AND A REFUSAL THEY COULD ANSWER IN ONE TURN COSTS THEM AN ITEM PLUS EVERYTHING BEHIND IT. Both were measured on one run, `run-20260924T050407Z-3108751`. The vocabulary half: `substantially-complete` described BOTH `xdvglg` (6/6 items performed, work correct, landed once a human re-issued its receipt) AND `7p3tt8` (ZERO of 5 items performed, empty evidence), while `failed-safely` described `m7gvuz`, the only plan in the run that refused ITSELF rather than tick a V-item it could not honor. The word an operator reads is anti-correlated with what happened. The response half: `xdvglg`'s refusal was two findings a running agent could have answered, and instead the item failed and `04vf1h` and `a5wdne` cascaded `dependency-blocked` behind it. Neither half is cosmetic: the vocabulary's worst token is a member of the live dependency bar, and the failed item blocked two others.
- Scope: Orchestrate three children that together make a run status name its refusing authority, make an answerable finalize refusal a question, and show an operator whether each item landed in `main`. This plan holds ORCHESTRATION ONLY: every deliverable belongs to a child (`cyamvi` the vocabulary and its exhaustiveness guard, `787hb4` the send-back, `9x7otz` the `Landed` column and the eight spec amendments), and this file contributes no code, no test, and no record of its own. EXCLUDES changing WHICH gate refuses what, in every child without exception.
- Scope-Paths: .aw/records/plans/pending/20260924-statusvocab-00-zngiya-make-a-run-status-name-its-refusing-authority-and-make-an-an.ipd.md
- Item-Dependencies: none
- Status: to-review
- Set: statusvocab
- Order: 0
- Highest E allocated: 03
- Priority: high
- Work-Kind: bug
- Blocks-Release: next
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: zngiya

## Workflow history
- 2026-09-24 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored as part of splitting the oversized cyamvi plan into a Set on maintainer instruction; complete enough to critique.

- 2026-09-24 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Make the word an operator reads answer the only two questions they have - is this work in `main`, and whose output do I read next - and stop the runner failing an item over a question it could have asked.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: sequence the children

- [ ] E-01 CONFIRM cyamvi REACHED executed
  - Depends on: none
  - Expected outcome: `cyamvi` reads `- Status: executed` on disk.
  - Execution state: pending
  Order 01 defines the vocabulary, moves every reader and writer onto it, and lands the tree-wide exhaustiveness guard. It must be first because both siblings depend on the tokens existing: Order 03 declares `executed:cyamvi` explicitly.

- [ ] E-02 CONFIRM 787hb4 REACHED executed
  - Depends on: none
  - Expected outcome: `787hb4` reads `- Status: executed` on disk.
  - Execution state: pending
  Order 02 changes the RESPONSE to two finalize findings and is INDEPENDENT of the vocabulary, so it may execute before or after Order 01. Sequenced second only because Order 01 is the larger change and a reviewer reads them in this order.

- [ ] E-03 CONFIRM 9x7otz REACHED executed
  - Depends on: E-01
  - Expected outcome: `9x7otz` reads `- Status: executed` on disk.
  - Execution state: pending
  Order 03 adds the `Landed` column and amends the eight specs. It MUST follow Order 01: a spec amended before the code emits the new vocabulary would leave the contract ahead of the implementation, which is why it declares `executed:cyamvi`.

## Child IPDs, sequence, and dependencies

| Order | Id | Plan | Purpose | Depends on |
| --- | --- | --- | --- | --- |
| 01 | cyamvi | `.aw/records/plans/pending/20260924-statusvocab-01-cyamvi-rename-the-terminal-status-vocabulary-so-a-label-names-its-r.ipd.md` | Define the twelve-label vocabulary and the legacy alias map, move every reader then every writer onto it, promote `interrupted` into `TERMINAL_STATES`, narrow the dependency bar to `{executed}`, fix `artifact_audit`'s `"complete"` coercion, and land the tree-wide exhaustiveness guard that makes a partial rename unshippable. | none |
| 02 | 787hb4 | `.aw/records/plans/pending/20260924-statusvocab-02-787hb4-send-back-an-answerable-finalize-refusal-instead-of-failing.ipd.md` | Move the two ANSWERABLE finalize-refusal classes (stale receipt, `Scope-Paths` reduction) onto the send-back path that already exists, leaving the fence-widening class terminal. | none |
| 03 | 9x7otz | `.aw/records/plans/pending/20260924-statusvocab-03-9x7otz-show-whether-each-item-landed-in-main-and-amend-the-specs-th.ipd.md` | Add the `Landed` column derived from the plan's terminal DIRECTORY, and amend the eight specs that name a legacy status token. | `executed:cyamvi` |

## Completion criteria (the whole Set is done only when)

1. Every terminal status a fresh run writes NAMES THE AUTHORITY THAT REFUSED, and no run writes a legacy token. Measured by the exhaustiveness guard Order 01 lands, shown RED before green.
2. Every legacy token remains READABLE, forever, so a gitignored historical run directory and a fresh clone are both parseable. Measured by reading a synthetic run directory carrying all eleven legacy tokens.
3. The dependency bar is `{executed}` alone, so a plan whose work never reached `main` can no longer satisfy another plan's prerequisite.
4. A finalize refusal an agent can answer in one turn is ASKED rather than failed, while a fence-widening mutation stays terminal.
5. An operator can read ONE COLUMN and know whether an item's work is in `main`, derived from the plan's directory and from no self-report.
6. No spec describes a vocabulary the runner no longer writes, and each amended spec states that legacy tokens stay readable.
7. `python3 -m pytest` is green, with the baseline re-derived at execution.

## Cross-IPD validation

- ORDER MATTERS AND IS DECLARED: Order 03 declares `executed:cyamvi` because a spec amended before the code emits the new vocabulary would leave the contract ahead of the implementation. Order 02 declares NO dependency and is genuinely independent - it changes the RESPONSE to two findings and touches neither the vocabulary nor a gate - so it may execute in any position and may be approved alone.
- THE READER-BEFORE-WRITER ORDERING IS INTERNAL TO ORDER 01 and is not expressible as a Set dependency: its E-02 moves every reader before its E-03 changes any writer, because a writer emitting a token no reader understands would break a live run mid-flight. A reviewer checking Set ordering should confirm that ordering inside Order 01 rather than looking for it here.
- NO CHILD MAY CHANGE WHICH GATE REFUSES WHAT. This is the Set's one standing exclusion and it is repeated in all three children. A child that finds a gate genuinely wrong should report it, not fix it here.

### Set-level findings (carried from authoring)

- F-01 THE SET WAS SPLIT FROM ONE OVERSIZED PLAN, ON THE MAINTAINER'S INSTRUCTION, and the original is preserved as Order 01 rather than rewritten. The single plan carried 9 E-items and 26 declared scope paths spanning 17 modules, every test file, and 8 specs, which is too large to review or execute in one pass. The split follows the dependency seams that already existed in its own checklist: the vocabulary and its guard (Order 01), the independent send-back fix (Order 02), and the two items that must follow the vocabulary (Order 03).
- F-02 TWO REVIEW ROUNDS ALREADY HARDENED ORDER 01 AND THEIR FINDINGS ARE CARRIED, NOT DISCARDED. Round 1 corrected a false harm claim (the dependency bar is consumed by orchestrator retirement and the cascade pass, NOT by `edge_satisfied`, whose live branch already reads the directory), an overstated measurement (three false negatives, not zero), an unsatisfiable validation bar, and ten census counts that had already drifted. Round 2 measured all 209 legacy `blocked` items and found FOUR producers answering to three authorities, taking the vocabulary from ten labels to twelve.
- F-03 ORDER 02 IS INDEPENDENT AND COULD SHIP ALONE, which is stated so a reviewer may approve the Set partially. It changes which findings the runner treats as retryable and touches neither the vocabulary nor any gate's logic.

### Conventions this Set was authored against

- AN ORCHESTRATOR HOLDS ORCHESTRATION, NOT WORK OF ITS OWN, and its checklist must be typed child-tracking rows (`IPD-S407`, landed by `orchtyped` Order 04 `68uhp0`). The runner RETIRES a parent once every child is `executed` and deliberately SKIPS the pre-transition E/V checkpoint, so a step parked here would be marked complete having never run. Every row above is a child confirmation; the reasoning lives on the continuation lines.
- THE ORCHESTRATOR COVERAGE GATE asks a model whether a parent carries work no child covers, and refuses a run unattended when it does. This parent was authored to pass it by construction: the three deliverables are each owned by exactly one child and named in the table.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Deferred / out of scope (with reason)

- Changing WHICH gate refuses what: excluded from every child. Order 01 renames outcomes, Order 02 changes the response to a finding, Order 03 adds a derived column; none moves a gate.
- A thirteenth label such as `fail-finalize` or `fail-receipt`: deferred with the test that would justify one, recorded in OQ-01, because adding a label now would invalidate Round 2's 209-item census and send Order 01 to a third review.
- Rewriting historical run directories: they are gitignored and unmigratable, which is why Order 01 keeps both vocabularies readable forever.

## Scope check

This plan sequences three children and contributes nothing else. Each deliverable is owned by exactly one child and named in the child table. The Set excludes gate changes entirely.

## Required tests / validation

Each child validates itself; this plan runs no tests of its own. The Set-level bar is that `python3 -m pytest` is green after each child, with the baseline re-derived at execution rather than trusted from authoring.

## Open questions

- [ ] OQ-01 Should a thirteenth label name the finalize gate specifically (`fail-finalize`), separating it from the lint/checkpoint refusals Order 01 folds into `fail-gate`? Blocking: no. RECOMMENDATION: not in this Set, and decide it with THIS TEST - a label is earned when it sends the operator SOMEWHERE DIFFERENT TO LOOK, not merely when it has a different remedy. `fail-begin`, `fail-lane` and `fail-gate` pass that test (the plan's open questions, `git branch --list 'aw/lane/*'`, the lifecycle output). `fail-finalize` points at the same output as `fail-gate`, so on that test it is a RENAMING of `fail-gate` rather than an addition - and arguably a better name, since "finalize" is a command an operator runs while "gate" is internal vocabulary. `fail-receipt` fails the test outright and would be actively harmful: "receipt" is an internal artifact under `.aw/state/` with no operator-facing command, so a reader has no way to learn what it means. RECORDED because the maintainer raised it and because without a stated test this vocabulary will grow one honest-looking label at a time.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `cyamvi`'s path under `.aw/records/plans/executed/` and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `787hb4`'s path under `.aw/records/plans/executed/` and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `9x7otz`'s path under `.aw/records/plans/executed/` and its `- Status: executed` line, and confirm it executed AFTER `cyamvi` rather than beside it.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

Human approval required before execution. Order 01's narrowing of the dependency bar to `{executed}` should be approved explicitly, because it can turn currently-dispatchable items into `fail-depend`.
