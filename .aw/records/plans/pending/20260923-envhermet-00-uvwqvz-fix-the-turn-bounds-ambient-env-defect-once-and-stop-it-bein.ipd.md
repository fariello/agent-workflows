# IPD: Fix the turn-bounds ambient-env defect once and stop it being filed a twenty-fifth time

- Date: 2026-09-23
- Kind: orchestrator
- Concern: A SINGLE NON-HERMETIC TEST ASSERTION HAS PRODUCED TWENTY-THREE OPEN BACKLOG ITEMS, AND BOTH HALVES OF THAT SENTENCE ARE DEFECTS. The DEFECT half: `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped` reads the AMBIENT `OPENCODE_CONFIG_CONTENT`, which `run_opencode` always sets for a turn, so the file is green for a human (`144 passed`) and red for every lane agent (`1 failed, 143 passed`, measured at HEAD `22cf67d9`). The PROCESS half: nothing warns a filer that the item already exists, so agents hitting it kept filing it; `uj5g58` counted 18 and the live count is 23, meaning six arrived after the item that counted them.
  THESE TWO MUST SHIP TOGETHER, WHICH IS THE ONLY REASON THIS SET EXISTS. Fixing only the test leaves the next environment-sensitive defect free to be filed twenty times over; fixing only the guard leaves twenty-three live release blockers describing a real red test. Each child is independently correct and independently reviewable, so the Set is an ordering device and not a bundle.
  THE COST IS CONCENTRATED IN FALSE EVIDENCE, NOT IN UNTIDINESS. All twenty-three carry `- Blocks-Release: next`, so one test defect is presented to the release gate as twenty-three blockers. Worse, an agent following the execution contract measures a baseline and compares failure sets by node id; this failure appears in both measurements and cancels, so the common outcome is a wasted investigation and the dangerous outcome is an agent that either "fixes" a correct test or learns to ignore a red node in a file where a genuine failure may appear next.
- Scope: Order and track the two children this needs. IN: child 01 (`heglfv`) makes the turn-bounds policy assertions read the constructed child env rather than the ambient one, preserving the `R4.1` guarantee; child 02 (`fwgq2u`) gives `aw backlog new` an advisory near-duplicate guard following `aw graduation`'s shipped precedent. OUT, and owned by neither child: retroactively consolidating the twenty-three items (a records act needing human judgement about which filing survives, safe only once child 01 has landed); removing `OPENCODE_CONFIG_CONTENT` from `run_opencode`, which carries the turn's configuration; and the `AW_EXECUTION_ROLE` variant some filings describe, which `conftest.py` already scrubs and whose residue `rolevac` `8i0xa7` owns.
- Scope-Paths: .aw/records/plans/pending/20260923-envhermet-01-heglfv-make-the-turn-bounds-policy-assertions-read-the-constructed.ipd.md, .aw/records/plans/pending/20260923-envhermet-02-fwgq2u-give-aw-backlog-new-a-near-duplicate-guard-so-one-defect-can.ipd.md
- Item-Dependencies: none
- Status: to-review
- Set: envhermet
- Order: 0
- Highest E allocated: 02
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: uvwqvz
- From-Backlog: uj5g58
- Blocks-Release: next

## Workflow history

- 2026-09-23 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from the twenty-three-item turn-bounds family plus `uj5g58`. `- Blocks-Release: next` is INHERITED; every member carries it.
  THIS PARENT CARRIES ORCHESTRATION ONLY, DELIBERATELY. Per `AGENTS.md`, a runner RETIRES an orchestrator once every child is `executed` and SKIPS the pre-transition E/V checkpoint, so any work parked here would be marked complete having never been performed. Both E-items below are child-completion checks, and the two substantive deliverables belong to `heglfv` and `fwgq2u`. The one thing that might have been parent-only work, consolidating the twenty-three items, is explicitly declared OUT rather than left implicit, because it needs human judgement and would otherwise be exactly the uncovered-parent-work the coverage gate refuses on.
  ORDER IS MEANINGFUL BUT NOT A HARD DEPENDENCY: child 01 fixes the defect that generated the duplicates and child 02 stops the next one recurring, so 01 first is the useful sequence; neither declares an `- Item-Dependencies:` edge on the other because they touch disjoint files (`tests/test_turn_bounds.py` versus `agent_workflows/backlog.py`) and either can land alone.

## Goal

