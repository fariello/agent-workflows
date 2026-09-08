# IPD: Stop flagging an interrupted item as a status discrepancy when its plan could not legally have moved

- Date: 2026-09-08
- Kind: child
- Concern: `audit_step_artifact` tolerates several run-status/file-status pairs that are legitimately different, and `interrupted` is missing from the list, so an interrupted item is reported as a discrepancy the operator is asked to investigate. The tolerance branch (`run_viewer.py:525-534`, located by SYMBOL) admits `queued`, `running`, `dependency-blocked` and `blocked` beside a file status of `approved`, `to-review`, `draft`, `reviewed`, `queued` or `running`. `interrupted` falls through to the catch-all (`:536-537`, `if f_norm != st: status_mismatch = True`).
  MEASURED AT HEAD `a2e0438a` by calling the real function against a synthetic repo, so the result depends on no live state. With the file at `- Status: approved` in `pending/`, which is the only value an unfinished execute-item's plan can hold: `queued`, `running`, `dependency-blocked`, `blocked` and `reviewed` all give `location_mismatch=False status_mismatch=False`, while `interrupted` gives `location_mismatch=False status_mismatch=True`. The location columns AGREE and the row appears purely on the status comparison, exactly as backlog `13ty0u` reported for run `run-20260905T201722Z-3652350`.
  WHY THAT IS WRONG IS A TAUTOLOGY, NOT A JUDGEMENT. An item whose turn was INTERRUPTED did not finish, so its plan MUST still carry the status it had when the turn began. For an execute-action item that is `approved`. There is no other legal value, so flagging it asks the operator to investigate a state that could not have been otherwise.
  THE ITEM'S SECOND HALF IS UNSOUND AS WRITTEN AND IS NOT IMPLEMENTED HERE. `13ty0u` asks that `substantially-complete` be added in the same pass. Measured, that pair does NOT have the property the item claims: `substantially-complete` is NORMALIZED to `complete` at `run_viewer.py:472` (`st = "complete" if step.status == "substantially-complete" else step.status`), and `complete` then selects `expected_dir_name = "executed"` at `:474-475`. So the audit returns `location_mismatch=True` as well as `status_mismatch=True`, and adding the value to the status tolerance list would leave the location half still flagging while creating a NEW collision: the tolerance branch cannot distinguish a run-side `substantially-complete` from a run-side `complete`, because both arrive as the same normalized token. See F-4 and the deferred section; that half needs a location-side decision this plan deliberately does not make.
