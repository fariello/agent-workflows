# IPD: Verify the whole Set against both measured incidents and record the residuals

- Date: 2026-09-07
- Kind: child
- Concern: The `integpath` Set's central claim is that verified work stops getting lost on the lane-to-main path. Four green child suites do NOT establish it: each child tests its own mechanism, while the failure the Set exists to prevent is an INTERACTION (a refusal that is terminal, times a recovery route the hook blocks, times a resume that orphans the lane). So the whole-Set verification is real execution work that somebody must perform.
  IT CANNOT LIVE ON THE ORCHESTRATOR, WHICH IS WHY THIS CHILD EXISTS. The runner-owned rollup deliberately OMITS the `pre-transition` E/V checkpoint for an orchestrator (`ipd_lifecycle.ROLLUP_OMITTED_GATES['pre-transition-ev-checkpoint']`, spec `77tr3o` R-5 shape (b)) on the premise that an orchestrator's items are performed by NOBODY. Work parked on a parent is therefore marked complete having never been performed OR verified. MEASURED, not predicted: orchestrator `84j8d7` sits in `executed/` today carrying `Execution state: pending` on its E-01 and `Result: pending` on its V-01, rollup-retired by run `run-20260906T222606Z-2987341` (commit `52c2872a`), despite carrying an explicit forceful warning against exactly that. A warning addressed to a human does not constrain a code path (`k1nity`: informing an agent is necessary and not sufficient).
  THIS SHAPE MAKES IT UNSKIPPABLE. A `Kind: child` plan gets the enforced E/V checkpoint and `retire_orchestrator` REFUSES to retire a child, so the rollup cannot discharge this verification. Maintainer ruling 2026-09-07, option (b) of orchestrator `cczotj` OQ-04.
- Scope: Perform the whole-Set verification (both measured incidents, both hosts) and write the durable residuals record. Authors NO product code: every implementation belongs to children 01 through 04. This child is the Set's evidence, so its only deliverables are pasted observed evidence and one walkthrough artifact.
- Scope-Paths: .aw/records/walkthroughs, .aw/records/plans/pending
- Item-Dependencies: executed:29wvmj, executed:6sb3yu, executed:51vw4y, executed:rl67b0
- Status: to-review
- Set: integpath
- Order: 5
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 3v7wo6
- From-Backlog: 5wdoze
- Blocks-Release: next

## Workflow history
- 2026-09-07 to-review (aw set): status set to to-review

- 2026-09-07 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created to carry orchestrator `cczotj`'s E-01/E-02, demoted here by maintainer ruling on that plan's OQ-04 (option (b)) so the whole-Set verification sits where the E/V checkpoint is ENFORCED rather than where the rollup omits it. The two E-items and their evidence requirements are carried over in substance from `cczotj` rather than rewritten, so nothing the review had already hardened is lost.

## Goal

Establish, with pasted evidence on both hosts, that the two measured incidents are survived end to end, and leave a durable record of exactly what this Set closed and what it deliberately did not.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This child authors NO product code. Its execution work is whole-Set verification and the durable record; children 01 through 04 carry every change.

### Task group 1: verify the Set's central claim

- [ ] E-01 VERIFY THE WHOLE SET against the two MEASURED INCIDENTS, on BOTH hosts, after all four implementing children have executed. This is the Set's central claim and it must be falsifiable rather than asserted from four green child suites.
  REPRODUCE INCIDENT ONE (`run-20260905T050043Z-639569`): a lane finalizes, finds an overlapping dirty path in main, and the dirt clears while other work is still running. Assert the item DEFERS and later INTEGRATES with no agent turn spent, and that a `--no-verify` was NOT required at any point.
  REPRODUCE INCIDENT TWO (`mm6wuz`, 2026-09-06): an item holding a verified lane is resumed. Assert the FIRST lane is integrated rather than a second being allocated, and that `git branch --list 'aw/lane/<id6>*'` shows no `_attempt2`.
  THE STARTUP GATE (`p8ni63`) IS CONDITIONAL AND IS NOT THIS SET'S TO DELIVER. It is NOT a child of this Set, so FIRST determine whether it has landed: check whether `--allow-dirty-base` exists in either runner. If it HAS, assert it refuses a dirty base and honors its override. If it has NOT, record that plainly and MOVE ON; its absence must NOT be reported as this Set's failure, and this item is complete without it. Do not treat its absence as a reason to weaken either incident reproduction, which are the parts this Set actually owns.
  DO BOTH HOSTS EXPLICITLY. The runner suites are asymmetric (`tests/test_oc_runipd.py` collects 148 tests versus 45 in `tests/test_agy_runipd_cli.py`, measured 2026-09-07), so four green child suites can still leave an agy-side regression. If a host cannot be demonstrated, say so plainly rather than inferring from the other.
  - Depends on: none
  - Expected outcome: both incidents are survived on both hosts with no paid turns, no orphaned lanes, and no hook bypass; the startup gate's presence is DETERMINED and either exercised or recorded absent.
  - Execution state: pending

### Task group 2: record what the Set closed and did not