Land both halves of the turn-bounds duplication problem: the test defect that generated twenty-three filings, and the missing guard that let them all be filed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: children

- [ ] E-01 CONFIRM CHILD 01 (`heglfv`) REACHED `executed`: the turn-bounds policy assertions read the constructed child env, the file is green with `OPENCODE_CONFIG_CONTENT` both set and unset, and the `R4.1` assertion was not weakened.
  - Depends on: none
  - Expected outcome: `heglfv` is in `.aw/records/plans/executed/` with every `V-*` carrying observed evidence, including the pasted green run with the variable SET and the demonstration that the fixed test can still fail.
  - Execution state: pending

- [ ] E-02 CONFIRM CHILD 02 (`fwgq2u`) REACHED `executed`: `aw backlog new` reports plausible existing items, never refuses, states its own detection limits, and is proved against fixtures derived from the twenty-three filings plus a negative control.
  - Depends on: none
  - Expected outcome: `fwgq2u` is in `.aw/records/plans/executed/` with every `V-*` carrying observed evidence, including the measured added latency and the negative-control assertion.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | Plan | Status | Owns |
| --- | --- | --- | --- | --- |
| 01 | `heglfv` | `20260923-envhermet-01-heglfv-make-the-turn-bounds-policy-assertions-read-the-constructed.ipd.md` | `to-review` | The DEFECT: make the turn-bounds policy assertions read the constructed child env, not the ambient one, preserving `R4.1`. Touches `tests/test_turn_bounds.py`. |
| 02 | `fwgq2u` | `20260923-envhermet-02-fwgq2u-give-aw-backlog-new-a-near-duplicate-guard-so-one-defect-can.ipd.md` | `to-review` | The PROCESS: give `aw backlog new` an advisory near-duplicate guard following `aw graduation`'s precedent. Touches `agent_workflows/backlog.py`. |

SEQUENCE IS USEFUL BUT NOT ENFORCED. Child 01 fixes the defect that generated the twenty-three filings and child 02 stops the next such defect recurring, so 01-then-02 is the informative order. Neither declares an `- Item-Dependencies:` edge on the other, deliberately: they touch DISJOINT files, so either may land alone and both may execute in parallel isolated worktrees without contending.

## Completion criteria (the whole Set is done only when)

1. `tests/test_turn_bounds.py` passes with `OPENCODE_CONFIG_CONTENT` both SET and UNSET, and the `R4.1` assertion is unchanged in strength (child 01).
2. The fixed test is demonstrated still able to FAIL under a deliberate mutation, so the hermeticity fix did not make it vacuous (child 01).
3. `aw backlog new` reports plausible existing items, never refuses, and states its own detection limits in its output (child 02).
4. The guard is proved against fixtures derived from the twenty-three real filings AND shown not to flag a genuinely distinct negative-control pair (child 02).
5. Both children are in `.aw/records/plans/executed/` with every `V-*` carrying observed evidence.

NOT A COMPLETION CRITERION, stated so nobody adds it later: consolidating the twenty-three duplicate items. It needs human judgement (OQ-01) and is declared out of scope; a retiring orchestrator would otherwise mark it done unperformed.

## Cross-IPD validation

- CID-1 THE TWO CHILDREN MUST NOT BOTH EDIT ONE FILE. Child 01 is confined to `tests/test_turn_bounds.py` and child 02 to `agent_workflows/backlog.py` plus its new test module. Verify by diffing each child's committed paths against its declared `- Scope-Paths:` after both land; an overlap means one child widened silently.
- CID-2 CHILD 02's GUARD MUST NOT DEPEND ON THE TWENTY-THREE STAYING OPEN. Its tests use fixtures, not the live tree (`jb0sc1`, `caf5ed`, `agrlvw` all record that hazard), so child 01 landing (or a later consolidation closing those items) must not red child 02's suite. Verify by running child 02's tests after child 01 is executed.
- CID-3 NEITHER CHILD MAY WEAKEN A GUARANTEE TO PASS. Child 01 must keep `R4.1`'s "no denial policy on a non-isolated turn" assertion, and child 02 must keep the advisory non-refusing. Verify by quoting both from the executed plans' evidence.

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR HOLDS ORCHESTRATION, NOT WORK OF ITS OWN (`AGENTS.md`): retirement skips the E/V checkpoint, so parent-only work would be discharged unperformed. Both items here are child-completion checks by construction, and the consolidation task that would have been parent-only work is declared out of scope instead.
- THE TWO CHILDREN TOUCH DISJOINT FILES, so they carry no dependency edge and may execute in either order or in parallel isolated worktrees.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | BLOCKER | `tests/test_turn_bounds.py` | The policy assertion reads the ambient `OPENCODE_CONFIG_CONTENT`, so the file is green for a human and red for every lane agent. Owned by child 01. | bare `144 passed`; with the variable set `1 failed, 143 passed` |
| F-2 | HIGH | `aw backlog new` | No near-duplicate guard, so the same defect was filed 23 times; `uj5g58` counted 18 and six arrived after it. Owned by child 02. | live enumeration of 23 open items |
| F-3 | MED | release gating | All 23 carry `Blocks-Release: next`, so one test defect reads as 23 release blockers. | each item's front matter |
| F-4 | MED (scope) | this parent | Consolidating the 23 is the one task no child covers; it is declared OUT rather than parked here, because a retiring orchestrator would mark it done unperformed. | `AGENTS.md` orchestrator-coverage rule |