- Scope: Add `interrupted` to the EXISTING status-tolerance branch in `audit_step_artifact` so an interrupted item beside an unmoved plan is not a discrepancy, and prove the `Issue` column clears with it. EXCLUDES `substantially-complete`, whose location half is also flagged and whose normalization collides with `complete` (deferred with the measurement); excludes any new classification vocabulary or direction-aware classifier; excludes the `integration-blocked` + `executed` case, which is backlog `1f9m2j`, BLOCKED on `rnl3b7` because deciding it requires evidence this module does not read.
- Scope-Paths: agent_workflows/run_viewer.py, tests/test_run_viewer.py
- Item-Dependencies: none
- Status: to-review
- Set: runviewdisc
- Order: 2
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: vdabn5
- From-Backlog: 13ty0u

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `13ty0u`, PARTIALLY: the `interrupted` half is graduated and the `substantially-complete` half is NOT, with the measurement recorded in the item file. The item carries no `- Blocks-Release:` so none is inherited or invented.
  I VERIFIED THE ITEM BY RUNNING THE FUNCTION RATHER THAN READING IT, which is what surfaced the problem with its second half. Its `interrupted` claim is exactly right and its cited line numbers have drifted (it cites `:451-468` and `:457`; the tolerance branch is at `:525-534` and the catch-all at `:536-537` at HEAD `a2e0438a`). Its careful `1f9m2j` boundary argument also re-verified: `run_viewer` reads only `actual_file.parent.name` and a `- Status:` regex, with zero references to finalize journals, receipts, git history or commits, so this plan asserts nothing about legitimacy and is genuinely not gated on `rnl3b7`.
  THE ITEM'S OWN WARNING WAS THE RIGHT INSTINCT AND UNDERSTATED THE PROBLEM. It says "verify which spelling actually reaches the comparison rather than assuming", pointing at the normalization. Measured, the normalization does more than change the spelling: `substantially-complete` becomes `complete`, and `complete` is one of the two tokens that select `expected_dir_name = "executed"`, so the audit ALSO reports `location_mismatch=True`. Adding the value to a STATUS tolerance list therefore fixes half a row and, worse, cannot express itself: the tolerance branch sees one token for two different run states. The honest fix for that pair is a location-side decision (should a deliberately-unfinalized item expect `pending/`?), which is a different change with a different risk, so it is deferred rather than bundled. This is why this plan implements one value and not two.
  ONE THING FOUND WHILE AUTHORING that shapes E-02: the `Issue` predicate is FIVE textual copies of the same three-term expression in `run_viewer.py`, and pending plan `r2i1b1` (`orchprobe` Order 01, `to-review`) owns extracting them into one function. This plan must NOT extract them (that is that plan's E-03) and must NOT extend one copy in a way that makes the surfaces disagree. Because the fix here is inside `audit_step_artifact`, which all five copies consume, every surface corrects at once with no predicate edit at all; E-02 proves that rather than assuming it.

## Goal

Stop asking an operator to investigate an interrupted item whose plan is exactly where it must be.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: extend the existing tolerance, add nothing new

- [ ] E-01 ADD `interrupted` TO THE EXISTING STATUS-TOLERANCE BRANCH in `audit_step_artifact`, and nothing else. Locate the branch by SYMBOL, not by line number: it is the `elif st in (...)` arm inside `audit_step_artifact` whose body admits `approved`/`to-review`/`draft`/`reviewed`/`queued`/`running` (at HEAD `a2e0438a` it is `run_viewer.py:525-534`, and the item's cited `:457` has drifted).
  PREFER EXTENDING THE EXISTING MECHANISM over introducing a classification vocabulary, and say so in the code. The ad-hoc tolerance list is admittedly not a general solution; a direction-aware classifier would be, and that is what `1f9m2j` wanted before it proved unsound without evidence the module does not read. Adding one value to a list that already encodes exactly this idea is the minimal honest change.
  DO NOT TOUCH THE NORMALIZATION AT `:472`. `st = "complete" if step.status == "substantially-complete" else step.status` is what makes the deferred half hard, and changing it here would silently alter the `executed`/`complete` branch at `:474-475` and `:519-521`, which governs every completed item in every run. That is a separate change with a much larger blast radius.
  DO NOT ADD `substantially-complete`. Its location half is also flagged (measured `location_mismatch=True`) and its normalized token collides with `complete`, so adding it to a STATUS list cannot express the intent. See F-4 and the deferred section.
  - Depends on: none
  - Expected outcome: a run-side `interrupted` beside a file at `approved` in `pending/` yields `status_mismatch=False`; the normalization at `:472` is unchanged; no new status vocabulary is introduced.
  - Execution state: pending

- [ ] E-02 PROVE THE `Issue` COLUMN CLEARS WITHOUT EDITING THE PREDICATE. `run_viewer` holds FIVE textual copies of the same three-term issue expression (`audit.missing_entirely or audit.location_mismatch or audit.status_mismatch`), one of which is in `render_steps_table` at `:1498`. Because all five consume `audit_step_artifact`'s OUTPUT, the E-01 fix should clear every one of them with no predicate change at all.
  VERIFY THAT, DO NOT ASSUME IT. The point of this item is to show the fix reaches the surface the operator actually reads, and a fix proven only on the dataclass is not that. Render the real table and read the column.
  DO NOT EXTRACT OR EDIT THE FIVE COPIES. Pending plan `r2i1b1` (`orchprobe` Order 01) owns extracting them into ONE predicate as its E-03, and extending one copy is precisely how the surfaces come to disagree (that plan's F-2 records the measurement). If E-02 finds a surface that does NOT clear, STOP and report rather than editing a copy to force it.
  - Depends on: E-01
  - Expected outcome: the `Issue` column reads clear for an interrupted item beside an unmoved plan, demonstrated on rendered output; no issue-predicate copy was edited or extracted.
  - Execution state: pending

### Task group 2: pin the fix and guard against over-suppression

- [ ] E-03 ADD THE THREE TEST CASES THE ITEM SPECIFIES, and treat the third as the load-bearing one. (a) run `interrupted` + file `approved` in `pending/` is NOT a discrepancy. (b) the same pair ALSO clears the `Issue` column in `render_steps_table`. (c) THE EXISTING TRUE POSITIVE MUST KEEP BEING FLAGGED.
  CASE (c) IS THE GUARD AGAINST OVER-SUPPRESSION and it already exists in the suite: `tests/test_run_viewer.py` builds a step with `status="complete"` against a plan at `- Status: approved` in `pending/` and asserts `location_mismatch` AND `status_mismatch` are both True, plus `actual_dir == "pending"`, `expected_dir == "executed"`, `file_status == "approved"`. That is a genuine regression (a completed item should have MOVED) and must stay flagged. Extend that test's neighborhood rather than rewriting it, and state which assertions you left byte-identical.
  CASES (a) AND (c) LOOK SUPERFICIALLY IDENTICAL AND MUST DIVERGE, which is the whole reason both are required: both are a `pending/` plan at `approved`, and the only difference is the RUN-side status. If a single change makes both pass or both fail, the fix is wrong in one direction or the other.
  BUILD THE FIXTURE IN A TEMPORARY REPO, NOT FROM THE LIVE TREE. `tests/test_run_viewer.py` reads run directories from `.aw/records/runs/`, which is gitignored; the item measured the module at 14/42 failing in a bare worktree and 42/42 in the real checkout. Measured at HEAD in the real checkout it is `46 passed`, and pending plan `utwr6y` (`testiso` Order 01) exists to make this module own its data. Do NOT add a case that reads the live tree, or this plan makes that plan's job larger.
  - Depends on: E-02
  - Expected outcome: three cases added, (a) and (b) passing on the fix, (c) still flagging with its existing assertions intact; no new test reads `.aw/records/runs/`.
  - Execution state: pending

- [ ] E-04 MUTATION-CHECK BOTH DIRECTIONS. A test that cannot fail is not evidence, and this fix's risk is symmetric: too little suppression leaves the defect, too much hides a real regression.
  REVERT E-01 and show case (a) FAILS, then restore and show it passes. THEN over-suppress deliberately, by also admitting the `complete` run-status into the same tolerance branch, and show case (c) FAILS. Restore. The second mutation is the important one: it demonstrates the guard actually catches the over-reach this plan's deferred half would have caused.
  - Depends on: E-03
  - Expected outcome: two mutations, each failing the case it should, each passing after revert, all four outputs pasted.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE TOLERANCE LIST IS THE ESTABLISHED MECHANISM FOR EXACTLY THIS IDEA. `audit_step_artifact` already has per-run-status arms: `executed`/`complete` require the file to read `executed`/`complete`; `reviewed` accepts `reviewed` or `approved`; the four in-flight statuses accept six file values. Adding a fifth in-flight status is consistent; inventing a classifier is not, and is what `1f9m2j` wanted before it proved unsound.
- THE NORMALIZATION IS LOAD-BEARING AND SHARED. `substantially-complete` -> `complete` happens at `run_viewer.py:472` for the RUN side and again at `:516-518` for the FILE side, and the same mapping appears at four other display sites (`:1464`, `:1649`, `:2174`, and the `status_word` at `:1181`). Any change to it reaches all of them.
- `run_viewer` READS EXACTLY TWO THINGS about an artifact: the parent directory name and a `- Status:` regex. It has ZERO references to finalize journals, receipts, git history or commits. That is precisely why `1f9m2j` is blocked and why this plan is not: this plan asserts nothing about whether a move was legitimate.
- THE ISSUE PREDICATE IS FIVE COPIES, and pending plan `r2i1b1` owns unifying them. Five surfaces consume `audit_step_artifact`'s output, so a fix inside the audit reaches all of them without touching a copy.
- `tests/test_run_viewer.py` IS ENVIRONMENT-SENSITIVE. It reads the gitignored `.aw/records/runs/`; measured `46 passed` in the real checkout at HEAD, and the item measured 14 of 42 failing in a bare worktree. Pending plan `utwr6y` exists to fix that coupling. Do not add to it.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals; a bare run on main is `1 failed, 5648 passed` (the known `tests/test_orchestrator_retirement.py` failure, which reads live plan statuses).

## Findings

| Id | Severity | Location (measured at HEAD `a2e0438a`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | `run_viewer.py:525-534`, `:536-537` | The status-tolerance branch omits `interrupted`, so it falls to the catch-all and is reported as a discrepancy. | called `audit_step_artifact` on a synthetic repo: `interrupted` -> `status_mismatch=True` while `queued`/`running`/`dependency-blocked`/`blocked` -> `False` |
| F-2 | MED | measured | The LOCATION columns agree for the interrupted case (`location_mismatch=False`), so the row appears purely on the status comparison, exactly as the item reported. | same run |
| F-3 | LOW | backlog `13ty0u` | The item's cited line numbers have drifted: it cites `:451-468` and `:457`; the branch is at `:525-534` and the catch-all at `:536-537`. | grep by symbol |
| F-4 | BLOCKER-FOR-THE-SECOND-HALF | `run_viewer.py:472`, `:474-475` | THE ITEM'S `substantially-complete` HALF IS UNSOUND AS WRITTEN. It is normalized to `complete` at `:472`, and `complete` selects `expected_dir_name = "executed"` at `:474-475`, so the audit returns `location_mismatch=True` TOO. Adding it to a STATUS tolerance list fixes half the row, and cannot express itself anyway because the branch receives one token for two distinct run states. | `substantially-complete` -> `location_mismatch=True status_mismatch=True`; `complete` -> identical output |
| F-5 | MED | `run_viewer.py:1498` and four sibling copies | The `Issue` predicate is FIVE textual copies of one three-term expression, all consuming `audit_step_artifact`'s output. So the E-01 fix should clear every surface with no predicate edit; pending plan `r2i1b1` E-03 owns unifying them. | `grep -c "missing_entirely or"` -> 5; read that plan's F-2 |
| F-6 | MED | `tests/test_run_viewer.py` | The existing true-positive fixture (run `complete`, file `approved` in `pending/`) asserts BOTH mismatches plus `actual_dir`/`expected_dir`/`file_status`. It is the over-suppression guard and must keep flagging. | source read |
| F-7 | LOW | `tests/test_run_viewer.py` | The module reads the gitignored `.aw/records/runs/`; `46 passed` in the real checkout at HEAD. Pending plan `utwr6y` owns decoupling it. | ran the module |
| F-8 | CONFIRMED-NOT-BLOCKED | backlog `1f9m2j` | That item is BLOCKED on `rnl3b7` because its case needs proof a move was legitimate, which `run_viewer` cannot read. This plan needs no such proof, so it is correctly independent. | `1f9m2j` reads `Gate-Kind: artifact`, `Gate-Ref: rnl3b7`; `grep` for journal/receipt/commit in `run_viewer.py` returns nothing |

## Proposed changes (ordered, validatable)

1. E-01 adds `interrupted` to the existing tolerance branch, changing no normalization and adding no vocabulary.
2. E-02 proves every `Issue` surface clears without editing any of the five predicate copies.
3. E-03 adds the item's three cases, keeping the existing true-positive assertions intact.
4. E-04 mutation-checks both under-suppression and over-suppression.

## Deferred / out of scope (with reason)

- `substantially-complete`, WHICH THE ITEM ASKED FOR IN THE SAME PASS. Deferred with a measurement, not an opinion (F-4): it normalizes to `complete`, `complete` expects `executed/`, so the audit flags the LOCATION as well and a status-list entry fixes half a row. Worse, the tolerance branch cannot distinguish it from a genuine `complete` because both arrive as one token, so admitting it would ALSO suppress the true positive that case (c) guards. The honest fix is a location-side decision (should a deliberately-unfinalized item expect `pending/`?) plus a way to tell the two normalized states apart, which is a different change with a different risk profile. Recorded in the backlog item so the surviving work is visible.
- ANY DIRECTION-AWARE CLASSIFIER or new status vocabulary. That is what `1f9m2j` wanted and it proved unsound without evidence `run_viewer` does not read.
- THE `integration-blocked` + `executed` CASE. Backlog `1f9m2j`, BLOCKED on `rnl3b7`. Classifying it benign requires asserting the move was LEGITIMATE, and `run_viewer` reads only a directory name and a status regex, so any verdict there is a fabrication.
- EXTRACTING OR EDITING THE FIVE `Issue` PREDICATE COPIES. Pending plan `r2i1b1` E-03 owns that. Extending one copy is how the surfaces come to disagree.
- CHANGING THE `substantially-complete` -> `complete` NORMALIZATION. It is shared by six sites and governs every completed item in every run.
- DECOUPLING `tests/test_run_viewer.py` FROM THE GITIGNORED RUNS TREE. Pending plan `utwr6y` (`testiso` Order 01) owns it.

## Scope check

- Over-scope: none. `run_viewer.py` is in scope ONLY for the one tolerance-branch value. Do NOT touch the normalization, the location computation, or any issue-predicate copy.
- Under-scope: stated rather than left as `none`. After this plan a `substantially-complete` item is STILL flagged, on both the location and the status axis. That is the deferred half above, recorded in the item.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS not totals. Note the honest complication: `tests/test_run_viewer.py` reads the gitignored `.aw/records/runs/`, so it behaves differently in a lane than in the real checkout (the item measured 14 of 42 failing bare; HEAD measures `46 passed` in the real checkout). Run the module in BOTH and report both, and build every new case in a temporary repo so the new cases themselves are environment-independent.

## Spec / documentation sync

N/A, with the reason stated rather than asserted. This plan changes which run-status/file-status pairs `aw runs` calls a discrepancy. Spec `25kzda` §5.6 governs the run's reporting surface and enumerates per-item outcomes, but the artifact-discrepancy audit is a `run_viewer` concern with no spec text fixing its tolerance list, and this change makes the view MORE accurate rather than altering a documented contract.
ONE THING TO CHECK RATHER THAN ASSUME: if any spec, README, or help string DOCUMENTS which pairs are reported as discrepancies, adding a tolerated pair changes that documented behavior and the file must be declared in `- Scope-Paths:` before execution, since the runners announce declared spec edits before a run starts and the finalize scope gate reconciles declared against actual. Grep for the discrepancy table's own wording before finalizing. Do NOT edit spec `25kzda`'s §4.2 finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

## Open questions

### OQ-01: Does an interrupted REVIEW-action item have a different legal file status than an interrupted execute-action item?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because the tolerance branch this plan extends already admits SIX file values (`approved`, `to-review`, `draft`, `reviewed`, `queued`, `running`) for the four in-flight statuses, so it is already action-agnostic and adding `interrupted` inherits that breadth. The question is whether that breadth is too generous for the new value: an interrupted EXECUTE item can only be `approved` (the item's tautology), while an interrupted REVIEW item would legitimately be `to-review` or `draft`. Since the existing arm covers both, the practical answer is that no narrowing is needed. Recorded because an executor might reasonably try to narrow the new value to `approved` alone, which would then FLAG an interrupted review turn, reintroducing the defect in a different shape. If you narrow, test the review case.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the changed branch as written, located by symbol, and state its line number at YOUR head (it will not be `:525-534`). Paste the PRE-FIX and POST-FIX output of `audit_step_artifact` for run `interrupted` + file `approved` in `pending/`, showing `status_mismatch` going True -> False and `location_mismatch` staying False. Paste a diff of `run_viewer.py` proving the normalization line and the location computation are BYTE-UNCHANGED.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the rendered `render_steps_table` output for an interrupted item beside an unmoved plan, with the `Issue` column visible and reading clear. Paste the same for the artifact-discrepancy summary. Paste a diff or grep proving NO issue-predicate copy was edited (the five-copy count is unchanged and each is byte-identical). If any surface did NOT clear, report it rather than editing a copy.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste all three tests and their actual runner output. For case (c), paste the assertions you left BYTE-IDENTICAL and confirm it still flags both `location_mismatch` and `status_mismatch`. Paste cases (a) and (c) side by side, showing they differ ONLY in the run-side status and yet reach opposite verdicts. Paste proof no new case reads `.aw/records/runs/`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste BOTH mutations in full. Mutation 1: revert E-01, paste case (a) FAILING, restore, paste it passing. Mutation 2: additionally admit `complete` into the tolerance branch, paste case (c) FAILING, restore, paste it passing. Mutation 2 is the load-bearing one; a V-04 pasting only mutation 1 has not shown the over-suppression guard works.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the two paths in `- Scope-Paths:`. Do NOT add `substantially-complete` to the tolerance list (F-4). Do NOT change the `substantially-complete` -> `complete` normalization. Do NOT change the location computation or `expected_dir_name`. Do NOT edit or extract any of the five `Issue` predicate copies. Do NOT touch the `integration-blocked` + `executed` case. Do NOT add a test that reads `.aw/records/runs/`. Do NOT introduce a new status vocabulary or classifier. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. The backlog item's own citations had already drifted by roughly 70 lines. Find `audit_step_artifact`, `StepArtifactAudit`, `render_steps_table`, `format_artifact_audit_summary`, and `find_artifact_file` by name.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved vdabn5 --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION, close backlog `13ty0u`, which this plan carries as `- From-Backlog:`. That item carries no release gate, so none is inherited. Its `substantially-complete` half is NOT delivered here and is recorded in the item as surviving work with the measurement that made it unsound as written, so closing it does not silently drop that half; if the maintainer would rather keep the item open for that half, set it `graduated` instead of `done` and say so.
