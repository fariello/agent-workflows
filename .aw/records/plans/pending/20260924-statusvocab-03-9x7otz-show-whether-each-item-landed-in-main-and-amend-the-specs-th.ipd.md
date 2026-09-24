# IPD: Show whether each item landed in main and amend the specs that name a legacy status

- Date: 2026-09-24
- Kind: child
- Concern: THE RUN SUMMARY HAS NO COLUMN FOR THE ONLY FACT AN OPERATOR NEEDS, AND EIGHT SPECS STILL NAME THE VOCABULARY ORDER 01 REPLACES. The table renders `Status`, `Item`, `Action`, `Verified` and `Issue`, and NONE of them answers "did this reach `main`". Today the answer is obtainable only by listing `.aw/records/plans/executed/` by hand, which is what a human had to do to triage run `run-20260924T050407Z-3108751`. The directory is also the one signal no agent can assert, which is why `runner_shared.edge_satisfied` was deliberately re-pointed at it by maintainer ruling on 2026-09-19 after an in-run status shortcut dispatched a plan into a tree with none of its prerequisite's work, costing "2h 10m and $55.02 for nothing integrated". SEPARATELY, eight specs name at least one legacy status token, and a spec is the contract every other plan is reviewed against: leaving one stale after Order 01 lands would re-authorize the removed vocabulary for every future plan reviewed against it. THE STATUS-VERSUS-LANDED RELATIONSHIP IS DIRECTIONAL, NOT EQUAL, and this is the trap that must be designed for rather than discovered: re-measured across all 28 items of that run, `executed` had zero false positives but THREE FALSE NEGATIVES (`yeh7gc` recorded `dependency-blocked`, `m7gvuz` `failed-safely`, `xdvglg` `substantially-complete` are ALL in `executed/` and ALL in `main`). A naive column that simply restated the status would read `no` for three items that landed.
- Scope: Add a `Landed` column to the run summary derived from the plan's terminal DIRECTORY, and amend the eight specs that name a legacy status token so the contract matches the vocabulary Order 01 ships. IN: the run summary table and its renderer, the directory-derived predicate that feeds the column, and the eight spec files in their real status subdirectories. OUT: deriving the column from any recorded status or self-report (the whole point is that it is independent of both), changing the status vocabulary itself (Order 01 owns it), and changing what any gate refuses.
- Scope-Paths: agent_workflows/run_viewer.py, agent_workflows/runner_shared.py, tests/test_run_summary_table.py, tests/test_run_viewer.py, .aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md, .aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md, .aw/records/specs/approved/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md, .aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md, .aw/records/specs/approved/20260912-6kwd2e-01-6kwd2e-midrun-question-surfacing.spec.md, .aw/records/specs/to-review/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md, .aw/records/specs/draft/20260920-i4gpto-01-i4gpto-standalone-executed-plan-audit.spec.md, .aw/records/specs/implementing/20260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md
- Item-Dependencies: executed:cyamvi
- Status: draft
- Set: statusvocab
- Order: 3
- Highest E allocated: 03
- Priority: high
- Work-Kind: bug
- Blocks-Release: next
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 9x7otz

## Workflow history

- 2026-09-24 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Let an operator read one column and know whether the work is in `main`, and leave no spec describing a vocabulary the runner no longer writes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the operator-facing fact

- [ ] E-01 DERIVE `Landed` FROM THE PLAN'S TERMINAL DIRECTORY AND FROM NOTHING ELSE. Add the predicate beside the vocabulary Order 01 defines, reading the plan's disposition directory (the `executed/` bucket) exactly as `edge_satisfied`'s `executed:` branch already does via `plan_bucket`. DO NOT derive it from the recorded status, from the attempt's disposition, or from any field an agent writes: independence from self-report is the property, not an implementation detail, and F-01 measures three items where status and landedness disagree.
  - Depends on: none
  - Expected outcome: one shared predicate answering landed-or-not from the directory; both hosts reach the same object.
  - Execution state: pending

- [ ] E-02 RENDER THE COLUMN IN THE RUN SUMMARY TABLE, beside `Status` rather than replacing it, because the two are independent facts and the DISAGREEMENT between them is diagnostic. Keep the existing columns unchanged. A replayed historical run must render without error, which means the column must tolerate a plan that has since moved, been superseded, or been deleted, and must say so rather than guessing.
  - Depends on: E-01
  - Expected outcome: `aw runs` shows `Landed` per item; a historical run renders; a missing plan reads as unknown rather than as `no`.
  - Execution state: pending

### Task group 2: the contract

- [ ] E-03 AMEND THE EIGHT SPECS THAT NAME A LEGACY STATUS TOKEN, stating in each that legacy tokens remain READABLE FOREVER and are no longer WRITTEN. The read-versus-write sentence is required, not decorative: without it a later reader concludes the old spelling is invalid input and "fixes" the back-compatibility path Order 01 built for gitignored historical run directories. THE EIGHT ARE DECLARED AT THEIR REAL PATHS ACROSS FOUR STATUS SUBDIRECTORIES (`approved/` x5, `to-review/`, `draft/`, `implementing/`); two are NOT `approved` (`z7nbn1` is `to-review`, `i4gpto` is `draft`) and amending a non-approved spec is legitimate but must be stated so a reviewer is not surprised.
  - Depends on: none
  - Expected outcome: no spec names a legacy token as a value a runner writes; each amended spec carries the read-versus-write distinction; `aw specs check` conforming.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE SPECS TREE USES STATUS SUBDIRECTORIES, and a plan declaring the old flat path will refuse to finalize. Measured at authoring: `.aw/records/specs/` contains `approved/`, `deferred/`, `draft/`, `implemented/`, `implementing/`. An earlier draft of this Set declared all seven spec paths flat and would have edited eight undeclared files.