## Proposed changes (ordered, validatable)

1. Child 01 (`heglfv`) makes the turn-bounds assertions hermetic without weakening `R4.1`.
2. Child 02 (`fwgq2u`) adds the advisory near-duplicate guard at filing time.

## Deferred / out of scope (with reason)

- RETROACTIVELY CONSOLIDATING THE TWENTY-THREE ITEMS. Needs human judgement about which filing survives and what each records; safe only after child 01 lands. Declared out rather than parked on this parent, per F-4.
- REMOVING `OPENCODE_CONFIG_CONTENT` FROM `run_opencode`. It carries the turn's configuration; changing the runner to satisfy a test inverts the priority.
- THE `AW_EXECUTION_ROLE` VARIANT some filings describe. Already scrubbed in `conftest.py`; the residual vacuity it caused is owned by `rolevac` `8i0xa7`.
- EXTENDING THE DUPLICATE GUARD TO OTHER RECORD TYPES. Out of child 02's measured corpus; a successor plan if its measurement shows the pattern elsewhere.

## Scope check

- Over-scope: this plan edits NOTHING but its own child plans' tracking. The two `- Scope-Paths:` entries are the children themselves.
- Under-scope: if a third defect surfaces in this family during execution, add a CHILD for it and a row here rather than performing it on this parent, per `AGENTS.md`.

## Required tests / validation

- No test runs on this parent: it performs no code change. Each child runs the bare `python3 -m pytest` and pastes its own summary line per the execution contract.
- This plan's validation is that both children reached `executed` with their own `V-*` evidence present, which V-01 and V-02 verify by inspection.

## Spec / documentation sync

- N/A for this parent: it changes no code and no contract. Child 01 notes that `R4.1` is unchanged in strength; child 02 updates `aw backlog new`'s documented behavior.

## Open questions

### OQ-01: Should the twenty-three duplicates be consolidated once child 01 lands?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking, and deliberately not performed by this Set. Once child 01 fixes the defect, the twenty-three become reports of a FIXED defect and could be closed citing it, which would remove twenty-three spurious release blockers from the board. It needs a human because the filings are not identical: some name a different test method, at least two attribute the failure to `AW_EXECUTION_ROLE` instead (a different cause, already scrubbed), and a bulk close keyed on a similarity judgement is exactly the automatic-close this Set's child 02 argues against for good reason. Recommend a separate human-approved records change after child 01 is `executed`.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `heglfv`'s path shown under `.aw/records/plans/executed/`, and its `V-02` observed-evidence block quoted, showing the pasted green run with `OPENCODE_CONFIG_CONTENT` SET and the mutation proving the fixed test can still fail.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `fwgq2u`'s path shown under `.aw/records/plans/executed/`, and its `V-02`/`V-03` observed-evidence blocks quoted, showing the advisory output with stated limits, the measured latency, and the negative-control pair not flagged.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: two children, disjoint files, no dependency edge; this parent carries orchestration only.

This plan is `to-review` and requires explicit human approval before execution. It performs no code change and commits nothing beyond its own lifecycle records. Its children commit only the paths named in their own `- Scope-Paths:` via `aw commit <plan> -- <paths>`, never `git add -A`, and never push. On completion of both children, `aw ipd lint --phase pre-transition` must conform and both `V-*` items must carry observed evidence before this plan moves to `.aw/records/plans/executed/`.