- [ ] E-02 RECORD WHAT THE SET CLOSED AND WHAT IT DID NOT, because this Set deliberately leaves several named things open and a reader six months from now must not have to infer which. THE ARTIFACT IS A WALKTHROUGH: write `.aw/records/walkthroughs/<YYYYMMDD>-integpath-05-3v7wo6-<slug>-walkthrough.md` per AGENTS.md's narrative-walkthrough convention. Do NOT invent a new record type and do NOT leave the artifact's type or path to the executor's judgement.
  STATE THE RESIDUALS EXPLICITLY, each already named by a child: content-based narrowing of the dirty-overlap false-positive rate (declined by the maintainer 2026-09-05 as low-value relative to the ladder); path-category allowlists (REJECTED, not deferred, because they reason about who probably wrote a file rather than whether it can conflict, which is the fail-open inference `d07nz2` prohibits); `h1ksy6`, which fixes the same function but WIDENS its input set and must be reconciled with the ladder rather than stacked on it; and `a8eufb`, which would let the runner tell its own dirt from a co-worker's and is NECESSARY BUT NOT SUFFICIENT here because trailers mark commits while the motivating incident was 130+ uncommitted files.
  RECORD WHY `76gsmv` PASSED THE HOOK AS AN ANSWERED QUESTION, NOT AN OPEN ONE. Child 01 RESOLVED it on 2026-09-07 (its OQ-01, `Status: resolved`) and this record must not re-open it: the cause is the finalize journal's LIFETIME, not anything about git. `_clear_finalize_journal` deletes the journal on successful completion (`ipd_lifecycle.py:2649`) and on every rollback path, so it exists only between finalize and its consumption, and `76gsmv` merged 22 minutes before its three siblings and still had one. The backlog item's rename explanation is conclusively ruled out: all four merges are identical in diff shape (`R061`, `R063`, `R061`, `R060`). Verify against child 01's F-12/F-13 rather than restating this from here.
  NAME THE SIBLING SETS this one does NOT cover, so the boundary is legible: `integearn` (`32ij2j`, `xtklpd`) covers a lane whose integration was never ATTEMPTED because the earned-integration gate refused, which is a different failure from the four here; `scopeattr` (`hyx1dg`) and `depreview` (`yf9fj9`) came from the same recovery sessions but are unrelated mechanisms. Do NOT cite `phawyy` as live work: it was RETRACTED and parked 2026-09-07 as false-premised (both blocked paths already persist the reason), so listing it as a sibling concern would propagate a withdrawn claim. Re-read each cited item's CURRENT status before writing the boundary section; several moved after the orchestrator was authored.
  ALSO RECORD THE ROLLUP DEFECT THIS CHILD'S EXISTENCE IS EVIDENCE OF: that an orchestrator carrying real verification work has it discharged unperformed by the rollup, measured on `84j8d7`, and that the general fix (option (c) of `cczotj` OQ-04, separate backlog against `77tr3o` R-5) is still owed. This child is the per-Set workaround, not that fix.
  - Depends on: E-01
  - Expected outcome: a walkthrough at the named path listing every residual with its reason and every sibling Set with its boundary, with `76gsmv` recorded as ANSWERED, `phawyy` recorded as RETRACTED, and the rollup defect recorded as still open; no residual is left as an unstated assumption.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A `Kind: child` plan gets the ENFORCED `pre-transition` E/V checkpoint, and `retire_orchestrator` REFUSES to retire a child. That asymmetry with the orchestrator rollup is the entire reason this plan exists as a child rather than as two items on `cczotj`.
- Walkthroughs live at `.aw/records/walkthroughs/` with a `...-walkthrough.md` suffix (AGENTS.md, durable-reference section). The artifact type is fixed by convention, not chosen by the executor.
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- This is a SHARED CHECKOUT. Run `aw runs` before starting, and never revert, stage, or clean another party's uncommitted work.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | rollup vs verification | An orchestrator's E/V items are skipped by the rollup by design, so verification parked on a parent is marked complete unperformed. This child is the structural fix for this Set. | `ipd_lifecycle.ROLLUP_OMITTED_GATES['pre-transition-ev-checkpoint']`; spec `77tr3o` R-5; `84j8d7` in `executed/` with E-01 `pending` and V-01 `pending`, retired by `run-20260906T222606Z-2987341` (`52c2872a`) |
| F-2 | HIGH | evidence sufficiency | Four green child suites cannot establish the Set's claim, because the prevented failure is an interaction across all four mechanisms. | `cczotj` gate section ("THE CLAIM THIS SET MAKES ..."); the seven-of-34 loss in `run-20260905T050043Z-639569` |
| F-3 | MEDIUM | host asymmetry | The two runner suites are unequal, so a green oc suite does not imply agy health. | measured 2026-09-07: `tests/test_oc_runipd.py` 148 collected vs `tests/test_agy_runipd_cli.py` 45 |
| F-4 | MEDIUM | baseline honesty | The suite is NOT green at HEAD; a pre-existing `test_orchestrator_retirement` failure must not be reported as this Set's. | `cczotj` gate section, BASELINE HONESTY |
| F-5 | LOW | dependency shape | All four implementing children must be `executed` before this child can verify anything, and the runner re-checks dependencies at dispatch, so declaring all four is correct rather than redundant. | `- Item-Dependencies:` above; AGENTS.md (dependencies re-checked at dispatch) |