- THE DIRECTORY IS THE AUTHORITY FOR "DID THIS LAND", by maintainer ruling 2026-09-19 recorded at `edge_satisfied`: the in-run status shortcut was REMOVED in favour of "ONE authority: the plan's directory on disk", because `executed/` "is exactly where `aw ipd finalize` puts a plan and a directory move is harder to forge than a status field". E-01 reuses that authority rather than inventing a second one.
- A PLAN MAY AMEND A SPEC AND MUST DECLARE IT: both runners announce declared spec edits before a run starts and the finalize scope gate reconciles declared against actual. All eight are declared.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- F-01 STATUS AND LANDEDNESS DISAGREE ON REAL DATA, AND THE DISAGREEMENT IS THE POINT. Re-measured over all 28 items of `run-20260924T050407Z-3108751`: zero items recorded `executed` are absent from `executed/`, but THREE items NOT recorded `executed` are present in it (`yeh7gc` `dependency-blocked`, `m7gvuz` `failed-safely`, `xdvglg` `substantially-complete`). All three were landed afterwards by hand. So `Landed` must be measured against the DIRECTORY and must NOT be required to agree with the status column; a validation demanding agreement would accept a column that reads `no` for three landed items.
- F-02 THE ASYMMETRY STRENGTHENS THE CASE FOR THE COLUMN RATHER THAN WEAKENING IT. A false negative means work IS in `main` while the run says otherwise, which is precisely the state an operator cannot currently see and which caused three plans in that run to be triaged in the wrong order.
- F-03 EIGHT SPECS, FOUR SUBDIRECTORIES, TWO NOT APPROVED. Measured at authoring: `0718`, `77tr3o`, `7ckptx`, `uonrjg`, `6kwd2e` in `approved/`; `z7nbn1` in `to-review/`; `i4gpto` in `draft/`; `c4gd2h` in `implementing/`. `c4gd2h` is included because Order 01 cites its R21 for the `interrupted` promotion, so its vocabulary must match too.

## Proposed changes (ordered, validatable)

1. E-01 add the directory-derived landed predicate.
2. E-02 render the `Landed` column beside `Status`.
3. E-03 amend the eight specs with the read-versus-write sentence.

## Deferred / out of scope (with reason)

- Deriving `Landed` from a recorded status or an agent's outcome file: independence from self-report is the property this plan exists to add.
- Changing the status vocabulary: Order 01 (`cyamvi`) owns it, and this plan depends on it being executed first.
- Adding a landed column to `aw attention` or any other surface: this plan changes the RUN SUMMARY, and a second surface is a separate decision with its own consumers.

## Scope check

One derived column from an authority that already exists, plus eight spec amendments that make the contract match the shipped vocabulary. No gate changes, no vocabulary changes, no new authority invented.

## Required tests / validation

Run the suite BARE (`python3 -m pytest`); `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Re-derive the baseline at execution rather than trusting a number authored days earlier; at authoring it was `8850 passed, 5 skipped, 2 xfailed` on `main` `a631a1f6`. Gate on NO NEW failures. Paste ACTUAL output for every `V-*`.

## Spec / documentation sync

EIGHT SPECS ARE AMENDED AND ALL EIGHT ARE DECLARED, at their real paths across four status subdirectories. WHY THIS PLAN AND NOT ORDER 01: a spec amended before the code emits the new vocabulary would leave the contract ahead of the implementation, and this plan's `- Item-Dependencies: executed:cyamvi` enforces that ordering. Each amendment states that legacy tokens stay READABLE and are no longer WRITTEN, because Order 01's back-compatibility path depends on historical run directories remaining parseable and `.aw/records/runs/` is gitignored and unmigratable.

## Open questions

- [ ] OQ-01 Should `Landed` distinguish "in `main`" from "in a terminal directory that is not `executed/`" (superseded, not-executed)? Blocking: no. RECOMMENDATION: yes, three values (`yes`, `no`, `n/a`), because a superseded plan never intended to land and reading `no` for it would mimic a failure. `nmlx47` is the live example: it is terminal, correctly never landed, and is not a problem.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the predicate's answer for the three F-01 counter-examples (`yeh7gc`, `m7gvuz`, `xdvglg`) showing `Landed` = yes DESPITE a non-`executed` recorded status, and for one genuinely stranded item showing no. Paste proof the predicate reads no status field and no outcome file, by inspection of its inputs.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `aw runs` for `run-20260924T050407Z-3108751` showing the `Landed` column. THE BAR IS DIRECTIONAL: `Landed` must agree with the DIRECTORY for every item, and must NOT be required to agree with the STATUS column; paste the three rows where they legitimately disagree as expected output rather than as failures. Paste a replayed run whose plan has since moved, showing unknown rather than a guess.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the amended section from each of the eight specs, and `aw specs check` conforming. Paste the read-versus-write sentence verbatim from at least three, including one of the two non-`approved` specs, and state that amending a `to-review`/`draft` spec was deliberate.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

Human approval required before execution.
