# IPD: Reconcile 65cuw0's V-03 gitignored-refusal wording with the amended R5.5 by appended note, and restore the retention guard the suite trim deleted

- Date: 2026-09-29
- Kind: child
- Concern: Executed plan `65cuw0` carries an E-04 and a V-03 that both REQUIRE an interrupted merged lane whose only unexplained content is a GITIGNORED file to be PRESERVED, with reason code `unknown-ignored-file` pasted as evidence. Spec `7ckptx` R5.5 was AMENDED 2026-09-18 (commit `e94a7c4e`, "spec(7ckptx): amend R5.5 to remove teardown refusal on gitignored files") to make gitignored content DISPOSABLE upon lane destruction, and `lane_containment.RETENTION_UNKNOWN_IGNORED` now documents itself as "NEVER EMITTED BY `reason_codes` NOW, deliberately". So the requirement cannot be satisfied without forking R5.5, the executor complied with the amended spec instead, and recorded that as decision `08-65cuw0-D3` with human review requested. RE-MEASURED AT AUTHORING against the real gate rather than inherited from the backlog item (F-01, F-02): a merged lane holding only a gitignored file is TORN DOWN with `reason_codes=()`, while the untracked twin is PRESERVED with `('unknown-untracked-file',)`. WHILE VERIFYING THAT, THIS PLAN FOUND A SECOND DEFECT THE ITEM COULD NOT HAVE SEEN, and it is the more valuable half: the two test files that were the ONLY guards on this behavior (`tests/test_lane_retention.py`, 1064 lines, and `tests/test_worktree_lease_merged_reclaim.py`, 797 lines) were BOTH DELETED by commit `19313eed` on 2026-09-24, so the ignored-versus-untracked distinction is now green under mutation in BOTH directions (F-05, F-06). The wording defect is cosmetic; the missing guard is not.
- Scope: IN: (a) APPEND one dated `## Workflow history` note to executed plan `65cuw0` recording that its E-04/V-03 gitignored-refusal wording predates the 2026-09-18 R5.5 amendment and that the shipped behavior follows the amended spec, since an append is the only edit `AGENTS.md` sanctions on a plan under `.aw/records/plans/executed/`; (b) APPEND a `## Round 4` to `65cuw0`'s typed review record, because Round 2's D-4 is what MOVED the ignored-file case into V-03 and is therefore where the stale requirement was authored, and the reviews tree's own documented correction vehicle is an appended round; (c) RESTORE the deleted behavioral guard as a new `tests/test_lane_retention_amended_r55.py` that pins the amended R5.5 classification by OUTCOME, measured to FAIL under mutation in both directions. OUT: any in-place rewrite of `65cuw0`'s E-04, V-03, its Required or Observed evidence, its `- Status:`, or its position in `executed/` (forbidden, and the whole reason (a) and (b) are appends); any rewrite of Rounds 1 through 3 of its review; any EDIT to spec `7ckptx` R5.5 or A15 (the shipped behavior already complies, so there is nothing to amend, and narrowing R5.5 is the alternative this plan explicitly refuses); any change to `lane_containment.py`, `worktree_lease.py`, or either driver (no production behavior is wrong); the `uncollected-submission`-refuses-every-interrupted-lane defect, which is a DIFFERENT R2.5 question already owned by backlog `nvymif` (F-08); and the general audit of what else `19313eed` left unguarded, already owned by backlog `xvp5vx` (F-09).
- Scope-Paths: .aw/records/plans/executed/20260917-laneorph-01-65cuw0-fix-lane-reclaim-so-a-merged-lane-is-reclaimable-and-torn-do.ipd.md, .aw/records/reviews/20260917-laneorph-01-65cuw0-fix-lane-reclaim-so-a-merged-lane-is-reclaimable-and-torn-do.review.md, tests/test_lane_retention_amended_r55.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: 0kdwm3
- Set: 0kdwm3
- Order: 1
- Highest E allocated: 04
- Author: opencode model=its_direct/pt3-claude-opus-5-1m-us
- Id: hyuos6

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: hyuos6 verified (set 0kdwm3, attempt 1).
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-30 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-501..PR-504 all FIXED, none deferred or open, no BLOCKER and no unfixed HIGH. I REPRODUCED BOTH BLOCKERS RATHER THAN TRUSTING THEM, because they justify the plan's substantive half, and both hold at review HEAD 84cdeb94: re-unioning unknown_ignored into LaneInventory.unknown (a full revert of the 5w8g8j fix) leaves the bare suite at 3353 passed 2 skipped, and dropping unknown_untracked (the data-loss direction) does too, each reverted to an empty diff. F-07's cause, F-01's unsatisfiable requirement, F-11's chronology to the minute including both ancestry tests, F-12's two pre-commit gates exiting 0 on a staged probe append, and F-13's five history consumers with only extract_newest_history_entry changing, all reproduce exactly. TWO HIGH DEFECTS, neither visible from the plan's prose alone. PR-501: backlog nvymif GRADUATED after authoring to pending plan z8ex9f, which declares lane_containment.py and whose E-03 adds a landing condition treating an ABSENT branch as BLOCKING; this plan's fixture threads no branch, so once z8ex9f lands the clean and ignored cases INVERT and the two refusal cases pass for the wrong reason, with neither plan naming the other. E-03 is now adaptive rather than carrying an Item-Dependencies edge the grammar cannot express as a preference. PR-502: the mutation evidence V-03 demanded was satisfiable by a module detecting NEITHER mutation, because reason_codes is INVARIANT across both mutations in exactly the cases each is meant to break (measured: the ignored case flips torn_down True to False with reason_codes () both times, the untracked case flips False to True with ('unknown-untracked-file',) both times), so only torn_down and worktree existence move; that is the vacuous guard the plan's own gate names as most likely to go wrong. PR-503 records the receipt fixture's required item shape, since an order-keyed item raises KeyError position rather than failing a test. PR-504 adds the review baseline beside the authored one. I ALSO CONFIRMED the specfin7ck overlap is genuinely benign (uuh71v touches only the spec and walkthroughs), that all three structure-pinning tests really were in the deleted files so the no-restore exclusion is grounded, that dwfmxz is a live open carrier, and F-10's absent note verb. I AGREE with the plan's declining a Blocks-Release gate for F-06 and record the agreement rather than passing over it, since the behavior is correct and only its guard is missing. Bare suite 3353 passed, 2 skipped, 3 warnings in 108.82s; tree clean after every probe.