## Proposed changes (ordered, validatable)

1. After children 01 through 04 are `executed`, reproduce incident one (deferral then integration, no paid turn, no bypass) on both hosts and paste the evidence.
2. Reproduce incident two (resume integrates the existing lane, no `_attempt2` branch) on both hosts and paste the evidence.
3. Determine whether `p8ni63` has landed; exercise it if so, record its absence plainly if not.
4. Run the bare suite, measure the BEFORE baseline yourself, and show the AFTER-minus-BEFORE failure set is empty.
5. Write the walkthrough with every residual, every sibling boundary, and the still-open rollup defect.

## Deferred / out of scope (with reason)

- The startup dirty-base gate (`p8ni63`): still OPEN backlog, prevention rather than recovery, not a child of this Set. Verified only if it happens to have landed.
- The general rollup fix (option (c) of `cczotj` OQ-04): owed as separate backlog against `77tr3o` R-5. This child is a per-Set workaround, not the durable fix.
- Whether `84j8d7` needs a corrective IPD for its unperformed E-01/V-01: a maintainer decision, recorded in E-02's walkthrough rather than acted on here.
- `h1ksy6` (widens `dirty_tree_overlap`'s input set): must be reconciled with the ladder, not stacked on it; recorded as a residual, not implemented.

## Scope check

- Over-scope: none. This child authors no product code.
- Under-scope: it does NOT re-test each child's own mechanism (each child owns its unit coverage) and it does NOT close any backlog item; children 01 through 04 close `rnl3b7`, `5wdoze`, and `yocdq4` respectively.

## Required tests / validation

Both incident reproductions on BOTH hosts, with pasted terminal output rather than summary. Plus the bare `python3 -m pytest` summary line, judged on the DELTA from a self-measured baseline, with the pre-existing `test_orchestrator_retirement` failure named and excluded.

## Spec / documentation sync

N/A for specs: this child changes no behavior and no contract. The walkthrough E-02 produces IS the documentation deliverable. Write no em or en dashes in that walkthrough, which is user-facing prose.

## Open questions

### OQ-01: Should this child also assert the startup dirty-base gate once `p8ni63` lands?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as authored. E-01 already handles both branches: exercise the gate if `--allow-dirty-base` exists, record its absence plainly if not. No further decision is needed, and the Set's completion criteria deliberately do not depend on it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste BOTH incidents reproduced and survived, for BOTH hosts. Incident one: a lane refused on dirty overlap, DEFERRED, then INTEGRATED after the dirt cleared, with the merge commit on main and NO agent turn spent. Incident two: an item with a verified lane resumed, showing the FIRST lane integrated and `git branch --list 'aw/lane/<id6>*'` containing NO `_attempt2`. For both, paste evidence that NO `--no-verify` was used anywhere. State whether `p8ni63` had landed (name the check you ran) and, if so, paste the startup gate refusing a dirty base and honoring its override; if it had not, say so and treat this item as complete without it, since it is not a child of this Set. If a host could not be demonstrated, SAY SO PLAINLY; an inferred agy result is a FAILED validation.
    Paste the BARE `python3 -m pytest` summary line (the `N passed` line), with the BEFORE baseline measured yourself and the AFTER-minus-BEFORE failure set shown EMPTY.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the walkthrough's path and its residuals section verbatim. Confirm by quotation that it names all four residuals (content-based narrowing as DECLINED, path-category allowlists as REJECTED, `h1ksy6` as needing reconciliation, `a8eufb` as necessary-but-not-sufficient), records `76gsmv` as ANSWERED with the journal-lifetime cause, records `phawyy` as RETRACTED, and records the rollup defect as still open with `84j8d7` named. Paste the CURRENT status line of every sibling artifact you cite, read at execution time rather than copied from this plan, since several moved after authoring. A walkthrough that restates the rename explanation for `76gsmv` is a FAILED validation.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). This child is dispatchable only after children 01 through 04 are `executed` on disk; the runner re-checks `- Item-Dependencies:` at dispatch, so an unmet edge marks this item `dependency-blocked` and continues rather than failing the run.

THIS CHILD IS THE SET'S EVIDENCE, AND THE E/V CHECKPOINT ON IT IS ENFORCED. That is the whole point of its existence: the same two items on the orchestrator would have been discharged by the rollup unperformed. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and BOTH `V-*` items carry concrete pasted evidence.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. If an incident cannot be reproduced, that is a FINDING to report, not a validation to soften.

DO NOT WEAKEN A REFUSAL TO MAKE A REPRODUCTION SUCCEED. Every refusal on this path exists because integrating over a contaminated base can clobber or half-finish real work. If a reproduction only succeeds once a refusal is relaxed, the Set has failed its claim and that is the honest report.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT: run `aw runs` before starting.

Closes no backlog item. `5wdoze` on this plan's `- From-Backlog:` records provenance only; child `51vw4y` closes it.