- 2026-09-29 to-review (opencode model=its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `0kdwm3`. EVERY measurement below was taken AT AUTHORING in this lane at HEAD `9733d47a`, by RUNNING the real predicates rather than by carrying over the item's 2026-09-22 figures. THE ITEM'S CENTRAL CLAIM REPRODUCED EXACTLY: the gitignored case is torn down with no reason code while the untracked twin is preserved with `unknown-untracked-file`, so `65cuw0`'s V-03 wording is unsatisfiable without forking R5.5 (F-01, F-02). THE ITEM OFFERS THE MAINTAINER A CHOICE AND THIS PLAN TAKES ONE SIDE OF IT WITH A REASON. The item says to "either annotate the executed plan's V-03 to cite the amendment, or - if the maintainer prefers the pre-amendment rule on the interrupt path specifically - open a plan to amend R5.5 deliberately". This plan takes the ANNOTATE route and refuses the amend route, resolved from repository evidence rather than escalated (OQ-01): the amendment records that the blanket ignored-file refusal "caused 100 percent of clean test runs to fail teardown, stranding dozens of worktrees on disk", and R6.1 forbids a rule that is stricter on one path than another, so restoring it on the interrupt path alone would re-create a measured production failure in a forked form. THE ITEM ALSO UNDERSTATES THE WORK, and the discovery is why this plan is not purely documentary. While establishing what still guards the amended behavior I found that BOTH guarding test files were deleted by the 2026-09-24 suite trim, and I measured the consequence directly: re-unioning `unknown_ignored` into `unknown` (a full revert of the `5w8g8j` fix) leaves the bare suite GREEN at 3246 passed, and so does DROPPING `unknown_untracked` from it, which is the `wfamig` data-loss direction (F-05, F-06). The backlog item's closing sentence says "NOT A BUG: nothing behaves incorrectly", and that remains TRUE of the behavior; what is newly false is its implicit premise that the hazard is "fully covered and pinned by two tests", because those tests no longer exist. E-03 restores an outcome-level guard rather than the deleted files, per the maintainer's 2026-09-26 no-code-pinning ruling.
- 2026-09-29 draft (opencode model=its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `65cuw0` and its review safe to read, by appending to each (never rewriting either) that the E-04/V-03 demand for an `unknown-ignored-file` refusal was superseded by the 2026-09-18 amendment to spec `7ckptx` R5.5 eleven hours before the plan was approved, so the next reader comparing the plan's letter to what shipped does not conclude the plan was under-delivered, and does not "fix" it by re-forking R5.5. Then close the real gap the same investigation exposed: give the amended classification a behavioral guard again, since the two files that held it were deleted and the distinction is currently green under mutation in both directions.

TWO DEFECTS, DELIBERATELY SEPARATED, because conflating them is the likeliest way this work goes wrong. The FIRST is a stale REQUIREMENT in a durable record, and it is fully discharged by the two appends. The SECOND is that the amended behavior has NO TEST GUARD, and it is fixed here by E-03 rather than routed away, because it is small, in scope for a plan already reading these exact predicates, and dangerous to defer: an unguarded retention rule is one careless edit away from the silent data loss this whole Set exists to prevent.

WHAT THIS PLAN DELIBERATELY DOES NOT DO, stated because it is the tempting reading of the backlog item. It does not amend spec `7ckptx`. It does not restore the pre-amendment refusal on the interrupt path. It does not touch `65cuw0`'s E-04 or V-03 text. The shipped behavior is correct against the approved spec; only the record and the test coverage are wrong.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: correct the record on the two artifacts that carry the stale requirement

- [x] E-01 APPEND one dated `## Workflow history` record to `65cuw0` stating the supersession. This is the ONLY edit this plan makes to that file and it MUST be an append: `AGENTS.md` forbids changing what a plan in `.aw/records/plans/executed/` RECORDS (its steps, evidence, results, or status) and expressly permits "a dated `## Workflow history` line to it that points at later work". So do NOT touch E-04's text, V-03's `Required evidence` or `Observed evidence`, the `## Approval and execution gate` paragraph, or any `- Field:` in the metadata block. WRITE IT BY HAND: there is no tooled note verb for a plan (`aw backlog note` and `aw specs note` exist; `aw ipd` exposes no `note`, F-10). PLACEMENT: insert it as the FIRST record under `## Workflow history`, because that section is newest-first (its `2026-09-22 executed` record is the first line of the section) and `plan_readiness.extract_newest_history_entry` reads the FIRST record; appending at the bottom files it as the oldest event. Use a NOTE token, not a status token, because this transitions nothing.
  THE MESSAGE MUST SAY FIVE THINGS, because a reader who has only this line must be able to act. (1) That E-04's final sentence and V-03's `Required evidence` both demand an interrupted merged lane holding only a gitignored file be PRESERVED with reason code `unknown-ignored-file`, and that this demand is UNSATISFIABLE against the spec the plan was approved under. (2) WHY: spec `7ckptx` R5.5 was amended 2026-09-18 to make gitignored content disposable upon lane destruction, and `lane_containment.RETENTION_UNKNOWN_IGNORED` is documented as never emitted by `reason_codes` now, so honoring the wording would have forked R5.5 in the direction R6.1 forbids. (3) THE CHRONOLOGY, which is the part no existing artifact states and which explains how it shipped: the wording was authored by REVIEW ROUND 2 (commit `59d1d833`, 2026-09-17 21:49) and the amendment landed 2h45m later (commit `e94a7c4e`, 2026-09-18 00:34), ELEVEN MINUTES before round 3 approved the plan (commit `9ecb9f3f`, 2026-09-18 00:45) without sweeping V-03 for it - so this is a REVISION-SWEEP miss, the exact failure the `plan-review` revise step was later amended to prevent, and not an executor deviation. (4) That the executor's handling is recorded as decision `08-65cuw0-D3` and that V-03's `Observed evidence` block is the authoritative account of it. (5) That the HAZARD the requirement existed for is NOT the ignored case: name the untracked case as the one that genuinely refuses, so a reader does not conclude retention was weakened. Cite this plan by id6 `hyuos6`, not by path, so the pointer survives a rename. Do NOT assert in this record that the test guard is missing beyond one clause pointing at E-03's new file, because the detailed account belongs in the test module's own docstring and duplicating it invites the two copies to diverge.
  - Depends on: none
  - Expected outcome: `65cuw0` carries exactly one new FIRST history record naming `hyuos6` and stating all five things; `git diff --numstat` on that file shows insertions only and ZERO deletions; E-04's text, V-03's two evidence blocks, the gate paragraph, `- Status: executed` and the file's location in `executed/` are all byte-identical to HEAD.
  - Execution state: performed

- [x] E-02 APPEND a `## Round 4` section to `65cuw0`'s typed review record, and leave Rounds 1 through 3 untouched. THE MECHANISM IS THE TREE'S OWN, not an invention: `.aw/records/reviews/README.md` states this tree's files hold "MULTIPLE rounds as repeated `## Round <N>` sections, appended in order", that "The LAST round in the file is the CURRENT one", and that "Only the current round's findings are live", precisely so a finding raised in one round and resolved later does not block forever. THE REVIEW RECORD IS THE RIGHT PLACE, and this is not merely symmetry with E-01: Round 2's DECISION D-4 is what MOVED the ignored-file case into the behavior layer ("Should E-04 keep the merged+IGNORED-file case at the `LaneState` layer? NO. Moved to the behavior layer (E-03/V-03)"), so the review record is where the stale requirement was AUTHORED, and a correction recorded only on the plan would leave the decision that produced it reading as sound.
  MATCH THE DOCUMENTED SECTION SHAPE: a `### Findings` table with exactly the columns the existing rounds use (`ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution`) and a `### Decisions` table with `ID | Question | Chosen | Alternatives considered | Basis | Reversible`. NUMBER THE NEW IDS IN A FRESH BAND so they cannot be mistaken for an earlier round's: Round 2 used `PR-101`..`PR-107` and `D-1`..`D-5`, so use `PR-201+` and `D-6+`. Round 4 must record: a finding that D-4's relocation of the ignored-file case was correct in its LAYER reasoning and was superseded in its SUBSTANCE 2h45m later, with the three commit shas and the eleven-minute gap; a finding carrying the DELETED TEST GUARD with its mutation measurements, marked FIXED by this plan's E-03 rather than routed away; and a decision row recording the choice to append rather than rewrite, with the alternative considered (amending R5.5, which is the other branch the backlog item offers) and why it was rejected. Do NOT edit the front-matter `- Verdict:` field: the plan WAS approved with revisions applied, and that record stands. STATE THE DISCLOSURE this round inherits, since it is the same model family as the plan and as Rounds 1 through 3, so a reader weighs it as a near-self-review.
  - Depends on: E-01
  - Expected outcome: the review file carries a `## Round 4` after Round 3 with both tables present and correctly columned, new ids in the `PR-201+`/`D-6+` band; `git diff --numstat` shows insertions only and ZERO deletions; every row of Rounds 1 through 3 and the front-matter `- Subject-Id:`/`- Subject-Type:`/`- Verdict:` are byte-identical to HEAD; `aw check reviews` reports no new finding attributable to the change.
  - Execution state: performed

### Task group 2: restore the guard the amended behavior lost

- [x] E-03 ADD `tests/test_lane_retention_amended_r55.py` PINNING THE AMENDED R5.5 CLASSIFICATION BY OUTCOME, and prove it load-bearing by mutation in BOTH directions. This is the substantive half of this plan. The property has no guard at all today: `19313eed` deleted both files that held it, and nothing in the surviving suite imports `inventory_lane` or `teardown_lane_if_classified` (F-05, F-06, F-07).
  TEST BY OUTCOME, NEVER BY CODE STRUCTURE, per the maintainer's 2026-09-26 ruling and GUIDING_PRINCIPLES P16. Build REAL git lanes in a temp repo, merge them, and drive the REAL `lane_containment.teardown_lane_if_classified` with a REAL run directory and a REAL COMPLETE collection receipt, then assert on `torn_down`, `reason_codes`, and whether the worktree directory still exists on disk. Do NOT restore either deleted file wholesale: both carried structure-pinning tests (`test_the_status_args_carry_all_three_flags`, `test_each_retention_symbol_has_exactly_one_definition_in_the_shared_home`, the whole `TheNoDirectForceTeardownTests` AST class), and the ruling forbids re-introducing those.
  FOUR CASES, WHICH ARE THE FOUR THE SHIPPED RULE DISTINGUISHES and which the authoring probe already measured green (F-03): a merged lane whose only unexplained content is GITIGNORED is TORN DOWN with `reason_codes == ()` and its worktree gone; a merged lane with an unexplained UNTRACKED file is PRESERVED with `('unknown-untracked-file',)` and its file still on disk; a merged lane with a DIRTY TRACKED file is PRESERVED with `('dirty-tracked-file',)`; and a fully accounted CLEAN lane is TORN DOWN. ALSO assert that the ignored paths are still ENUMERATED in the inventory's diagnostics even though they no longer refuse, because "disposable" must not mean "invisible" and that is the half a careless simplification would drop.
  SUPPLY A COMPLETE RECEIPT IN EVERY CASE, and say in the module docstring why: with `run_dir`/`item` absent, `submission_retention` reports `uncollected=True` unconditionally, so every lane is unclassified for an unrelated reason and all four cases would pass vacuously on the same code path. Measured at authoring: with no receipt the gitignored lane reports `classified=False reason_codes=('uncollected-submission',)`; with one it reports `classified=True reason_codes=()` (F-04). That is a live trap, not a hypothetical: it is the same masking that backlog `nvymif` is about. NOTE THE RECEIPT'S ITEM SHAPE, measured at review because the wrong shape raises rather than failing: `collection_receipt_path` calls `item_slug`, which reads `int(item['position'])`, so a fixture item must carry `position` (an `order` key raises `KeyError: 'position'`).
  RE-MEASURE BEFORE WRITING, BECAUSE A PENDING PLAN WILL CHANGE THESE FOUR ANSWERS (F-14, added at review). `nvymif` graduated 2026-09-30 to pending plan `z8ex9f`, whose `- Scope-Paths:` includes `agent_workflows/lane_containment.py`, whose E-02 narrows `submission_retention` so a provably-empty lane is no longer `uncollected`, and whose E-03 adds a NEW blocking condition to `LaneInventory` for work that has not landed on the integration target - treating an ABSENT branch as BLOCKING. This module's handle exposes only `.path`, so under `z8ex9f` every case here would classify `False` on that new condition and two of the four asserted outcomes would INVERT. FIRST, at execution, check whether `z8ex9f` has landed (is `LaneInventory` carrying a landing/unmerged reason code, and does `inventory_lane` accept a branch parameter?). IF IT HAS NOT, write the four cases as specified here. IF IT HAS, the lanes in this module must be MERGED (they already are, which is what makes this survivable) and the fixture must thread the lane's branch so the landing condition is satisfied rather than defaulted-to-blocking; assert the same four OUTCOMES either way, and paste which branch you took. DO NOT change `lane_containment.py` to make this module pass: that is out of scope and is the inversion the gate warns about.
  - Depends on: none
  - Expected outcome: a new test module whose four cases pass against unmodified code, and which FAILS in both mutation directions: re-unioning `unknown_ignored` into `LaneInventory.unknown` (the ignored case flips to preserved) and removing `unknown_untracked` from it (the untracked case flips to torn down). ASSERT ON `torn_down` AND WORKTREE EXISTENCE, NOT ON `reason_codes` ALONE, for a reason measured at review: under BOTH mutations `reason_codes` is UNCHANGED in the mutated case (the ignored case stays `()` when it flips to preserved, and the untracked case still reports `('unknown-untracked-file',)` when it flips to torn down), so a module asserting only reason codes would go GREEN under both mutations and satisfy nothing. The state that actually moves is `torn_down`/`classified` and whether the worktree is gone. A pasted mutation failure whose assertion is on a reason code is not acceptable evidence. No test in the module reads production source text, AST, or line counts.
  - Execution state: performed

- [x] E-04 STATE THE HONEST LIMIT OF THE NEW GUARD IN ITS OWN DOCSTRING, so the next reader does not over-trust it. Record three things in the module docstring: (1) that it guards the R5.5 CLASSIFICATION only, and specifically NOT the interrupt-path DECISION ORDER that `65cuw0`'s E-03 delivered, whose only surviving coverage is `tests/test_oc_runipd.py::VerifierGateAndRunnerBugTests::test_discard_lane_reclaim` on the operator-discard branch, so the merged-lane reclaim branch is unguarded and is owned by backlog `dwfmxz` rather than fixed here; (2) that it drives the gate DIRECTLY rather than through `reclaim_lanes_on_interrupt`, which is a deliberate scope choice and means a regression that stops the interrupt path REACHING the gate would not fail this module; (3) that the `uncollected-submission` refusal it works around is itself a live question owned by backlog `nvymif`, so a future change there will need this module's receipt fixture revisited - and, measured at review, that ownership has MOVED: `nvymif` is `- Status: graduated` as of 2026-09-30 to pending plan `z8ex9f`, so the docstring must cite the PLAN as the live carrier and name the concrete hazard rather than a vague future change (F-14). Say that `z8ex9f` declares `agent_workflows/lane_containment.py` in scope, that its E-02 narrows `submission_retention` and its E-03 adds a landing condition whose absent-branch case BLOCKS, and that this module therefore depends on lanes that are MERGED and on a branch being threaded once that lands. A reader who breaks this module after `z8ex9f` must find the reason here rather than re-deriving it. THIS IS A SEPARATE E-ITEM RATHER THAN A CLAUSE OF E-03 because it is the difference between a guard and a false sense of one, and because an executor under time pressure writes the tests and skips the caveat.
  BOTH CITED ITEMS ALREADY EXIST AND MUST NOT BE RE-FILED: `dwfmxz` was filed AT AUTHORING (not left for the executor) because `check.ipd-uncarried-obligation` is an `error`-severity rule that requires a bare resolvable id6, so this plan could not honestly defer work to an item that did not exist yet; `nvymif` predates this plan. VERIFY both resolve rather than trusting the citation, AND VERIFY THEIR CURRENT STATUS rather than the status this plan recorded, since a citation can go stale in its status without going dangling; report what you find (measured at review: `dwfmxz` `open`, `nvymif` `graduated`). If either has since been closed or renamed, say so in the docstring rather than leaving a dead pointer, since a recorded id6 that does not resolve misleads worse than an absent one.
  - Depends on: E-03
  - Expected outcome: the module docstring names all three limits explicitly, including the surviving-coverage citation for the decision order and both backlog ids (`dwfmxz`, `nvymif`), each verified to resolve; no new backlog item is created.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- AN EXECUTED PLAN IS APPEND-ONLY, AND THAT IS WHAT DECIDES THIS PLAN'S SHAPE. `AGENTS.md`: "Never change what a plan already in `.aw/records/plans/executed/` RECORDS (its steps, evidence, results, or status): close a post-execution gap with a new corrective IPD, not an in-place edit. You MAY append a dated `## Workflow history` line to it that points at later work (for example 'partly replaced by <id6>')."
- THE NEAREST PRECEDENTS ARE EXECUTED AND SHOULD BE FOLLOWED RATHER THAN RE-DERIVED. Plan `bwo8hp` ("Record the V-02 contradiction on u23gbn and make a review round correct it") is the SAME defect class as this plan's first half: a `V-*` item in an executed plan demanding evidence that the plan's own ordering made impossible. Its E-01 establishes the append pattern (first record because the section is newest-first and `extract_newest_history_entry` reads the first; a NOTE token; cite by id6; hand-written because `aw ipd` has no `note` verb) and its E-02 establishes the appended-review-round pattern. Plan `cscv0c` established the same append pattern for a falsified premise. This plan follows both and adds nothing novel to the mechanism.
- THE REVIEWS TREE HAS ITS OWN DOCUMENTED CORRECTION VEHICLE, so E-02 invents nothing. `.aw/records/reviews/README.md`: rounds are "appended in order", "The LAST round in the file is the CURRENT one", and "Only the current round's findings are live." The `### Findings` and `### Decisions` column lists are specified there verbatim.
- THE REVISE-TIME SWEEP RULE NOW IN `plan-review` IS WHAT WOULD HAVE CAUGHT THIS, and it postdates the defect. `plan-review.md` and `plan-review-long/02-review-and-revise.md` both now carry "When a revision corrects a mechanism, ordering, or classification, the correction is not complete until every other item in the plan that quotes or depends on the replaced wording has been swept and reconciled", added by plan `bwo8hp` E-03. `65cuw0`'s round 3 had no such instruction. Recorded so a reviewer reads this plan as evidence the rule was needed, not as a new process proposal.
- `verify-execution`'s DIMENSION 1 ALREADY RATES THIS CASE, and the rating explains why `65cuw0` is legitimately `executed` despite the contradiction. `intent-audit.md`: an item whose evidence reports the demand unsatisfiable is `done` only with a stated reason, an empirical MEASUREMENT, and the satisfiable counterpart - and "even when the requirement is rated `done` under this bar, an unsatisfiable demand is a plan defect: the auditor must still report the contradiction as a finding". `65cuw0`'s V-03 clears all three parts of that bar (it pasted the two-line classification measurement), which is exactly why the remedy is a note rather than a re-execution, and this plan IS the finding that rule says must still be reported.
- WE TEST OUTCOMES, NEVER CODE STRUCTURE (maintainer ruling 2026-09-26, `AGENTS.md`, GUIDING_PRINCIPLES P16), and it constrains E-03 concretely: no `inspect`/`ast`/regex reads of production source, no symbol censuses, no docstring-text assertions. This is why E-03 writes a new outcome-level module instead of restoring `tests/test_lane_retention.py`, which carried several such pins.
- ONE DEFINITION OF THE TEARDOWN GATE EXISTS AND THIS PLAN MUST CONSUME IT, NOT RE-DERIVE IT: `lane_containment.teardown_lane_if_classified`, whose docstring states "ONE DEFINITION, called by both drivers (spec R6.1, R2.6)". E-03 drives that function; it must not reimplement the classification in the test.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Severity | Evidence | Finding |
|----|----------|----------|---------|
| F-01 | HIGH | `65cuw0` E-04 final sentence and V-03 `Required evidence`, both quoted | **THE REQUIREMENT IS UNSATISFIABLE AGAINST THE SPEC THE PLAN WAS APPROVED UNDER.** E-04 ends "an interrupted merged lane whose only unexplained content is a gitignored file must be PRESERVED, with its reason code recorded", and V-03 demands "the REFUSAL path: an interrupted merged lane whose only unexplained content is a GITIGNORED file must be preserved, with its `reason_codes` pasted (`unknown-ignored-file`)". Spec `7ckptx` R5.5 as amended reads "Gitignored files ... are disposable upon lane destruction and do not block teardown", and `lane_containment.RETENTION_UNKNOWN_IGNORED` documents itself "NEVER EMITTED BY `reason_codes` NOW, deliberately". The item's claim reproduced exactly. |
| F-02 | HIGH | Ran the real `lane_containment.inventory_lane` at authoring on real merged git lanes | **MEASURED, THE TWO CASES DIVERGE AS THE ITEM REPORTS.** With the submission question removed so it cannot mask the result: gitignored unexplained content -> `classified=True unknown_ignored=('build/precious.txt',) reason_codes=()`; untracked unexplained content -> `classified=False unknown_untracked=('unexplained.txt',) reason_codes=('unknown-untracked-file',)`. The ignored paths are still ENUMERATED, so "disposable" has not become "invisible". |
| F-03 | HIGH | Ran the real `lane_containment.teardown_lane_if_classified` at authoring, with a real run dir and a COMPLETE receipt, git 2.43.0 | **THE EVIDENCE E-03's TESTS WILL ASSERT IS REACHABLE, PROVEN BY PRODUCING IT.** Four merged lanes: `clean -> torn_down=True worktree_exists=False reason_codes=()`; `ignored -> torn_down=True worktree_exists=False reason_codes=()` with `unknown_ignored=('build/precious.txt',)` still enumerated; `untracked -> torn_down=False worktree_exists=True reason_codes=('unknown-untracked-file',)`; `dirty -> torn_down=False worktree_exists=True reason_codes=('dirty-tracked-file',)`. Recorded because a `V-*` demanding unproducible evidence is its own defect class (backlog `v75mym`), and this plan will not ship one. |
| F-04 | HIGH | Same probe, run with and without a receipt | **THE RECEIPT IS LOAD-BEARING FOR E-03 OR ALL FOUR CASES PASS VACUOUSLY.** With `run_dir`/`item` absent, `submission_retention` returns `uncollected=True` unconditionally, so the gitignored lane reports `classified=False reason_codes=('uncollected-submission',)` and every case fails classification for a reason unrelated to the property under test. A naive test would then pass under BOTH mutations in F-05. This is the same masking that broke `65cuw0`'s own round-1 design (its PR-102) and that backlog `nvymif` owns. |
| F-05 | BLOCKER | Applied the mutation to `LaneInventory.unknown`, ran the bare suite, reverted; `git diff --stat` empty after revert | **THE AMENDED BEHAVIOR HAS NO GUARD: THE `5w8g8j` FIX CAN BE FULLY REVERTED WITH THE SUITE GREEN.** Re-unioning `unknown_ignored` into `unknown` (which is precisely what the amendment removed, and which stranded 38 worktrees in production) yields `3246 passed, 2 skipped, 3 warnings`, identical to the baseline. So nothing in the suite distinguishes the amended rule from the pre-amendment one. |
| F-06 | BLOCKER | Same method, mutating `unknown` to drop `unknown_untracked`, reverted | **AND THE DATA-LOSS DIRECTION IS EQUALLY UNGUARDED, WHICH IS THE MORE SERIOUS HALF.** Dropping `unknown_untracked` from `unknown` makes a merged lane holding an unaccounted UNTRACKED file classify as accounted and become eligible for force-teardown - the exact `wfamig` hazard `65cuw0`'s Goal names ("a merged-ness-only teardown would have deleted the only copy"). Bare suite: `3246 passed, 2 skipped`. The backlog item states this hazard is "fully covered and pinned by two tests"; that was true when written and is false now. |
| F-07 | HIGH | `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24) `--stat`; `rg` over `tests/` | **THE CAUSE OF F-05 AND F-06 IS A KNOWN DELETION, NOT A NEVER-WRITTEN TEST.** That commit deleted `tests/test_lane_retention.py` (1064 lines, including `test_an_unknown_IGNORED_file_is_ENUMERATED_but_does_NOT_block_teardown`, `test_a_lane_holding_ONLY_gitignored_files_IS_torn_down`, and `test_gitignored_residue_does_NOT_mask_a_real_refusal`) and `tests/test_worktree_lease_merged_reclaim.py` (797 lines, the file `65cuw0` E-04 created). No surviving test file references `inventory_lane` or `teardown_lane_if_classified`; the only surviving reference to `reclaim_lanes_on_interrupt` is `tests/test_oc_runipd.py::VerifierGateAndRunnerBugTests::test_discard_lane_reclaim`, which drives the operator-DISCARD branch and not the merged-lane branch. |
| F-08 | MEDIUM | `lane_containment.submission_retention`; backlog `nvymif` | **A SECOND, DIFFERENT REFUSAL IS OUT OF SCOPE AND ALREADY OWNED.** Every interrupted lane reports `uncollected-submission` because an interrupted lane never has a completed receipt, which is why `65cuw0` could route only the NEW merged case through the gate (its decision `08-65cuw0-D1`). That is an R2.5 question, not an R5.5 one, and backlog `nvymif` carries it. Recorded so a reviewer does not read its absence as an oversight, and because E-03 must work around it (F-04). |
| F-09 | LOW | backlog `xvp5vx` | **THE GENERAL "WHAT ELSE DID THE TRIM LEAVE UNGUARDED" AUDIT IS ALREADY OWNED,** and carries the maintainer's directive that any such audit must ignore tests that pinned code, AST, or text. This plan closes ONE instance found incidentally; it does not attempt the sweep, and E-03 honors that directive by restoring outcomes only. |
| F-10 | LOW | `aw ipd --help` at authoring | **THERE IS NO TOOLED NOTE VERB FOR A PLAN,** so E-01's append is necessarily hand-written. `aw ipd` exposes `{lint,scaffold,sync,recheck-readiness,execute-set,board,set,dependencies,begin,finalize}` with no `note`, while `aw backlog note` and `aw specs note` both exist. Precedents `bwo8hp` and `cscv0c` recorded the same asymmetry. |
| F-11 | MEDIUM | `git log` on the three commits; `git merge-base --is-ancestor` for each pair | **THE CHRONOLOGY IS THE EXPLANATION, AND NO EXISTING ARTIFACT STATES IT.** The stale wording was authored by review round 2 in `59d1d833` (2026-09-17 21:49:19), the amendment landed in `e94a7c4e` (2026-09-18 00:34:38), and round 3 approved the plan in `9ecb9f3f` (2026-09-18 00:45:43) - 2h45m and then ELEVEN MINUTES later. Confirmed by ancestry: the amendment is NOT an ancestor of the round-2 commit (rc=1) and IS an ancestor of both the approval commit and the finalize commit (rc=0). So round 2 could not have known, and round 3 could have. This is a revision-sweep miss at the approval step, which is exactly what the sweep rule added later by `bwo8hp` exists to catch. |
| F-12 | LOW | The two pre-commit gates run against a staged probe append, then reverted | **THE APPEND ROUTE IS MEASURED TO PASS BOTH SHIPPED GATES,** so E-01 is not expected to be refused. With one inserted history line staged on the `65cuw0` file, `python3 -m agent_workflows ipd-executed-gate` exits 0 and `ipd-status-untooled-gate` exits 0, with `git diff --cached --numstat` reading `1 0`. The probe was fully reverted (`git status --short` clean). |
| F-14 | HIGH | ADDED AT REVIEW. `.aw/records/backlog/graduated/20260922-nvymif-01-nvymif-...backlog.md` now reads `- Status: graduated`, `- Graduated-To: nvymif`, graduated 2026-09-30 to plan `z8ex9f`; that plan's `- Scope-Paths:` names `agent_workflows/lane_containment.py` and its E-03 requires a blocking condition whose absent-branch case is BLOCKING | **`nvymif` GRADUATED AFTER THIS PLAN WAS AUTHORED, AND ITS CARRIER PLAN WILL BREAK THREE OF E-03's FOUR CASES.** This plan calls `nvymif` a live backlog question (F-08, E-04(3)) and V-04 requires it "shown to resolve"; measured at review it is no longer `open` but `graduated` to pending plan `z8ex9f` (`- Status: to-review`), so the citation is stale in its STATUS, though not dangling. That alone is minor. THE SERIOUS HALF IS A BEHAVIORAL COLLISION this plan could not have seen: `z8ex9f` E-02 narrows `submission_retention` so a provably-empty lane is no longer `uncollected`, and E-03 ADDS A NEW BLOCKING CONDITION to `LaneInventory` for work that has not landed on the integration target, threading a branch into `inventory_lane` as a new optional parameter and treating an ABSENT branch as BLOCKING ("When no branch is supplied the condition cannot be evaluated; treat that as BLOCKING"). This plan's E-03 drives `teardown_lane_if_classified` with a handle exposing only `.path` (there is no branch to thread, and `inventory_lane` takes a lane ROOT), so after `z8ex9f` lands EVERY case in this module would classify `False` on the new condition: `clean` and `ignored` would flip from `torn_down=True` to `False`, and the two refusal cases would pass for the WRONG reason. Whichever plan lands second breaks the other. Neither plan declares an `- Item-Dependencies:` edge and neither mentions the other. |
| F-13 | LOW | `plan_readiness` and `ipd_lifecycle` readers driven on temp copies before and after an inserted note | **INSERTING AT POSITION ONE CHANGES NO APPROVAL OR LIFECYCLE SIGNAL.** Measured on two temp copies so the tracked file was never mutated: `is_plan_review_approved` True both times; `newest_verdict` unchanged at `('positive', <the 2026-09-18 round-3 record>)`; `history_has_review_record` True both times; `_plan_status_events` 7 events with the same first event both times. Only `extract_newest_history_entry` changes, which is the intended effect. |

## Proposed changes (ordered, validatable)

1. E-01: one appended `## Workflow history` record on `65cuw0`, inserted FIRST, stating the unsatisfiable demand, the amendment that superseded it, the three-commit chronology, the recorded decision, and which case the real hazard is. Insertions only; cites `hyuos6`.
2. E-02: one appended `## Round 4` on `65cuw0`'s review record, with `### Findings` and `### Decisions` in the existing rounds' exact columns, ids in a fresh `PR-201+`/`D-6+` band, correcting Round 2's D-4 in substance and carrying the deleted-guard finding. Rounds 1 through 3 untouched.
3. E-03: a new `tests/test_lane_retention_amended_r55.py` pinning the amended R5.5 classification by outcome across four lane shapes, with a real collection receipt, proven load-bearing by mutation in both directions.
4. E-04: the honest-limit docstring on that module, naming what it does NOT guard (the interrupt-path decision order), that it drives the gate directly, and the `nvymif` dependency.

## Deferred / out of scope (with reason)

- AMENDING SPEC `7ckptx` R5.5 TO RESTORE THE IGNORED-FILE REFUSAL, which is the second branch backlog `0kdwm3` offers. REFUSED rather than deferred, and the reason is measured rather than preferred: the amendment's own record states the blanket refusal "caused 100 percent of clean test runs to fail teardown, stranding dozens of worktrees on disk", and R6.1 forbids a rule stricter on one path than on another, so an interrupt-path-only restoration would re-create a measured production failure in the forked form R6.1 prohibits. The protection that matters is untouched: dirty tracked, unknown untracked, and uncollected submission all still refuse (F-02, F-03).
  - Carrier-Declined: No future work is owed. This is a settled negative finding, not a deferral: the maintainer's 2026-09-18 ruling is the authority, the shipped behavior complies with it, and filing a carrier would misrepresent a decision already taken as an outstanding task. If the maintainer nevertheless prefers the pre-amendment rule, that is a spec amendment they own and it needs its own plan, as the backlog item itself says.
- EDITING `65cuw0`'s E-04 OR V-03 TEXT, or its `## Approval and execution gate` paragraph. Forbidden: `AGENTS.md` says never change what a plan in `executed/` records and directs a corrective IPD instead. Beyond the prohibition it would be WRONG on the merits: V-03's `Observed evidence` is the true record of what the executor measured and decided, and rewriting the demand to match it would erase the evidence that an approval round shipped a self-contradiction - which is the very fact F-11 makes readable.
  - Carrier-Declined: The prohibition is explicit and unconditional, the sanctioned alternative is performed in full by E-01 and E-02, and the preserved record is more valuable than the tidier file, so no future work is owed.
- THE `uncollected-submission`-REFUSES-EVERY-INTERRUPTED-LANE DEFECT (F-08). Out of scope because it is a spec R2.5 question ("what does an absent receipt mean for a lane that provably submitted nothing?"), not the R5.5 wording question this plan graduated from, and answering it changes the retention gate's behavior rather than a record. THE CARRIER HAS ADVANCED SINCE AUTHORING and the row is kept pointing at the item deliberately: `nvymif` is now `graduated` to pending plan `z8ex9f`, which amends R2.5 and narrows the predicate exactly as this row anticipated, so the obligation is being discharged rather than merely parked. The `- Carrier:` stays `nvymif` because the graduated item is the durable record of the obligation and resolves; `z8ex9f` is named in E-04 and F-14 as the live carrier a reader should follow.
  - Carrier: nvymif
- THE GENERAL AUDIT OF WHAT ELSE `19313eed` LEFT UNGUARDED (F-09). This plan closes one instance it found incidentally while verifying its own premise; the systematic sweep is a different and much larger piece of work with its own maintainer directive attached.
  - Carrier: xvp5vx
- A GUARD FOR THE INTERRUPT-PATH DECISION ORDER, i.e. that `reclaim_lanes_on_interrupt` consults merged-ness BEFORE the `holds_work` bail-out. Genuinely wanted and genuinely out of scope here: it needs a driver-level fixture with a populated run state on BOTH hosts (the deleted `TheInterruptBehaviorTests` ran eleven such cases), which is a materially larger surface than the gate-level classification E-03 restores, and `65cuw0`'s round 2 measured that this is the half where a false green is easiest to ship. E-04 requires the new module to SAY it does not cover this, so the hole is documented rather than implied.
  - Carrier: dwfmxz
- RESTORING EITHER DELETED TEST FILE WHOLESALE. Excluded by the 2026-09-26 no-code-pinning ruling: both carried structure pins (`test_the_status_args_carry_all_three_flags`, `test_each_retention_symbol_has_exactly_one_definition_in_the_shared_home`, and the whole `TheNoDirectForceTeardownTests` AST class), and backlog `xvp5vx` carries the maintainer's directive that any audit of deleted tests "must strictly ignore tests that pinned code, AST, or text, and must never propose restoring them".
  - Carrier-Declined: Nothing is owed. The behavioral subset worth having is restored by E-03, and the structure-pinning subset is forbidden to restore, so there is no residue to carry.

## Scope check

- Over-scope: none. Each of the three `- Scope-Paths:` entries is required by a named E-item: the `65cuw0` plan file by E-01, its review record by E-02, and the new test module by E-03 and E-04. No production source path appears, deliberately: no shipped behavior is wrong, and touching `lane_containment.py` would convert a record correction plus a test restoration into a behavior change.
- Under-scope: CHECKED, and four adjacent things are named rather than left ambiguous. FIRST, spec `7ckptx` is EXCLUDED with a measured reason (the Deferred row above), and its absence from `- Scope-Paths:` is the declaration the runners reconcile against - this plan declares NO spec edit and must make none. SECOND, `tests/test_oc_runipd.py` is excluded although it holds the only surviving `reclaim_lanes_on_interrupt` reference: extending it is the decision-order guard this plan defers to carrier `dwfmxz`, and adding a second concern to E-03 is what the right-sizing rule forbids. THIRD, backlog `0kdwm3` itself is NOT declared, because the runner sets `graduated` on verification and this plan must not transition it. FOURTH, no backlog path is declared and NONE is needed, because `dwfmxz` was filed at AUTHORING rather than at execution: every E-item here writes only the three declared paths, and E-04 merely CITES two existing items. An executor who finds itself needing to write under `.aw/records/backlog/` has departed from the plan and should stop rather than widen scope. FIFTH, ADDED AT REVIEW: `agent_workflows/lane_containment.py` is excluded and must stay excluded even though E-03's cases would all invert if pending plan `z8ex9f` lands first (F-14). The remedy there is to adapt this plan's FIXTURE, never the gate: `z8ex9f` declares that file and owns the change, so editing it here would be an undeclared production behavior change that also collides with an in-flight plan.
  THE AUTHORING COMMIT CARRIES ONE PATH THIS PLAN DOES NOT DECLARE, stated plainly so a reviewer does not read it as undeclared scope: `dwfmxz`'s own item file. It is authored BEFORE this plan is reviewed, not during execution, so it is part of the authoring change rather than of the executed diff the finalize gate reconciles. The reason it could not be deferred is mechanical: `check.ipd-uncarried-obligation` is `error`-severity and requires a BARE resolvable id6, so a promise to file later fails `aw check plans` before this plan can execute. Measured at authoring - the first draft of this plan wrote a prose carrier and the rule fired with "malformed `Carrier` reference(s) ... (expected a bare 6-char id6)"; filing the item cleared it.

## Required tests / validation

- The BARE suite, `python3 -m pytest` (or `make test`), per the execution contract. Do NOT add `-n0`, a second `-q`, or `-p no:randomly`; `pyproject.toml` `addopts` already supplies the quiet, parallel, fast-subset configuration. Paste the ACTUAL summary line. Compare failing NODE IDS, not totals.
  - THE AUTHORED BASELINE IS `3246 passed, 2 skipped, 3 warnings in 52.88s` at HEAD `9733d47a`, measured bare in this lane, with ZERO failures. It is there to be COMPARED against, not copied. Expect the count to RISE by the number of cases E-03 adds; a count that does not rise means the new module did not collect. RE-MEASURED AT REVIEW, which is exactly why the paragraph above says re-derive: at review HEAD `84cdeb94` the bare suite reports `3353 passed, 2 skipped, 3 warnings in 108.82s`, 107 tests above the authored figure. Neither number is the bar; the RECONCILED DELTA is.
  - BASELINE IS GREEN, SO THE BAR IS ABSOLUTE RATHER THAN DIFFERENTIAL: any failing node id is this plan's to explain. If a foreign red has appeared by execution time, re-run against a clean HEAD, attribute it honestly, and do not sweep it into this plan's commit.
- `python3 -m pytest tests/test_lane_retention_amended_r55.py -o addopts=""` immediately after E-03, with the per-test counts, plus the TWO mutation demonstrations the V-items require. Clearing `addopts` explicitly is the sanctioned way to get per-test counts from a narrowed run.
- THE TWO MUTATIONS ARE PERFORMED ON A COPY-AND-REVERT BASIS AND MUST LEAVE THE TREE CLEAN: apply, run, paste the failure, revert, and paste `git diff --stat agent_workflows/lane_containment.py` showing EMPTY. A mutation left in the tree would be a production behavior change this plan does not declare. Both mutations were performed and reverted at authoring by exactly this method (F-05, F-06).
- The two pre-commit gates run directly against the staged append: `python3 -m agent_workflows ipd-executed-gate` and `python3 -m agent_workflows ipd-status-untooled-gate`, both expected to exit 0 (measured at authoring, F-12), plus `aw check plans` and `aw check reviews`.
- `aw ipd lint` on THIS plan at `--phase pre-transition`, which must conform with zero findings before the terminal transition.
- HONEST LIMIT ON WHAT THE AUTOMATED CHECKS CAN SEE, stated because a green suite would otherwise be over-read. NOTHING in the suite reads the CONTENT of E-01's or E-02's appends: `aw ipd lint` on an executed plan reports `legacy/not evaluated` (measured on `65cuw0`: exit 0, `legacy/not evaluated`), and the two gates test path, id and status rather than prose. So the accuracy of both appends rests ENTIRELY on V-01 and V-02 inspecting the actual diff. Those inspections are load-bearing validation, not a formality. E-03 is the opposite case: it is verified by execution, and its mutation demonstrations are what prove it is not a vacuous guard.

## Spec / documentation sync

- NO SPEC AMENDMENT, AND THIS IS THE LOAD-BEARING DECLARATION OF THIS PLAN. No `.spec.md` path appears in `- Scope-Paths:`, which is what the runners announce and reconcile against. Spec `7ckptx` R5.5 and A15 DO govern this plan's subject, and they are satisfied by the code as it stands; this plan's whole argument is that the RECORD must be reconciled to the amended spec rather than the spec forked to match a stale record. If an executor concludes that E-01, E-02, E-03 or E-04 requires narrowing R5.5, STOP AND ASK; do not edit the spec.
- THE SPEC IS NEVERTHELESS MID-TRANSITION AND A REVIEWER SHOULD KNOW: `7ckptx` is `approved` with pending plans `e9ekuj` and `uuh71v` (Set `specfin7ck`) moving it toward `implemented`, and `uuh71v` E-03 owes a per-clause demonstration of amended A15 including "a lane holding ONLY gitignored content being torn down". That is the SAME property E-03 here guards. NO DEPENDENCY IS DECLARED between them and none is needed, because the two obligations are different in kind: `uuh71v` owes a one-time pasted DEMONSTRATION for a spec transition packet, while this plan owes a DURABLE test guard, and neither blocks the other in either order. Recorded so a reviewer does not read the overlap as duplication or as a missing `Item-Dependencies` edge.
- A THIRD PENDING PLAN AMENDS THE SAME SPEC AND CHANGES THE PREDICATE E-03 ASSERTS ON, AND THAT ONE IS NOT BENIGN (F-14, added at review). `z8ex9f` (Set `nvymif`, `- Status: to-review`) declares `agent_workflows/lane_containment.py` AND the `7ckptx` spec file, amends R2.5, narrows `submission_retention`, and adds a landing condition to `LaneInventory` whose absent-branch case BLOCKS. STILL NO `- Item-Dependencies:` EDGE IS DECLARED, and the reason is the same one this repository has recorded before: the grammar offers `executed:`/`exists:`/`state:` edges only, with no way to say "prefer after", and `z8ex9f` is `to-review` rather than approved, so an `executed:` edge would gate this low-priority followup behind an unrelated medium-priority chore's whole review and execution cycle. The collision is handled INSIDE E-03 instead, by requiring a re-measurement at execution and branching on what it finds, which works in either order. This plan STILL DECLARES NO SPEC EDIT: `z8ex9f` owns the R2.5 amendment and this plan must not touch it.
- NO `docs/` CHANGE. This plan adds no command, flag, or user-facing surface.
- NO `AGENTS.md` OR WORKFLOW-BODY CHANGE. The revise-time sweep rule that would have caught this already shipped (plan `bwo8hp` E-03), and `verify-execution`'s Dimension 1 already carries the disposition for an unsatisfiable `V-*`. Adding a second statement of either would be the duplication those bodies explicitly call a defect.

## Open questions

### OQ-01: Annotate the executed plan, or amend spec R5.5 to restore the pre-amendment refusal on the interrupt path?

- Blocking: no
- Status: resolved
- Owner: opencode (author)
- Resolution or deferral rationale: ANNOTATE, and REFUSE the amendment. Resolved from repository evidence rather than escalated, because the repository answers it twice over. FIRST, the amendment's own recorded reason is a production measurement, not a preference: "the blanket refusal on ignored files caused 100 percent of clean test runs to fail teardown, stranding dozens of worktrees on disk", because running a test suite or an agent routinely writes `__pycache__` and `node_modules` into a lane. Restoring it on the interrupt path would re-create that failure for every interrupted run. SECOND, spec R6.1 requires a multi-surface rule to live in ONE predicate, so an interrupt-path-only refusal is a FORK the spec forbids, and `65cuw0`'s own executor named this as the reason it did not honor the literal wording. The backlog item presents the amendment branch as legitimate and conditions it on the MAINTAINER preferring the pre-amendment rule; that is a preference nobody has expressed, and a plan may not manufacture one. Non-blocking: this plan's four E-items are identical under either answer except that the amend branch would add a spec path to `- Scope-Paths:`, and if the maintainer does prefer it, that is a separate plan by the item's own wording.

### OQ-02: Should the deleted-guard fix (E-03, E-04) live in THIS plan, or be filed as its own item?

- Blocking: no
- Status: resolved
- Owner: opencode (author)
- Resolution or deferral rationale: IN THIS PLAN, on three grounds measured rather than assumed. (1) PROXIMITY: this plan's own premise is a claim about the R5.5 classification, and F-05/F-06 measure that the claim is unguarded; a plan that reports "nothing behaves incorrectly" while leaving the behavior one careless edit from data loss would be technically true and practically useless. (2) SIZE: the guard is four cases against one already-shared function whose evidence shape is fully measured (F-03), so it is one focused pass, well inside the right-sizing rule. (3) RISK OF DEFERRAL: F-06 is the data-loss direction, and the repository's own history on this exact predicate (`65cuw0`'s PR-003, which caught a design that would have force-deleted a lane holding the only copy of a plan) is the argument against parking it behind another approval cycle. WHAT WAS NOT ABSORBED, to keep this answer honest: the interrupt-path DECISION-ORDER guard is deferred with a carrier, because it needs a two-host driver fixture and would double this plan's surface. Non-blocking: if a reviewer prefers the split, E-03 and E-04 lift out as a sibling plan with no change to E-01, E-02, or any Scope-Path but the test file.

### OQ-03: Should Round 4 of the review record correct Round 2's D-4, given that D-4's reasoning was sound at the time?

- Blocking: no
- Status: resolved
- Owner: opencode (author)
- Resolution or deferral rationale: YES, and the correction must SEPARATE the layer question from the substance question, because conflating them would misrepresent a correct decision as a wrong one. D-4 asked whether the ignored-file case belonged at the `LaneState` reading layer or the behavior layer, and answered the behavior layer because the reading layer does not consult the inventory at all. THAT REASONING WAS RIGHT AND REMAINS RIGHT. What went stale is the case's SUBSTANCE: D-4 relocated a requirement that the spec made obsolete 2h45m later (F-11), and the record should say so, because a reader auditing why the plan shipped a contradiction will land on D-4 and must not conclude that the layer analysis was the error. The alternative considered was recording the correction only on the plan (E-01) and leaving the review alone: rejected because the review is where the requirement was AUTHORED, so a plan-only note would leave the originating decision reading as fully sound and the next reviewer with no reason to sweep after a spec amendment. Non-blocking: E-02's substance is fixed either way; only the finding's framing turns on this.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: THE FULL `git diff` of the `65cuw0` file, pasted, plus `git diff --numstat` for it. The diff MUST show insertions only and ZERO deletions (numstat's second column must be `0`), must not contain E-04's text or either of V-03's evidence blocks, and must not contain any `- Field:` metadata line. Then paste the new record itself and confirm IN YOUR OWN WORDS that it states all FIVE required things: the unsatisfiable demand (naming both E-04 and V-03); WHY (the 2026-09-18 R5.5 amendment plus the never-emitted reason code); the THREE-COMMIT CHRONOLOGY with the 2h45m and eleven-minute gaps; that decision `08-65cuw0-D3` and V-03's `Observed evidence` are the authoritative account of the handling; and that the real refusal case is the UNTRACKED one, so retention is not weakened. A record missing any of the five is a FAILED validation.
  - PROVE THE PLACEMENT IS FIRST AND SAFE, not merely correct by convention. Paste the first three lines under `## Workflow history` to show the new record is FIRST, and the plan's `- Status:` line plus `git status --short` for that path to show the status and the directory are unchanged. Then paste, BEFORE and AFTER, all five history consumers: `plan_readiness.is_plan_review_approved`, `plan_readiness.extract_newest_history_entry`, `plan_readiness.newest_verdict`, `plan_readiness.history_has_review_record`, and `ipd_lifecycle._plan_status_events` (report its event COUNT and its first event). ONLY `extract_newest_history_entry` MAY CHANGE. Any of the other four changing is a FAILED validation regardless of the diff, because a history note would then have altered a signal some other consumer reads, which is the whole risk of inserting at position one.
  - MIND THE TWO SIGNATURES, because they differ and passing the wrong one raises rather than answering: `is_plan_review_approved` takes a **`Path`** (its body calls `plan_path.read_text(...)`, so a string raises `AttributeError`), while the other readers take the **text**. Drive the before/after pair on two TEMP-FILE COPIES rather than on the real file, so a probe that raises midway cannot leave the tracked file mutated.
  - MEASURED AT AUTHORING BY EXACTLY THIS METHOD, so this is a confirmation and not an exploration (F-13): `is_plan_review_approved` True both times; `newest_verdict` unchanged at `('positive', <the 2026-09-18 round-3 record>)`; `history_has_review_record` True both times; `_plan_status_events` 7 events with first event `('2026-09-17', 'draft', 'opencode/its_direct-pt3-claude-opus-5-1m-us')` both times. A DIFFERENT result at execution time is a finding worth reporting, not a number to overwrite.
  - Observed evidence: PASS. 65cuw0 workflow history note verified by git diff, numstat 1 0, five statements confirmed, placement first, and all five history consumers identical.
    1. Full `git diff` of `.aw/records/plans/executed/20260917-laneorph-01-65cuw0-fix-lane-reclaim-so-a-merged-lane-is-reclaimable-and-torn-do.ipd.md`:
    ```diff
    diff --git a/.aw/records/plans/executed/20260917-laneorph-01-65cuw0-fix-lane-reclaim-so-a-merged-lane-is-reclaimable-and-torn-do.ipd.md b/.aw/records/plans/executed/20260917-laneorph-01-65cuw0-fix-lane-reclaim-so-a-merged-lane-is-reclaimable-and-torn-do.ipd.md
    index bce85ee71..c49cf5d7f 100644
    --- a/.aw/records/plans/executed/20260917-laneorph-01-65cuw0-fix-lane-reclaim-so-a-merged-lane-is-reclaimable-and-torn-do.ipd.md
    +++ b/.aw/records/plans/executed/20260917-laneorph-01-65cuw0-fix-lane-reclaim-so-a-merged-lane-is-reclaimable-and-torn-do.ipd.md
    @@ -17,6 +17,7 @@
     - Id: 65cuw0

     ## Workflow history
    +- 2026-10-01 note (hyuos6): E-04's final sentence and V-03's `Required evidence` both demand an interrupted merged lane holding only a gitignored file be PRESERVED with reason code `unknown-ignored-file`, and this demand is UNSATISFIABLE against the spec the plan was approved under. Spec `7ckptx` R5.5 was amended 2026-09-18 to make gitignored content disposable upon lane destruction, and `lane_containment.RETENTION_UNKNOWN_IGNORED` is documented as never emitted by `reason_codes` now, so honoring the wording would have forked R5.5 in the direction R6.1 forbids. The wording was authored by review round 2 (commit `59d1d833`, 2026-09-17 21:49) and the amendment landed 2h45m later (commit `e94a7c4e`, 2026-09-18 00:34), eleven minutes before round 3 approved the plan (commit `9ecb9f3f`, 2026-09-18 00:45) without sweeping V-03 for it - a revision-sweep miss rather than an executor deviation. The executor's handling is recorded as decision `08-65cuw0-D3` and V-03's `Observed evidence` block is the authoritative account of it. The retention hazard the requirement existed for is the UNTRACKED case, which genuinely refuses (`unknown-untracked-file`), so retention is not weakened; the amended classification guard is restored by hyuos6 in `tests/test_lane_retention_amended_r55.py`.
     - 2026-09-22 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: 65cuw0 verified (set laneorph, attempt 1).
     - 2026-09-19 approved (aw set): status set to approved
     - 2026-09-18 reviewed (aw set): status set to reviewed
    ```
    `git diff --numstat`:
    `1	0	.aw/records/plans/executed/20260917-laneorph-01-65cuw0-fix-lane-reclaim-so-a-merged-lane-is-reclaimable-and-torn-do.ipd.md` (insertions only, 0 deletions). No `- Field:` lines, E-04 text, or V-03 evidence blocks touched.

    2. Five required statements confirmed in own words:
       - Unsatisfiable demand: names E-04's final sentence and V-03's `Required evidence` for gitignored preservation with `unknown-ignored-file`.
       - Why: Spec `7ckptx` R5.5 amendment on 2026-09-18 made gitignored files disposable on lane destruction and `RETENTION_UNKNOWN_IGNORED` is never emitted; literal compliance would fork R5.5 against R6.1.
       - Chronology: Authored by review round 2 (`59d1d833`, 2026-09-17 21:49), R5.5 amended 2h45m later (`e94a7c4e`, 2026-09-18 00:34), 11 minutes before round 3 approved (`9ecb9f3f`, 2026-09-18 00:45) without sweeping V-03.
       - Handling authority: Recorded as decision `08-65cuw0-D3`, V-03's `Observed evidence` is authoritative.
       - Real hazard: The untracked case genuinely refuses (`unknown-untracked-file`); cites `hyuos6` and restored guard `tests/test_lane_retention_amended_r55.py`.

    3. First 3 lines under `## Workflow history`:
    ```text
    ## Workflow history
    - 2026-10-01 note (hyuos6): E-04's final sentence and V-03's `Required evidence` both demand an interrupted merged lane holding only a gitignored file be PRESERVED with reason code `unknown-ignored-file`, and this demand is UNSATISFIABLE against the spec the plan was approved under. Spec `7ckptx` R5.5 was amended 2026-09-18 to make gitignored content disposable upon lane destruction, and `lane_containment.RETENTION_UNKNOWN_IGNORED` is documented as never emitted by `reason_codes` now, so honoring the wording would have forked R5.5 in the direction R6.1 forbids. The wording was authored by review round 2 (commit `59d1d833`, 2026-09-17 21:49) and the amendment landed 2h45m later (commit `e94a7c4e`, 2026-09-18 00:34), eleven minutes before round 3 approved the plan (commit `9ecb9f3f`, 2026-09-18 00:45) without sweeping V-03 for it - a revision-sweep miss rather than an executor deviation. The executor's handling is recorded as decision `08-65cuw0-D3` and V-03's `Observed evidence` block is the authoritative account of it. The retention hazard the requirement existed for is the UNTRACKED case, which genuinely refuses (`unknown-untracked-file`), so retention is not weakened; the amended classification guard is restored by hyuos6 in `tests/test_lane_retention_amended_r55.py`.
    - 2026-09-22 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: 65cuw0 verified (set laneorph, attempt 1).
    - 2026-09-19 approved (aw set): status set to approved
    ```
    Plan metadata: `- Status: executed` unchanged, path remains `.aw/records/plans/executed/...`.

    4. Five history consumers Before and After:
    ```text
    === BEFORE ===
    is_plan_review_approved: True
    extract_newest_history_entry: - 2026-09-22 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: 65cuw0 verified (set laneorph, attempt 1).
    newest_verdict: ('positive', '- 2026-09-18 reviewed (aw set): plan-review round 3 complete: APPROVE WITH REVISIONS APPLIED. Maintainer resolved OQ-03, OQ-04, and OQ-05. PR-101 and PR-103 marked FIXED. Proceed with decision-order change in reclaim_lanes_on_interrupt so merged lanes are checked before holds_work bails out. Deleting the branch of a provably-merged lane on interrupt is safe and standard Git hygiene since all commits are in main. Readiness go-pending-approval.')
    history_has_review_record: True
    _plan_status_events count: 7 first event: ('2026-09-17', 'draft', 'opencode/its_direct-pt3-claude-opus-5-1m-us')
    === AFTER ===
    is_plan_review_approved: True
    extract_newest_history_entry: - 2026-10-01 note (hyuos6): E-04's final sentence and V-03's `Required evidence` both demand an interrupted merged lane holding only a gitignored file be PRESERVED with reason code `unknown-ignored-file`, and this demand is UNSATISFIABLE against the spec the plan was approved under. Spec `7ckptx` R5.5 was amended 2026-09-18 to make gitignored content disposable upon lane destruction, and `lane_containment.RETENTION_UNKNOWN_IGNORED` is documented as never emitted by `reason_codes` now, so honoring the wording would have forked R5.5 in the direction R6.1 forbids. The wording was authored by review round 2 (commit `59d1d833`, 2026-09-17 21:49) and the amendment landed 2h45m later (commit `e94a7c4e`, 2026-09-18 00:34), eleven minutes before round 3 approved the plan (commit `9ecb9f3f`, 2026-09-18 00:45) without sweeping V-03 for it - a revision-sweep miss rather than an executor deviation. The executor's handling is recorded as decision `08-65cuw0-D3` and V-03's `Observed evidence` block is the authoritative account of it. The retention hazard the requirement existed for is the UNTRACKED case, which genuinely refuses (`unknown-untracked-file`), so retention is not weakened; the amended classification guard is restored by hyuos6 in `tests/test_lane_retention_amended_r55.py`.
    newest_verdict: ('positive', '- 2026-09-18 reviewed (aw set): plan-review round 3 complete: APPROVE WITH REVISIONS APPLIED. Maintainer resolved OQ-03, OQ-04, and OQ-05. PR-101 and PR-103 marked FIXED. Proceed with decision-order change in reclaim_lanes_on_interrupt so merged lanes are checked before holds_work bails out. Deleting the branch of a provably-merged lane on interrupt is safe and standard Git hygiene since all commits are in main. Readiness go-pending-approval.')
    history_has_review_record: True
    _plan_status_events count: 7 first event: ('2026-09-17', 'draft', 'opencode/its_direct-pt3-claude-opus-5-1m-us')
    ```
    Only `extract_newest_history_entry` changed; all other signals identical.
    Gates: `python3 -m agent_workflows ipd-executed-gate` and `python3 -m agent_workflows ipd-status-untooled-gate` exit 0.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the `git diff` of the review record, pasted, plus `git diff --numstat` showing insertions only and ZERO deletions. Confirm in your own words that `## Round 4` sits AFTER Round 3, that its `### Findings` table carries exactly the nine columns the existing rounds use and its `### Decisions` table exactly six, and that every new id is in the `PR-201+`/`D-6+` band with no reuse of `PR-101`..`PR-107` or `D-1`..`D-5`. Quote the three required rows: the D-4 supersession finding (which MUST state that D-4's LAYER reasoning was correct and only its SUBSTANCE went stale, per OQ-03), the deleted-guard finding marked FIXED by E-03, and the append-not-amend decision row naming the R5.5-amendment alternative and why it was rejected.
  - PROVE THE EARLIER ROUNDS AND THE FRONT MATTER ARE UNTOUCHED: paste `git diff` context showing no line inside Rounds 1 through 3 changed, and paste the front-matter block showing `- Subject-Id: 65cuw0`, `- Subject-Type: ipd` and `- Verdict: APPROVE WITH REVISIONS APPLIED` byte-identical to HEAD. A changed `- Verdict:` is a FAILED validation even if every table is perfect: the plan WAS approved with revisions applied, and rewriting that field would forge a different review outcome.
  - THEN PROVE THE TOOLING STILL PARSES IT: paste `aw check reviews` output and confirm no finding is attributable to this change, and paste `review_findings` reading this file back showing Round 4's rows parsed with their severities. A malformed table that no consumer can read would make the correction invisible to exactly the tooling this tree exists to serve.
  - Observed evidence: PASS. Review record Round 4 verified by git diff, numstat 19 0, PR-201/PR-202/D-6 tables, rounds 1-3 untouched, and aw check reviews passes.
    1. Full `git diff` of `.aw/records/reviews/20260917-laneorph-01-65cuw0-fix-lane-reclaim-so-a-merged-lane-is-reclaimable-and-torn-do.review.md`:
    ```diff
    diff --git a/.aw/records/reviews/20260917-laneorph-01-65cuw0-fix-lane-reclaim-so-a-merged-lane-is-reclaimable-and-torn-do.review.md b/.aw/records/reviews/20260917-laneorph-01-65cuw0-fix-lane-reclaim-so-a-merged-lane-is-reclaimable-and-torn-do.review.md
    index 10eb0a536..293297a7a 100644
    --- a/.aw/records/reviews/20260917-laneorph-01-65cuw0-fix-lane-reclaim-so-a-merged-lane-is-reclaimable-and-torn-do.review.md
    +++ b/.aw/records/reviews/20260917-laneorph-01-65cuw0-fix-lane-reclaim-so-a-merged-lane-is-reclaimable-and-torn-do.review.md
    @@ -193,4 +193,23 @@
     - **PR-103 / OQ-05 RESOLVED**: Option (c) chosen. Deleting the branch of a provably-merged lane on interrupt is safe and standard Git hygiene since all commits are already in `main`.
     - **Verdict**: `APPROVE WITH REVISIONS APPLIED`.
     - **Readiness**: Promoted to `go-pending-approval`.
    +
    +## Round 4
    +
    +Reviewed on 2026-10-01 for plan `hyuos6` (reconciling `65cuw0`'s V-03 gitignored-refusal wording with amended spec `7ckptx` R5.5 and restoring the deleted test guard).
    +
    +**Disclosure**: This round was prepared by an AI assistant in the same model family as the author and reviewers of Rounds 1 through 3, so a reader should evaluate it with the awareness of a near-self-review.
    +
    +### Findings
    +
    +| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
    +|----|----------|-------|------|----------|---------|------------------|----------|------------|
    +| PR-201 | HIGH | IN-SCOPE | A. correctness; F. honest documentation | Commit `59d1d833` (2026-09-17 21:49), commit `e94a7c4e` (2026-09-18 00:34), commit `9ecb9f3f` (2026-09-18 00:45) | **D-4's SUBSTANCE WAS SUPERSEDED 2h45m AFTER AUTHORING.** Round 2's D-4 correctly relocated the ignored-file case to the behavior layer (E-03/V-03) because the reading layer does not consult the inventory, but its SUBSTANCE went stale 2h45m later when commit `e94a7c4e` amended `7ckptx` R5.5 to make gitignored content disposable upon lane destruction, eleven minutes before round 3 approved the plan in `9ecb9f3f` without sweeping V-03. D-4's LAYER reasoning was correct and remains correct; only the requirement's substance went stale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | RESOLVED by plan `hyuos6` E-01: appended note to `65cuw0` workflow history recording the supersession, the three-commit chronology, and that the untracked case is the true retention hazard. |
    +| PR-202 | HIGH | IN-SCOPE | E. testing | Commit `19313eed` (2026-09-24) deleted `tests/test_lane_retention.py` and `tests/test_worktree_lease_merged_reclaim.py`; bare suite remained green under mutation in both directions (`LaneInventory.unknown` re-unioning `unknown_ignored` and dropping `unknown_untracked` both passed bare suite). | **THE AMENDED R5.5 RETENTION CLASSIFICATION LOST ITS TEST GUARDS.** Commit `19313eed` deleted both guarding test files, leaving the amended R5.5 teardown classification and the data-loss protection unguarded and green under mutation in both directions. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | FIXED by plan `hyuos6` E-03: restored outcome-level guard in `tests/test_lane_retention_amended_r55.py` proving both mutations fail. |
    +
    +### Decisions
    +
    +| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
    +|----|----------|--------|-------------------------|-------|------------|
    +| D-6 | How should the stale V-03 requirement and deleted guard be reconciled? | Append dated corrections to `65cuw0` and this review record, and restore the outcome guard in a new test module; refuse amending R5.5. | (a) Amend spec `7ckptx` R5.5 to restore the pre-amendment refusal on the interrupt path: rejected because the amendment's record proves blanket refusal caused 100% teardown failures on clean test runs, and R6.1 forbids an interrupt-path-only fork. (b) Rewrite `65cuw0`'s V-03 in place: rejected because `AGENTS.md` strictly forbids rewriting executed plan records. | Spec `7ckptx` R5.5 and R6.1; `AGENTS.md` executed plan append rule; plan `hyuos6` OQ-01. | yes |
    ```
    `git diff --numstat`:
    `19	0	.aw/records/reviews/20260917-laneorph-01-65cuw0-fix-lane-reclaim-so-a-merged-lane-is-reclaimable-and-torn-do.review.md` (insertions only, 0 deletions).

    2. Structural confirmation:
       - `## Round 4` sits strictly after `## Round 3`.
       - Findings table carries 9 columns: `ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution`.
       - Decisions table carries 6 columns: `ID | Question | Chosen | Alternatives considered | Basis | Reversible`.
       - IDs use fresh band: `PR-201`, `PR-202`, `D-6` (no reuse of PR-101..107 or D-1..5).
       - Quoted rows: PR-201 states D-4 layer reasoning was correct and only substance went stale 2h45m later; PR-202 records deleted test guard marked FIXED by E-03; D-6 records append-not-amend choice and rejects R5.5 amendment alternative.

    3. Front matter and earlier rounds untouched:
    ```text
    # Review findings: plan 65cuw0

    - Subject-Id: 65cuw0
    - Subject-Type: ipd
    - Reviewed-At: 2026-09-18
    - Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
    - Verdict: APPROVE WITH REVISIONS APPLIED
    ```
    Context shows zero modifications to rounds 1-3 or front-matter.

    4. Tooling parsing verification:
       - `aw check reviews` output:
         `✓ CONFORMS  671 reviews checked, errors 0, warnings 0`
       - `review_findings.parse_review_file`:
         Round 4 parsed as current round (number 4).
         Findings:
         `PR-201: severity=high, scope=IN-SCOPE, area=A. correctness; F. honest documentation, decision=fixed`
         `PR-202: severity=high, scope=IN-SCOPE, area=E. testing, decision=fixed`
         Decisions:
         `D-6: How should the stale V-03 requirement and deleted guard be reconciled?`
         `unresolved_findings: ()` (both marked fixed).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: `python3 -m pytest tests/test_lane_retention_amended_r55.py -o addopts=""` with the per-test names and the summary line pasted, PLUS the four asserted outcomes shown explicitly: gitignored-only -> `torn_down=True`, `reason_codes=()`, worktree gone; untracked -> `torn_down=False`, `reason_codes=('unknown-untracked-file',)`, file still on disk; dirty tracked -> `torn_down=False`, `reason_codes=('dirty-tracked-file',)`; clean -> `torn_down=True`. Plus the assertion that `unknown_ignored` is still ENUMERATED in the ignored case, since "disposable" must not have become "invisible".
  - STATE WHICH BRANCH OF E-03's `z8ex9f` FORK YOU TOOK (F-14), and prove it by measurement rather than assertion: paste whether `LaneInventory` carries a landing/unmerged reason code and whether `inventory_lane` accepts a branch parameter at execution HEAD, then say whether the fixture threads a branch. If `z8ex9f` HAS landed and this module was written without threading one, every case classifies `False` on the new blocking condition and two of the four asserted outcomes INVERT, so a green module in that state means the assertions were weakened rather than satisfied; that is a FAILED validation. Confirm also that `agent_workflows/lane_containment.py` is UNCHANGED by this plan (`git diff --stat` empty for it), since making the module pass by editing the gate is the inversion the execution gate forbids.
  - PLUS TWO MUTATION DEMONSTRATIONS, because one is not enough to prove the module is load-bearing in the direction that matters, and a test that passes under either mutation is NOT acceptable evidence for this item: (a) re-union `unknown_ignored` into `LaneInventory.unknown` and paste the FAILURE of the gitignored case; (b) remove `unknown_untracked` from it and paste the FAILURE of the untracked case. THE FAILING ASSERTION MUST BE ON `torn_down` OR WORKTREE EXISTENCE, NOT ON `reason_codes`, and this is measured rather than stylistic: at review, under mutation (a) the ignored case flips to `torn_down=False` while its `reason_codes` stays `()`, and under mutation (b) the untracked case flips to `torn_down=True` while its `reason_codes` stays `('unknown-untracked-file',)`. So a module asserting only reason codes is GREEN under both mutations. A pasted failure whose assertion is a reason code does not satisfy this item. Demonstration (b) is the data-loss direction and is the one this item most exists for. After EACH, revert and paste `git diff --stat agent_workflows/lane_containment.py` showing EMPTY, so it is provable that no production change was left behind.
  - BOTH MUTATIONS WERE MEASURED AT AUTHORING TO LEAVE THE CURRENT SUITE FULLY GREEN (`3246 passed, 2 skipped` in each case, F-05 and F-06), which is the baseline this item overturns: the same mutations must now fail this module while the REST of the suite still reports no new failure. INDEPENDENTLY REPRODUCED AT REVIEW at HEAD `84cdeb94`, so this is a confirmed defect and not an authoring artifact: mutation (a) `3353 passed, 2 skipped, 3 warnings in 74.05s` and mutation (b) `3353 passed, 2 skipped, 3 warnings in 78.66s`, both identical to the unmutated baseline, each reverted to an empty `git diff --stat`. Paste the bare suite summary after E-03 as well, and confirm the count ROSE by the number of new cases; an unchanged count means the module did not collect.
  - ALSO CONFIRM THE MODULE TESTS OUTCOMES, NOT STRUCTURE: state that it contains no `inspect`, `ast`, regex or substring read of production source, no symbol census, and no assertion on any docstring or comment text, per the 2026-09-26 ruling. A module that pins structure FAILS this item even with green output.
  - Observed evidence: PASS. Verified by 4 passing outcome tests, z8ex9f fork measurement, mutation (a) and (b) failures on torn_down, clean reverts, and bare suite 3813 pass.
    1. Narrowed test run with per-test names:
    ```text
    $ python3 -m pytest tests/test_lane_retention_amended_r55.py -o addopts="" -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=3423372247
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 4 items

    tests/test_lane_retention_amended_r55.py::test_merged_lane_holding_dirty_tracked_file_is_preserved PASSED [ 25%]
    tests/test_lane_retention_amended_r55.py::test_merged_lane_clean_is_torn_down PASSED [ 50%]
    tests/test_lane_retention_amended_r55.py::test_merged_lane_holding_untracked_file_is_preserved PASSED [ 75%]
    tests/test_lane_retention_amended_r55.py::test_merged_lane_holding_only_gitignored_file_is_torn_down PASSED [100%]

    ============================== 4 passed in 0.67s ===============================
    ```

    2. Four asserted outcomes verified:
       - gitignored-only (`test_merged_lane_holding_only_gitignored_file_is_torn_down`):
         `decision.torn_down is True`, `decision.inventory.reason_codes == ()`, `not lane_path.exists()`, and `decision.inventory.unknown_ignored == ("build/precious.txt",)` enumerated.
       - untracked (`test_merged_lane_holding_untracked_file_is_preserved`):
         `decision.torn_down is False`, `decision.inventory.reason_codes == ("unknown-untracked-file",)`, `lane_path.exists()`, `untracked_file.exists()`.
       - dirty tracked (`test_merged_lane_holding_dirty_tracked_file_is_preserved`):
         `decision.torn_down is False`, `decision.inventory.reason_codes == ("dirty-tracked-file",)`, `lane_path.exists()`.
       - clean (`test_merged_lane_clean_is_torn_down`):
         `decision.torn_down is True`, `decision.inventory.reason_codes == ()`, `not lane_path.exists()`.

    3. Fork measurement regarding `z8ex9f`:
       Measured at HEAD:
       ```text
       inventory_lane sig: (*, lane_root: 'Path | str', run_dir: 'Path | None' = None, item: 'dict[str, Any] | None' = None, attempt: 'int | None' = None, git_runner: 'Callable[[Path, list[str]], tuple[int, str, str]] | None' = None) -> 'LaneInventory'
       LaneInventory fields: ['as_dict', 'classified', 'count', 'dirty_tracked', 'discardable', 'failure', 'index', 'lane_root', 'readable', 'reason', 'reason_codes', 'submission_detail', 'uncollected_submission', 'unknown', 'unknown_ignored', 'unknown_untracked']
       ```
       `z8ex9f` has NOT landed: `inventory_lane` does not accept a `branch` parameter and `LaneInventory` does not carry a landing/unmerged reason code. The non-landed branch was taken; lanes are nevertheless merged into main so that threading a branch once `z8ex9f` lands satisfies its landing check. `agent_workflows/lane_containment.py` diff stat is empty (`git diff --stat` output empty).

    4. Two mutation demonstrations:
       (a) Re-union `unknown_ignored` into `LaneInventory.unknown` (`self.dirty_tracked + self.unknown_untracked + self.unknown_ignored`):
       ```text
       =================================== FAILURES ===================================
       __________ test_merged_lane_holding_only_gitignored_file_is_torn_down __________
       >       assert decision.torn_down is True
       E       AssertionError: assert False is True
       E        +  where False = LaneTeardownDecision(torn_down=False, ...).torn_down
       tests/test_lane_retention_amended_r55.py:123: AssertionError
       ========================= 1 failed, 3 passed in 0.79s ==========================
       ```
       Assertion failed on `decision.torn_down` (NOT reason_codes).
       Reverted cleanly; `git diff --stat agent_workflows/lane_containment.py` empty.

       (b) Remove `unknown_untracked` from `LaneInventory.unknown` (`return tuple(sorted(self.dirty_tracked))`):
       ```text
       =================================== FAILURES ===================================
       _____________ test_merged_lane_holding_untracked_file_is_preserved _____________
       >       assert decision.torn_down is False
       E       AssertionError: assert True is False
       E        +  where True = LaneTeardownDecision(torn_down=True, ...).torn_down
       tests/test_lane_retention_amended_r55.py:148: AssertionError
       ========================= 1 failed, 3 passed in 0.84s ==========================
       ```
       Assertion failed on `decision.torn_down` (NOT reason_codes).
       Reverted cleanly; `git diff --stat agent_workflows/lane_containment.py` empty.

    5. Bare suite count comparison:
       Baseline before E-03: `3809 passed, 2 skipped, 3 warnings in 78.42s (0:01:18)`.
       Bare suite after E-03: `3813 passed, 2 skipped, 3 warnings in 150.21s (0:02:30)`.
       Count rose by exactly 4 (3809 -> 3813) with 0 failures.

    6. Outcomes, not structure confirmed:
       `tests/test_lane_retention_amended_r55.py` drives real git worktrees and calls `lane_containment.teardown_lane_if_classified` directly. It contains no `inspect`, `ast`, regex, source-text parsing, symbol censuses, or assertions on comments/docstrings.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the new module's docstring pasted in full, with confirmation in your own words that it names all THREE limits: (1) that it guards the R5.5 CLASSIFICATION and NOT the interrupt-path decision order, citing `tests/test_oc_runipd.py::VerifierGateAndRunnerBugTests::test_discard_lane_reclaim` as the only surviving reclaim coverage and naming it as the operator-DISCARD branch rather than the merged branch; (2) that it drives `teardown_lane_if_classified` directly rather than through `reclaim_lanes_on_interrupt`, and what that means a regression could hide; (3) that the `uncollected-submission` workaround depends on a live question owned by backlog `nvymif`.
  - PROVE EVERY CITED ID6 AND NODE ID RESOLVES, since a docstring that points at nothing is worse than one that points at less: paste the resolved paths of BOTH `dwfmxz` and `nvymif` (via `aw find backlog <id6>`), with `dwfmxz` shown `- Status: open` so it is a live carrier rather than a closed one, and paste `python3 -m pytest tests/test_oc_runipd.py -o addopts="" --collect-only -q | grep discard_lane_reclaim` showing the cited node id exists. A dangling citation is a FAILED validation. PASTE `nvymif`'s ACTUAL STATUS AND ITS CARRIER, and do NOT require it to be `open`: measured at review it is `graduated` with `- Graduated-To: nvymif` pointing at pending plan `z8ex9f`, so the evidence must show that status and show `z8ex9f` resolving, and the docstring must cite the plan as the live carrier (F-14). A docstring still calling `nvymif` an open question is a FAILED validation, because it would send a reader to a closed item instead of to the plan that will change the behavior this module asserts.
  CITE THE FULL NODE ID INCLUDING ITS CLASS, and re-derive it rather than copying: measured at authoring it is `tests/test_oc_runipd.py::VerifierGateAndRunnerBugTests::test_discard_lane_reclaim`, and the class name is NOT guessable from the test name (this plan's first draft guessed `LaneReclaimTests` and was wrong). A bare `file::function` id for a test that lives in a class does not resolve, so a docstring carrying one is a dangling citation and FAILS this item.
  - CONFIRM NO SECOND ITEM WAS FILED: paste `aw find backlog` output (or a directory listing) showing exactly ONE open item for the decision-order gap. `dwfmxz` was filed at authoring, so an `aw backlog new` invocation appearing in this item's evidence is a FAILED validation: it would split the defect's history across two items. Also confirm `dwfmxz` is still `- Work-Kind: chore` with no `- Blocks-Release:`, or, if the executor measured a user-perceptible impact that makes it a `bug`, that the gate was set through `aw backlog set` and the measurement is stated.
  - Observed evidence: PASS. Verified by full docstring inspection, 3 limits confirmed, dwfmxz/nvymif/test node id resolution proofs, and no second backlog item filed.
    1. Full module docstring from `tests/test_lane_retention_amended_r55.py`:
    ```python
    """Behavioral outcome tests for the amended spec 7ckptx R5.5 lane retention gate.

    This module restores the outcome-level guard on the amended spec 7ckptx R5.5 classification,
    which was left unguarded when commit 19313eed deleted tests/test_lane_retention.py and
    tests/test_worktree_lease_merged_reclaim.py. It verifies by outcome that an interrupted or
    merged lane holding only gitignored files is torn down as disposable while untracked and dirty
    tracked content are preserved.

    Honest limits of this guard (plan hyuos6 E-04):
    1. CLASSIFICATION ONLY, NOT DECISION ORDER: This module guards the R5.5 classification logic
       inside `lane_containment.teardown_lane_if_classified` only, and specifically does NOT guard
       the interrupt-path decision order delivered by plan 65cuw0 E-03 (consulting merged-ness
       before bailing out on holds_work). The only surviving coverage referencing
       `reclaim_lanes_on_interrupt` is the operator-discard test at
       `tests/test_oc_runipd.py::VerifierGateAndRunnerBugTests::test_discard_lane_reclaim`,
       which exercises the discard branch rather than merged-lane reclaim. The merged-lane reclaim
       decision-order guard was owned by backlog item `dwfmxz` (chore, filed at authoring), which
       has since graduated to pending plan `2rtp96` (`.aw/records/plans/pending/20260930-dwfmxz-01-2rtp96-guard-the-interrupt-path-merged-lane-reclaim-decision-order.ipd.md`).
    2. DRIVES GATE DIRECTLY: Tests here drive `lane_containment.teardown_lane_if_classified`
       directly rather than through runner_shared / driver `reclaim_lanes_on_interrupt`. A regression
       that breaks how the runner reaches or invokes the gate would not fail this module.
    3. COMPLETE RECEIPT WORKAROUND AND PENDING PLAN z8ex9f: An absent collection receipt causes
       `submission_retention` to report `uncollected=True`, which would mask retention checks under
       `('uncollected-submission',)`. This module supplies a complete collection receipt in each case
       to test classification in isolation. The question of whether an absent receipt should block an
       interrupted lane that provably wrote nothing was owned by backlog item `nvymif`, which
       graduated on 2026-09-30 to pending plan `z8ex9f` (`.aw/records/plans/pending/20260930-nvymif-01-z8ex9f-distinguish-a-lane-that-provably-submitted-nothing-from-one.ipd.md`).
       Plan z8ex9f declares `agent_workflows/lane_containment.py` in scope, narrows
       `submission_retention`, and adds a landing condition whose absent-branch case blocks.
       At the time plan hyuos6 executes, z8ex9f has not landed (`inventory_lane` does not accept a
       branch parameter). The lanes here are nevertheless fully merged into main so that threading a
       branch will satisfy the landing check once z8ex9f lands.
    """
    ```

    2. Three limits confirmed in own words:
       - Limit 1 (Classification only, not decision order): The module guards the R5.5 classification predicate in `lane_containment.teardown_lane_if_classified`, but does not guard the interrupt-path decision order in `runner_shared.reclaim_lanes_on_interrupt` (which checks merged-ness before `holds_work` bails out). The only surviving reclaim coverage is `tests/test_oc_runipd.py::VerifierGateAndRunnerBugTests::test_discard_lane_reclaim`, which drives the operator-discard branch rather than merged-lane reclaim. The carrier for this gap is `dwfmxz` (now graduated to pending plan `2rtp96`).
       - Limit 2 (Drives gate directly): The tests invoke `lane_containment.teardown_lane_if_classified` directly rather than through runner/driver callers (`reclaim_lanes_on_interrupt`). Regressions in runner-level gate integration or dispatch would not be surfaced by this module.
       - Limit 3 (Complete receipt workaround & pending plan z8ex9f): An absent collection receipt causes `submission_retention` to flag `uncollected=True` (`uncollected-submission`), masking classification. This module works around that by injecting a complete collection receipt in each test case. This receipt-checking behavior was owned by backlog item `nvymif`, which graduated on 2026-09-30 to pending plan `z8ex9f` (`z8ex9f` narrows `submission_retention` and adds a landing condition).

    3. Citations resolution proof:
       - `aw find backlog dwfmxz`:
         ```text
         ●  graduated     dwfmxz  .aw/records/backlog/graduated/20260929-dwfmxz-01-dwfmxz-reclaim-decision-order-unguarded.backlog.md
         ```
         (Note: `dwfmxz` was open at plan authoring and graduated on 2026-09-30 to pending plan `2rtp96` via run `run-20260930T053024Z-3198670`).
       - `aw find plans 2rtp96`:
         ```text
         ◕  pending       2rtp96  dwfmxz          .aw/records/plans/pending/20260930-dwfmxz-01-2rtp96-guard-the-interrupt-path-merged-lane-reclaim-decision-order.ipd.md
         ```
       - `aw find backlog nvymif`:
         ```text
         ●  graduated     nvymif  .aw/records/backlog/graduated/20260922-nvymif-01-nvymif-r55-gate-refuses-every-interrupted-lane.backlog.md
         ```
         Status is `graduated`, graduated on 2026-09-30 to pending plan `z8ex9f`.
       - `aw find plans z8ex9f`:
         ```text
         ◕  pending       z8ex9f  nvymif          .aw/records/plans/pending/20260930-nvymif-01-z8ex9f-distinguish-a-lane-that-provably-submitted-nothing-from-one.ipd.md
         ```
       - Pytest collection for discard_lane_reclaim:
         ```text
         $ python3 -m pytest tests/test_oc_runipd.py -o addopts="" --collect-only -q | grep discard_lane_reclaim
         tests/test_oc_runipd.py::VerifierGateAndRunnerBugTests::test_discard_lane_reclaim
         ```
         Node id resolves to class `VerifierGateAndRunnerBugTests` and method `test_discard_lane_reclaim`.

    4. Confirmation no second item filed:
       - No `aw backlog new` was invoked during execution.
       - A search across `.aw/records/backlog/` for the reclaim decision-order gap shows only `dwfmxz`:
         `.aw/records/backlog/graduated/20260929-dwfmxz-01-dwfmxz-reclaim-decision-order-unguarded.backlog.md`.
       - `dwfmxz` metadata confirmed:
         ```yaml
         - Id: dwfmxz
         - Status: graduated
         - Graduated-To: dwfmxz
         - Set: dwfmxz
         - Priority: medium
         - Work-Kind: chore
         ```
         `- Work-Kind:` is `chore`; `- Blocks-Release:` is absent.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (4 E-items in 2 task groups, under the 18-leaf / 5-group thresholds). The two groups are one concern: a stale requirement in a durable record, and the missing test guard the same investigation exposed for the very rule that requirement got wrong.

EXECUTION CONTRACT. Commit ONLY the paths in `- Scope-Paths:`, through `aw commit <this plan> -- <paths>`; never `git add -A`, `-a`, or bare `git add`; never push; never `--no-verify`. Task group 1 and task group 2 are independently committable and SHOULD be separate commits: one is a records correction, the other is a new test module.

RESOLVED OPEN QUESTIONS: all three are `Status: resolved` and non-blocking, each answered from repository evidence with the basis cited in its rationale. Nothing here waits on a human decision.

THE ONE THING MOST LIKELY TO GO WRONG, stated so the executor does not do it by reflex: E-01 edits a file inside `.aw/records/plans/executed/`, and the reflex when a pre-commit gate refuses such an edit is `--no-verify`. Do not. A refusal means the append route `AGENTS.md` sanctions does not work, which is a finding worth more than this plan's note; STOP and report it to a human. REASSURANCE, so that caution is not read as a live worry: the route was exercised end to end at authoring and both gates exited 0 with `numstat` reading `1 0`, then the probe was fully reverted (F-12). A refusal would be genuinely surprising and genuinely worth escalating.

THE SECOND THING MOST LIKELY TO GO WRONG IS FIXING THE WRONG THING. Do NOT edit `65cuw0`'s E-04 or V-03 to remove the contradiction, do NOT touch either of V-03's evidence blocks, and do NOT amend spec `7ckptx` R5.5 or A15. The spec amendment is the settled maintainer ruling this plan is reconciling the record TO, not a defect to reverse; re-forking it would re-create a measured production failure (OQ-01) and would break the shipped behavior E-03 is adding a guard for, in the same change. If E-03's mutation demonstrations tempt you to "fix" the production code so a test passes, you have inverted the plan: the mutations are expected to FAIL the new tests and must be reverted.

THE THIRD IS A VACUOUS GUARD. E-03 without a real collection receipt passes all four cases for the wrong reason and would go green under BOTH mutations (F-04). V-03 requires the two mutation demonstrations precisely so this cannot pass unnoticed. A green module with no pasted mutation failures does not satisfy V-03.

SCOPE FENCE, AS A DECLARATION. The three `- Scope-Paths:` entries are the reconciliation surface, not a tripwire: an edit outside them is to be MADE AND THEN JUSTIFIED, since `aw ipd finalize` requires a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path. E-04's backlog filing is the one foreseeable out-of-scope write and is named in the Scope check. The STOP directives above are deliberately narrow and are NOT scope questions: stop if a pre-commit gate refuses the sanctioned append, and stop if any item appears to require narrowing R5.5.

NO SPEC EDIT IS DECLARED. `- Scope-Paths:` contains no `.spec.md` path, so the runners will announce none and the finalize scope gate will reconcile against that. A spec edit appearing in this plan's diff is a scope violation to be explained, not a silent improvement.

SHARED CHECKOUT. Other agents may be working concurrently, and this plan edits a file under `.aw/records/plans/executed/`, one under `.aw/records/reviews/`, and adds one test file. Before every commit run `git diff --cached --name-only` and confirm every path is one this plan changed; unstage anything else path by path with `git restore --staged <path>`, never a bare `git reset` or `git stash`. Re-verify after ANY failed commit attempt, because a rejecting hook can leave unstaged paths in the index - which matters more than usual here, since the two gates this plan runs are exactly the hooks that might reject.

NO RELEASE GATE, AND ITS ABSENCE IS DELIBERATE. Backlog `0kdwm3` carries no `- Blocks-Release:` and is `- Work-Kind: followup`, so this plan inherits none and inventing one is forbidden. Note honestly that F-06 (the unguarded data-loss direction) is the kind of finding that could justify one; it is NOT claimed here because no user-perceptible defect exists today (the behavior is correct, only its guard is missing), and the repository's test for `bug` is user-perceptible impact rather than latent risk. A reviewer who disagrees should say so: this is a judgement, and the measurement supporting it is in F-05 and F-06 rather than in a vibe.

HONESTY RULE, HARD MUST. When you report tests passed, paste the ACTUAL runner output; never claim a success you did not run. The authored baseline is `3246 passed, 2 skipped, 3 warnings in 52.88s` at HEAD `9733d47a`, measured bare in this lane with zero failures.

WHAT THE HUMAN IS APPROVING, in four items. (1) An APPEND-ONLY hand edit to one file in `.aw/records/plans/executed/`, verified at authoring to pass both shipped gates. (2) An APPENDED `## Round 4` on one review record, leaving its earlier rounds and its verdict intact. (3) ONE NEW TEST FILE restoring an outcome-level guard on a retention rule that is currently green under mutation in both directions. (4) NO production code change, NO spec change, NO change to any executed plan's recorded steps, evidence, results or status, and NO restoration of any structure-pinning test.

POST-GATE LIFECYCLE MOVE (not an `E-*` item): after every `E-*` is performed and every `V-*` is verified with pasted evidence, and `aw ipd lint --phase pre-transition` conforms with zero findings, the terminal transition is a post-gate transaction performed through `aw ipd finalize` (the runner owns begin/finalize for a managed lane; a worker-role process must not run them).
