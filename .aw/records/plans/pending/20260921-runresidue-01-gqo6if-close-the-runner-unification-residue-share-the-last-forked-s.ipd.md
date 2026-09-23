# IPD: Close the runner unification residue: share the last forked symbols or record each as genuinely host-specific

- Date: 2026-09-21
- Kind: child
- Concern: The `rununify` Set substantially met the maintainer's 2026-09-16 directive ("at the end of the SET, there should be one code base shared by the two runners that contains 100% of the otherwise redundant code that currently is duplicated between the two runners") but did not fully meet it, and its orchestrator is about to retire. THE SHAPE OF THE RESIDUE IS THE LOAD-BEARING CLAIM AND IT REPRODUCES; THE ABSOLUTE COUNTS DO NOT, so they are stated as what they are. Re-measured independently at review 2026-09-22, both at this plan's own cited HEAD `f763be8c` and at review HEAD, by classifying each co-defined symbol's BODY with `ast.unparse`: 58 symbols are defined in BOTH `oc_runipd` and `agy_runipd` (57 functions plus the class `StallWatchdog`, which the authored "57" excluded without saying so), 32 have BOTH sides calling into `runner_shared` somewhere, and ONE has one side doing so (not 5). THE RESIDUE IS A RANGE because two defensible tests disagree, and THAT DISAGREEMENT IS THE FINDING this plan exists to resolve per symbol rather than by threshold: under a STRICT test (neither side calls ANY `runner_shared` symbol anywhere in its body) it is 25 symbols / 444 agy `ast.unparse` lines at `f763be8c` and 23 / 391 at review HEAD; under a LOOSE test (neither side is a single-statement delegation) it is 37 / 1103 and 36 / 1122. The authored figures (7 / 170 strict, 20 / 667 loose) reproduce under NEITHER test at EITHER commit and are superseded; what DID reproduce is the structure (strict is a strict subset of loose, with 12 to 13 symbols between them). E-01 exists precisely so the next reader re-derives these rather than trusting any of them. ONE CASE IS UNAMBIGUOUS AND IS THE ANCHOR: `reclaim_lanes_on_interrupt` is identical in length on both sides at 0.998 similarity after host-token normalisation (98 `ast.unparse` lines each at review HEAD, 68 each at `f763be8c`; the authored "174 lines" matches neither metric, the raw source span being 252), i.e. copied code rather than a host difference.
- Scope: Per symbol in the residue, either SHARE it (one implementation in `runner_shared`, host-shaped shell on each side) or RECORD IT AS GENUINELY HOST-SPECIFIC against the maintainer's own test ("one host does A, the other NOT A") with the evidence. IN: every symbol E-01's committed scanner puts in the STRICT class, which are unambiguous; every symbol it puts BETWEEN strict and loose, each decided and recorded; and `reclaim_lanes_on_interrupt`, which the strict test misses only because both copies call shared helpers while remaining near-identical to each other. THE MEMBERSHIP IS WHATEVER THE SCANNER REPORTS AT EXECUTION HEAD, not a count fixed here: the authored "7 strict / 13 between" did not reproduce (review measured 23 to 25 strict and 12 to 13 between), and a plan whose scope is pinned to a stale count either under-covers the residue or reports false completion. OUT: re-doing any of the 11 executed `rununify` children's work, changing the five large host-shaped functions the Set always expected as residue (`run_queue`, `main`, `build_parser` and their kin already delegate), and any behavior change at all - this is extraction, so a behavior difference found mid-flight is a finding to report, not a thing to fix here.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, agent_workflows/runner_shutdown.py, tests/test_runner_shared.py, tests/test_runner_refork_guard.py, tests/test_rununify_characterization.py, .aw/records/research
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: runresidue
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: gqo6if
- Approval: 2026-09-23, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-23 approved (aw set): status set to approved
- 2026-09-22 reviewed (aw set): plan-review complete: APPROVE WITH REVISIONS APPLIED; 7 findings, all FIXED; E-04 split into four cluster items; readiness go-pending-approval; typed review record under .aw/records/reviews/

- 2026-09-22 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006, all FIXED. Reviewed at HEAD `64c452fb`; `aw ipd lint --phase author` conforming before and `--phase review-finalize` conforming after, but `aw check` reported TWO error-severity findings the IPD linter does not see, both now cleared. THE PLAN'S PURPOSE IS RIGHT AND ITS ANCHOR IS SOLID: `reclaim_lanes_on_interrupt` really is copied code, re-verified at 0.998 normalised similarity with IDENTICAL length on both sides at both commits, so E-03 has a genuine subject; the maintainer's "one host does A, the other NOT A" test is quoted accurately from `rununify`'s records; spec `c4gd2h` R19 says what F-06 claims; all 11 `rununify` children are `executed`; and the strict-subset-of-loose STRUCTURE that motivates a per-symbol decision reproduces exactly. SIX DEFECTS FOUND, TWO OF THEM CAPABLE OF SENDING AN EXECUTOR BACKWARDS. (PR-003, BLOCKER) E-05 prescribed extending `tests/test_rununify_characterization.py`, but NO `tests/*characterization*` FILE EXISTS: `d4dd6b88` (2026-09-18) "retire change-detector tests over code text and prose" deleted `test_wtiso_characterization.py` and `7ebc2964` deleted four `test_rununify_*_characterization.py` files (~3,900 lines) removing exactly the source-text/similarity/AST pins this item's form implies, so following it would revert a four-day-old maintainer decision. (PR-005, BLOCKER) "re-base any guard that pins it as forked" cannot be done as written: `tests/test_runner_refork_guard.py` rows require the runner to have NO top-level definition of the symbol AND to expose the OWNER'S OBJECT via `assertIs`, which no "thin host-shaped shell" can satisfy - measured, `oc_runipd.integrate_lane_branch is runner_shared.integrate_lane_branch` is already False and that symbol is correctly absent from the table. (PR-002) E-04 named TWO ALREADY-UNIFIED symbols as lift targets: `reconcile_interrupted` is a two-line byte-identical delegation on both sides (similarity 1.000) and `driver_finalize` calls `runner_shared` on both sides. (PR-001) EVERY HEADLINE COUNT IS UNREPRODUCIBLE AT THE PLAN'S OWN CITED HEAD: authored 57 symbols / 5 one-side / 7-strict-170-lines / 20-loose-667-lines, measured at `f763be8c` 58 / 1 / 25-444 / 37-1103 and at review HEAD 23-391 / 36-1122; the anchor's "174 lines each" is 98 by `ast.unparse` and 252 by raw span; `run_queue`'s "456 lines / 10 calls" is 161 lines and 8 calls. The 57 silently excluded the class `StallWatchdog`. (PR-004) E-05 planned to extend a file `40it5e` owns and has not created, with `Item-Dependencies: none`, racing that plan. (PR-006) all four Deferred rows named no durable carrier. (PR-007) E-04 bundled 18 symbols across FOUR unrelated clusters with four independent test surfaces, which the linter's `IPD-Z602` density advisory flagged; it is SPLIT into E-04 (low-risk remainder), E-06 (lock/base, which owns `c4gd2h` R2's observable `driver.lock` release), E-07 (`set_plan_approved` alone, because it writes PERMANENT workflow history through a per-host actor the `hostdedup` Set already measured as a misattribution hazard) and E-08 (stop/signal last, being both the riskiest and the LEAST similar cluster at 0.493 to 0.895), ordered least-risky-first, with matching V-06/V-07/V-08 and the watermark advanced to 08. Also cleared: a `check.lifecycle-transition-invalid` error caused by the history lines being ordered `draft` above `to-review` in a newest-first section.
- 2026-09-21 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored at the maintainer's explicit direction of 2026-09-22, given through `/askme` when they resolved `rununify`'s orchestrator question: "Mark it done, file the rest as new work ... BUT Write the plan NOW. Don't wait." So this plan exists BEFORE that orchestrator retires, which removes the one risk their chosen option rested on - that a deferred follow-up never gets filed. It carries `- From-Plan-Verdict: 40it5e` in spirit: `40it5e` E-04 is the item that must name this Set as the carrier of the residue.
- 2026-09-21 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Finish what the directive asked for, or state precisely and with evidence why the remainder cannot be
finished. Either outcome is acceptable; an unexamined remainder is not. The deliverable is that after this
plan, every symbol still defined in both runners is either ONE implementation with two host shells, or
carries a recorded per-symbol justification a reader can check against the maintainer's own test.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure, then decide per symbol

- [x] E-01 COMMIT THE SCANNER, so every figure in this plan is reproducible and the next reader is not taking a number on trust. The `rununify` Set's own PR-006 records that its original baseline came from an ad-hoc scan that no longer exists, which is precisely why its headline figure could not be re-derived and why one measurement in this area has already been quoted wrongly. So: commit a scanner that takes both runner modules, classifies each shared top-level symbol as BOTH-DELEGATE / ONE-SIDE-DELEGATES / NEITHER-DELEGATES, reports the strict and loose counts SEPARATELY with the test each uses stated in its own output, and prints a per-symbol table with line counts and a host-token-normalised similarity. It must be runnable by a reader with one command.
  - Depends on: none
  - Expected outcome: a committed scanner plus its pasted output at execution HEAD, reporting both the strict count and the loose count and naming which test produced each. A single number without its test named FAILS this item.
  - Execution state: performed

- [x] E-02 DECIDE EVERY RESIDUE SYMBOL AGAINST THE MAINTAINER'S OWN TEST, per symbol, and immortalize the table. The test is theirs and is quoted in `rununify`'s own child-breakdown note: `oc_runipd` is the preferred version "unless a difference is a real capability (one host does A, the other NOT A)". Apply exactly that. For each symbol record: the two line counts, the normalised similarity, the decision (SHARE or HOST-SPECIFIC), and for HOST-SPECIFIC the capability difference in one sentence naming what one host does that the other does not. A similarity figure is NOT a decision - `_record_forced_stop` at 0.683 may be a real capability difference while `_lane_reclaim_prompt` at 0.967 may be pure duplication - so do not let the number decide for you.
  - Depends on: E-01
  - Expected outcome: a research artifact created with `aw research new` (never hand-named) holding the per-symbol table for every residue symbol, with a SHARE/HOST-SPECIFIC decision and, for each HOST-SPECIFIC, the capability sentence. The counts must reconcile with E-01's output.
  - Execution state: performed

### Task group 2: share what should be shared

- [x] E-03 SHARE `reclaim_lanes_on_interrupt` FIRST, because it is the unambiguous case and it de-risks the rest. Identical length on both sides at 0.998 similarity after host-token normalisation (re-verified at review: 98 `ast.unparse` lines each at review HEAD, 68 each at `f763be8c`; the authored "174" matches neither metric, so state YOUR metric when you re-measure). This is copied code, not a host difference, and it is the single largest true duplication in the residue. Lift it to ONE implementation in `runner_shared` with whatever host-specific values it needs injected (follow the `HostLabels` precedent the `hostdedup` Set established rather than inventing a second mechanism), leave a thin host-shaped shell on each side, and re-base any guard that pins it as forked. PURE MOVE, NO BEHAVIOR CHANGE.
  - Depends on: E-02
  - KNOW WHAT `tests/test_runner_refork_guard.py` ACTUALLY ASSERTS BEFORE ADDING A ROW TO IT, because its contract is INCOMPATIBLE with the "thin host-shaped shell" design this item and E-04 choose (PR-005). Read at review: for every `(symbol, owner)` row in `REFORK_TABLE` each listed runner must (1) NOT contain a TOP-LEVEL DEFINITION of that symbol, checked by AST, and (2) expose the OWNER'S OBJECT at that attribute name, checked with `assertIs`. A host shell is a top-level definition and is NOT the owner's object, so adding a row for a shell-bound symbol fails BOTH halves; measured, `oc_runipd.integrate_lane_branch is runner_shared.integrate_lane_branch` is already False for exactly that reason, and that symbol is correctly NOT in the table. THE GUARD IS FOR RE-EXPORTS, NOT WRAPPERS. So: add a row ONLY for a symbol you bound as a bare re-export, and for a shell-bound symbol pin the delegation instead (the form `tests/test_runner_shared.py` already uses for the integration wrappers). Baseline `17 passed` at review; do not weaken an assertion to make a shell fit.
  - Expected outcome: one implementation, two shells, the relevant suites green with their invocation stated, and the scanner from E-01 showing this symbol moved out of the NEITHER-DELEGATES class. Plus a statement of which guard form was used and why it matches the binding shipped.
  - Execution state: performed

SPLIT AT REVIEW (PR-007). The authored E-04 was ONE item covering 18 symbols across FOUR unrelated clusters
with four independent test surfaces, which is exactly what the right-sizing rule forbids and what the linter's
`IPD-Z602` density advisory flagged. It is now four items, ordered least-risky first so the riskiest cluster
runs last against the most evidence. TWO RULES GOVERN ALL FOUR.

FIRST, THE MEMBERSHIP LISTS BELOW ARE ILLUSTRATIVE, NOT AUTHORITATIVE. E-02's recorded table decides
SHARE-versus-HOST-SPECIFIC, and E-01's scanner decides what is in the residue at execution HEAD. Any symbol
named below that the scanner reports as already delegating must be SKIPPED and NAMED as skipped, not lifted;
any residue symbol the scanner finds that these lists omit must be DECIDED by E-02 rather than silently
dropped. Review found BOTH error directions present, which is why this is stated rather than assumed.

SECOND, TWO NAMES WERE REMOVED FROM THE AUTHORED LISTS BECAUSE THEY ARE ALREADY UNIFIED (PR-002). Measured:
`reconcile_interrupted` is a TWO-LINE body on BOTH sides, byte-identical, reading
`runner_shared.reconcile_interrupted(run_dir, state, save_state=save_state)` - the sanctioned delegation shape,
similarity 1.000. `driver_finalize` calls `runner_shared` on BOTH sides too (23/22 lines, similarity 0.720),
so it is a PARTIALLY shared symbol whose remaining per-host body is a judgement call for E-02, NOT an unshared
fork. `reconcile_interrupted` must not re-enter; `driver_finalize` may, but only via E-02's recorded decision.

- [x] E-04 SHARE THE LOW-RISK REMAINDER CLUSTER, the symbols with no signal, lock or lifecycle role: `_lane_reclaim_prompt` (0.974), `_escalation_recorder` (0.760), `_budget_breach_recorder` (0.867), `_add_output_mode_flags` (0.921), `build_isolation_notice` (0.295), `disable_lane_prompt` (1.000). FIRST BECAUSE IT IS SAFEST: these are prompt text, recorders and flag registration, so a mistake is visible immediately and cannot strand a run. Note `build_isolation_notice` at 0.295 is the LEAST similar symbol in the whole residue and is the likeliest genuine host difference in this group; if E-02 recorded it HOST-SPECIFIC, skip it here and say so.
  - Depends on: E-03
  - Expected outcome: each `SHARE` symbol in this cluster has one implementation and two shells; each skipped symbol named with E-02's decision; the scanner re-run showing this cluster's members gone from NEITHER-DELEGATES.
  - Execution state: performed

- [x] E-06 SHARE THE LOCK AND BASE CLUSTER: `run_lock` (0.736), `locked_run` (0.689), `evaluate_clean_base_for_launch` (0.583). SEPARATE FROM THE REST BECAUSE `run_lock` OWNS A SHIPPED CONTRACT: spec `c4gd2h` R2 requires the `driver.lock` release to be OBSERVABLE (drop the `flock` AND remove the file), the two copies already differ (41 vs 34 lines), and `runner_shutdown.RunLockHandle` participates in that release. A regression here strands a lock and makes the repository look permanently busy. Do NOT alter the acquisition/release semantics while moving them; if unifying would change WHEN the file is removed or WHEN the flock drops, that is a behavior change and OQ-02 applies.
  - Depends on: E-04
  - Expected outcome: one implementation per `SHARE` symbol; explicit confirmation that the `c4gd2h` R2 observable-release behavior is unchanged, with the evidence; any symbol left forked named with its reason.
  - Execution state: performed

- [x] E-07 DECIDE AND, IF SHARED, LIFT `set_plan_approved`, ALONE, because it writes DURABLE HISTORY and the two copies are the second-least similar pair in the residue (33 vs 19 lines, similarity 0.521). It records an approval into a plan's permanent `## Workflow history` through an `--actor` value that DIFFERS PER HOST, which the `hostdedup` Set already measured as a misattribution hazard: a verbatim lift would attribute every agy auto-approval to the oc command. So the host value MUST arrive through the descriptor (`HostLabels`) with NO default, and the attribution must be pinned in BOTH directions by test. If that cannot be done without changing what lands in history, leave it forked and record why.
  - Depends on: E-04
  - Expected outcome: either one implementation with the actor injected and a both-directions attribution test pasted, or a recorded HOST-SPECIFIC decision with the capability sentence. A lift with no attribution test FAILS.
  - Execution state: performed

- [x] E-08 SHARE THE STOP AND SIGNAL CLUSTER LAST: `_record_forced_stop` (0.693), `_record_checkpoint_stop` (0.865), `_record_deliberate_stop` (0.770), `_observe_between_turn_stop` (0.679), `install_stop_triggers` (0.493), `handle_stop_command` (0.895), `terminate_process` (0.697), `requeue_interrupted` (0.653). LAST AND ALONE BECAUSE IT IS THE RISKIEST GROUP BY BOTH MEASURES: it is the code that runs when an operator interrupts a run, so a regression is discovered at the worst possible moment, and it is the LEAST similar cluster measured, so it is the most likely to contain a real capability difference rather than duplication. Spec `c4gd2h` R19 governs what a stopped item may do (verified at review: a later run MUST refuse to blindly resume an `unknown_outcome` item), so a unification that changes what is recorded at stop time is a spec question, not an extraction. `install_stop_triggers` at 0.493 is the single most divergent member and should be decided before the others in the cluster are moved.
  - Depends on: E-06, E-07
  - Expected outcome: every `SHARE` member has one implementation; every member left forked is named with its capability sentence; the `c4gd2h` R19 behavior is shown unchanged; and the scanner shows the NEITHER-DELEGATES class reduced to EXACTLY the HOST-SPECIFIC set E-02 recorded.
  - Execution state: performed

- [x] E-05 PROVE NO BEHAVIOR CHANGED, on the terms `rununify` itself established, PINNING OBSERVABLE BEHAVIOR ONLY. The suites are asymmetric, so "both suites green" is NOT sufficient evidence for an agy-side change, which is the precise reason that Set called for a characterization baseline. Pin the CURRENT observable behavior of both hosts for every symbol this plan touches, BEFORE touching it, and show the pinned tests still pass afterwards. Then run the suite per the SUITE RULE below.
  - Depends on: E-04, E-06, E-07, E-08
  - THIS REPOSITORY DELIBERATELY RETIRED CHANGE-DETECTOR CHARACTERIZATION TESTS FOUR DAYS BEFORE THIS PLAN WAS AUTHORED, and re-creating that form under a new name would revert a maintainer decision (PR-003). Measured at review: `tests/test_rununify_characterization.py` DOES NOT EXIST, and neither does any `tests/*characterization*` file at all. Commit `d4dd6b88` (2026-09-18) "test: retire change-detector tests over code text and prose" deleted `tests/test_wtiso_characterization.py` (192 lines) and `7ebc2964` before it deleted four `test_rununify_*_characterization.py` files totalling roughly 3,900 lines, eliminating source-text pins (`len(getsourcelines(...))`, `SequenceMatcher` ratios, AST censuses). SO: assert BEHAVIOR THROUGH THE PUBLIC SEAM (call the symbol, observe its effect, its return value, its written state, its emitted events) and assert NOTHING about source text, line counts, similarity ratios, or AST shape. A test containing a source-text or line-count assertion FAILS this item even if it passes, which is the same bar `40it5e` E-03 was given at its own review. Follow the LIVE precedent (`tests/test_rununify_run_queue.py` and its kin) rather than the deleted one.
  - WRITE THE PINS WHERE THEY BELONG RATHER THAN IN A FILE THIS PLAN DOES NOT OWN (PR-004). `tests/test_rununify_characterization.py` is `40it5e` E-03's deliverable, and `40it5e` is `Status: reviewed`, NOT executed, so at this plan's execution time the file may not exist. The authored "create it if that plan has not executed" produces a RACE: two plans creating and extending the same new file, with this plan carrying `Item-Dependencies: none`, so the runner's dependency-depth sort cannot order them (`40it5e` F-08 records this same undeclared edge from the other side). PREFER the existing per-symbol behavioral suites named in `Scope-Paths` (`tests/test_runner_shared.py` and the cluster's own files); if a NEW file is genuinely needed, give it a name this plan owns and say so, and do NOT reach into `40it5e`'s file.
  - THE SUITE RULE: the gate is NO NEW failing node ids against a baseline taken THE SAME WAY in the same session, never an absolute green. Measured at review HEAD in this lane, a bare `python3 -m pytest` is `2 failed, 8521 passed, 3 skipped, 2 xfailed`, and BOTH failures are unrelated to this plan (`tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`, an ambient `OPENCODE_CONFIG_CONTENT` leak that is `76 passed` under `env -u OPENCODE_CONFIG_CONTENT`; and `tests/test_orchestrator_retirement.py::RealRepositorySets`, unrelated corpus drift). Classify every failure pre-existing or attributable; do NOT edit either test to reach green.
  - Expected outcome: behavioral pins written BEFORE each change and passing after, named per symbol, in a file this plan owns; the file shown to contain NO source-text/line-count/similarity assertion; plus the suite summary with every failure classified pre-existing or attributable.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- THE MAINTAINER'S TEST FOR A LEGITIMATE HOST DIFFERENCE is "one host does A, the other NOT A", recorded in `rununify`'s child-breakdown note together with the ruling that `oc_runipd` is the preferred version otherwise. This plan applies that test rather than inventing a similarity threshold.
- `HostLabels` IS THE ESTABLISHED MECHANISM for expressing a real per-host difference behind one implementation (the `hostdedup` Set). Do not invent a second one.
- SOURCE-READING TESTS ARE WORK, NOT VETOES (`rununify`'s supporting ruling of 2026-09-16): many test files assert on the SHAPE of source, so a test pinning a duplication is a thing to update, not a reason to abandon a unification. BUT UPDATING A GUARD IS NOT THE SAME AS FITTING AN INCOMPATIBLE ONE: `tests/test_runner_refork_guard.py` rows require no top-level definition PLUS the owner's own object, which no host shell can satisfy, so a shell-bound symbol needs a DELEGATION pin rather than a row (F-08). Re-base deliberately; never weaken an assertion to make a shell pass.
- SOURCE-TEXT ASSERTIONS ARE THEMSELVES BEING RETIRED, and the two rulings above must not be confused. Commits `d4dd6b88` and `7ebc2964` (2026-09-18) deleted every `*_characterization.py` file and the source-text pins inside them (`len(getsourcelines(...))`, `SequenceMatcher` ratios, AST censuses) as change detectors. So a STRUCTURAL guard over already-extracted symbols is sanctioned, while a new test that pins source TEXT or line counts is not. E-05 pins observable behavior only (F-07).
- SYMBOL COUNTS OVER LINE COUNTS, per `rununify`'s Goal: its symbol figures reproduced at review while its line figures did not. AND EVEN A SYMBOL COUNT IS A DATED MEASUREMENT: this plan's counts did not reproduce at its own cited HEAD, and the strict residue moved 25 -> 23 between `f763be8c` and review HEAD. Re-derive at execution time; never quote a count from a plan document as current.
- A "LINE COUNT" IS MEANINGLESS WITHOUT ITS METRIC. Measured on one symbol at review: `reclaim_lanes_on_interrupt` is 98 lines by `ast.unparse` and 252 by raw source span, and `run_queue` is 161 versus 456. Differences of that size are why this plan's line figures could not be matched to any test. State the metric beside every figure.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH | AST body-classification, re-measured at review at BOTH `f763be8c` and review HEAD | 58 symbols are defined in both runners (57 functions plus the class `StallWatchdog`), 32 have BOTH sides calling `runner_shared`, and ONE has one side doing so. So the `rununify` Set substantially SUCCEEDED, and any report of its outcome that counts those 32 as duplication is wrong. CORRECTED AT REVIEW: the authored "57 symbols ... 5 have one side delegating" was 58 and 1; the 57 silently excluded `StallWatchdog`, which the plan's own residue lists then also omit. |
| F-02 | HIGH | strict vs loose classification at both commits | THE RANGE IS THE FINDING AND IT HOLDS; THE NUMBERS IN IT WERE WRONG. Strict (neither side calls any shared symbol): 25 symbols / 444 agy `ast.unparse` lines at `f763be8c`, 23 / 391 at review HEAD. Loose (neither side is a single-statement delegation): 37 / 1103 and 36 / 1122. The authored 7/170 and 20/667 reproduce under NEITHER test at EITHER commit. What DID reproduce is the structure: strict is a strict subset of loose with 12 to 13 symbols between them, calling shared code while keeping substantial per-host bodies. No threshold resolves it, so E-02 decides per symbol. |
| F-03 | HIGH | `difflib` similarity after host-token normalisation, both commits | `reclaim_lanes_on_interrupt` is IDENTICAL in length on both sides at 0.998 similarity (98 `ast.unparse` lines each at review HEAD, 68 each at `f763be8c`). That is copied code, and the strict test misses it only because both copies call shared helpers. It is the anchor case and E-03's sole subject. The authored "174/174" matches no metric reproduced at review (the raw source span is 252), so E-03 must state its metric. |
| F-07 | BLOCKER | `git show --stat d4dd6b88` and `7ebc2964`; `ls tests/*characterization*` -> no such file | E-05's PRESCRIBED TEST FORM WAS DELIBERATELY RETIRED FOUR DAYS BEFORE THIS PLAN WAS AUTHORED. Commit `d4dd6b88` (2026-09-18) "retire change-detector tests over code text and prose" deleted `tests/test_wtiso_characterization.py`, and `7ebc2964` deleted four `test_rununify_*_characterization.py` files (~3,900 lines) removing source-text pins, `SequenceMatcher` ratios and AST censuses. NO `tests/*characterization*` file exists today. Writing one would revert a maintainer decision, so E-05 now demands OBSERVABLE-BEHAVIOR pins only and forbids source-text assertions. |
| F-08 | HIGH | `tests/test_runner_refork_guard.py` `REFORK_TABLE` + `Owned` contract; measured `oc_runipd.integrate_lane_branch is runner_shared.integrate_lane_branch` -> False | THE RE-FORK GUARD IS INCOMPATIBLE WITH THIS PLAN'S "THIN SHELL" DESIGN, so "re-base any guard that pins it as forked" would fail. Each row requires the runner to have NO top-level definition of the symbol AND to expose the OWNER'S OBJECT (`assertIs`). A host shell is a top-level definition and is not the owner's object, failing both halves. The guard is for bare RE-EXPORTS; a shell-bound symbol must be pinned by DELEGATION instead. Baseline `17 passed`. |
| F-09 | HIGH | `reconcile_interrupted` bodies quoted; `driver_finalize` measured | E-04 NAMED TWO ALREADY-UNIFIED SYMBOLS AS LIFT TARGETS. `reconcile_interrupted` is a two-line body on BOTH sides, byte-identical, delegating to `runner_shared.reconcile_interrupted` (similarity 1.000) - already the sanctioned shape. `driver_finalize` calls `runner_shared` on both sides (23/22 lines, 0.720), so it is PARTIALLY shared and a judgement call for E-02, not an unshared fork. Both removed from the cluster lists. |
| F-10 | MEDIUM | `40it5e` `Status: reviewed` (not executed); its `Scope-Paths` claims `tests/test_rununify_characterization.py`; this plan's `Item-Dependencies: none` | E-05 PLANNED TO EXTEND A FILE ANOTHER PENDING PLAN OWNS AND HAS NOT YET CREATED. The authored fallback ("create it if that plan has not executed") makes two plans create and extend the same new file with no declared edge, so the runner's dependency-depth sort cannot order them. `40it5e` F-08 records the same edge from the other side. E-05 now writes into files this plan owns. |
| F-04 | MEDIUM | `rununify` PR-006, quoted | That Set's original headline figure came from an ad-hoc scan that does not exist in-tree, so it could not be re-derived. A measurement in this area has ALREADY been quoted wrongly once (58 symbols / 2711 lines, corrected to 20 / 667 in `40it5e` OQ-01). E-01 commits a scanner so this plan's numbers cannot rot the same way. |
| F-05 | MEDIUM | `rununify` E-02, quoted; the figures re-measured at `40it5e`'s own review | The two hosts' suites are asymmetric, so a reconciliation can change agy behavior with both suites green, which is why E-05 requires pins written BEFORE each change. NOTE THE CITED NUMBERS ARE 2026-08-30 DATA AND ARE STALE: `40it5e`'s review re-measured 284 oc / 97 agy (2.9x, not the 95/21 and 4.5x quoted here), and `integrate_lane_branch` now has 13 referencing test files rather than zero. The ARGUMENT survives the correction and is why the item stands; the figures should not be re-quoted as current. |
| F-06 | LOW | the residue table; spec `c4gd2h` R19 verified at review | The stop/signal cluster is the largest group in the residue (8 symbols after `reconcile_interrupted` was removed per F-09). It is the code that runs when an operator interrupts a run, and spec `c4gd2h` R19 constrains it ("A later run MUST refuse to blindly resume an `unknown_outcome` item"), so E-04 calls it out for particular care rather than treating it as ordinary extraction. Note the stop cluster is also the LEAST similar group measured (`install_stop_triggers` 0.493, `_observe_between_turn_stop` 0.679, `_record_forced_stop` 0.693), so it is the group most likely to contain a real capability difference and the least likely to be a pure move. |

## Proposed changes (ordered, validatable)

1. Commit a scanner reporting both tests with their definitions AND its line metric (E-01).
2. Decide every residue symbol SHARE or HOST-SPECIFIC against the maintainer's test, and immortalize the table (E-02).
3. Share `reclaim_lanes_on_interrupt`, the unambiguous equal-length 0.998 case, pinning it in the guard form
   that matches the binding shipped (E-03).
4. Share the low-risk remainder cluster (E-04), then the lock/base cluster preserving `c4gd2h` R2's
   observable release (E-06), then `set_plan_approved` alone with a both-directions attribution test (E-07),
   then the stop/signal cluster last (E-08), skipping and naming any symbol the scanner reports as already
   delegating.
5. Prove no behavior changed, with OBSERVABLE-behavior pins written first in a file this plan owns (E-05).

## Deferred / out of scope (with reason)

- THE FIVE LARGE HOST-SHAPED FUNCTIONS. `run_queue` makes EIGHT calls into `runner_shared` on EACH side
  (corrected at review: the authored "456 agy lines / 10 calls" measured 161 `ast.unparse` lines and 8 calls,
  the 456 being the raw source span); `main`, `build_parser`, `expand_selectors` and
  `retry_deferred_integrations` all delegate too. They are the host-shaped shells the Set always expected to
  remain, so they are not residue and this plan does not touch them.
  - Carrier-Declined: NOTHING IS OUTSTANDING. These are the sanctioned end state ("CORE-PLUS-HOOK for the
    five large host-shaped functions rather than one side winning", the maintainer's 2026-09-14 ruling
    recorded in `rununify`'s orchestrator), not deferred work, so filing an item would assert a defect the
    maintainer explicitly chose.
- RE-DOING ANY EXECUTED `rununify` CHILD'S WORK. All 11 are `executed` (verified at review); this plan starts
  from their result.
  - Carrier-Declined: ALREADY DISCHARGED. Eleven children are terminal and must not be reopened
    (`AGENTS.md`: close a post-execution gap with a new corrective IPD, which is what THIS plan is).
- ANY BEHAVIOR CHANGE. This is extraction. A behavior difference discovered mid-flight is a finding to
  REPORT (and, if it matters, a separate plan), because fixing it inside a pure-move item would make the
  move unverifiable.
  - Carrier-Declined: NO CARRIER CAN BE NAMED IN ADVANCE, and naming a speculative one would file work
    nobody has shown exists. OQ-02 resolves the handling (report, leave forked) and E-04 requires the symbol
    and its reason to be recorded, so a divergence found at execution becomes a NAMED finding with evidence,
    which is the point at which filing a carrier is possible and honest.
- THE ORCHESTRATOR'S RETIREMENT. The maintainer decided 2026-09-22 that `rununify`'s parent retires as
  `executed` with the residue filed as this new Set. This plan does not reopen that.
  - Carrier-Declined: THIS PLAN IS THE CARRIER. The maintainer's decision was "Mark it done, file the rest as
    new work", and `40it5e` E-04 names `gqo6if` by id as the residue's carrier, so the obligation is held
    here rather than deferred.

## Scope check

- Over-scope: none.
- Under-scope: none remaining. Every symbol in the loose-test residue is either shared (E-03/E-04) or recorded
  host-specific with evidence (E-02), and membership is decided by E-01's scanner at execution HEAD rather
  than by any count fixed in this text.
- Under-scope, closed at review (2026-09-22): E-05 prescribed a test FORM this repository deliberately retired
  four days before the plan was authored, and no `tests/*characterization*` file exists (PR-003/F-07, now
  observable-behavior pins with source-text assertions forbidden); "re-base any guard that pins it as forked"
  would have FAILED against `tests/test_runner_refork_guard.py`, whose contract requires no top-level
  definition plus the owner's own object and is therefore incompatible with the thin-shell design this plan
  chooses (PR-005/F-08, now guard-form aware); E-04 named two already-unified symbols as lift targets
  (PR-002/F-09, both removed with the measured evidence); E-05 planned to extend a file another pending plan
  owns and has not created, with no declared dependency edge (PR-004/F-10, now writes into files this plan
  owns); every headline count was unreproducible at the plan's own cited HEAD (PR-001/F-01/F-02/F-03, now
  corrected with both commits measured and the metric named); and every Deferred row named no durable carrier
  (PR-006).

## Required tests / validation

BEHAVIORAL pins written per symbol BEFORE each change (E-05), in a file THIS plan owns rather than
`tests/test_rununify_characterization.py`, which is `40it5e`'s undelivered deliverable (F-10) and whose
`*_characterization` FORM this repository retired in `d4dd6b88` / `7ebc2964` (F-07). Assert through the public
seam; a source-text, line-count, `SequenceMatcher` or AST-shape assertion fails E-05 even when green.

Both hosts' runner suites, with the invocation stated. `tests/test_runner_refork_guard.py` baseline `17
passed` at review: add a row ONLY for a symbol bound as a bare re-export, since the guard's rows require no
top-level definition PLUS the owner's own object and therefore cannot describe a host shell (F-08); pin a
shell-bound symbol by DELEGATION instead, and never weaken an existing assertion to make a shell fit.

A bare `python3 -m pytest` judged on failing-node DELTA against a baseline measured the same way in the same
session, never on an absolute green. Measured at review HEAD in this lane: `2 failed, 8521 passed, 3 skipped,
2 xfailed`, both unrelated to this plan (`tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`,
an ambient `OPENCODE_CONFIG_CONTENT` leak, `76 passed` under `env -u OPENCODE_CONFIG_CONTENT`; and
`tests/test_orchestrator_retirement.py::RealRepositorySets`, unrelated corpus drift whose own message forbids
loosening it). Classify each failure pre-existing or attributable; edit neither test.

SPEC-ADJACENT BEHAVIOR MUST BE DEMONSTRATED, NOT ASSERTED, in the two clusters that touch a shipped contract:
`c4gd2h` R2's observable `driver.lock` release (E-06/V-06) and R19's refusal to blindly resume an
`unknown_outcome` item (E-08/V-08). Those are the two places where a "pure move" can silently change a
guarantee, so each needs its own pasted evidence rather than inclusion in a suite total.

## Spec / documentation sync

NO SPEC EDIT IS PLANNED AND NONE IS DECLARED, which is correct for a pure extraction: this plan moves
implementations without changing behavior or any public surface. `Scope-Paths` therefore contains no
`.spec.md` path, deliberately.

TWO CLUSTERS SIT AGAINST A SHIPPED CONTRACT, THOUGH, so the boundary is stated rather than assumed. Spec
`c4gd2h` R2 requires the `driver.lock` release to be OBSERVABLE (drop the `flock` AND remove the file), which
E-06 moves the implementation of; and R19 requires a later run to refuse blindly resuming an
`unknown_outcome` item, which the E-08 stop cluster implements. If EITHER unification would change what the
spec guarantees, that is a FINDING TO REPORT and the symbol stays forked per OQ-02; the spec amendment then
becomes its own decision with its own declared path, never a silent rider on an extraction plan. The reason
is mechanical rather than procedural: this plan's entire validation rests on "no behavior changed", so a pass
that also changed a guaranteed behavior could not be verified by its own evidence.

## Open questions

### OQ-01: Should a symbol whose two copies differ only in log or prompt WORDING count as host-specific?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO - IT IS SHARED, WITH THE WORDING INJECTED. Resolved from the repository rather than deferred: `HostLabels` exists precisely to express a per-host string behind one implementation, and the `hostdedup` Set already classified "differs only by a host string" as a UNIFY case (8 of its symbols), not as a capability difference. The maintainer's own test settles it too - differing wording is not "one host does A, the other NOT A". So a wording-only difference is shared with the label injected, and E-02 must not record it as host-specific.

### OQ-02: If a residue symbol's two copies turn out to differ in BEHAVIOR rather than shape, what then?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: REPORT IT AND LEAVE THE SYMBOL FORKED; do not reconcile the behavior inside this plan. Resolved from this plan's own scope fence and from why that fence exists: this is an extraction plan, and its whole validation rests on "no behavior changed", so a pass that also CHANGES behavior cannot be verified by the characterization pins E-05 relies on. A genuine behavioral divergence is a product question about which host is right, which is the maintainer's to settle and may well be a defect in one host. E-04 already instructs recording a symbol that resists rather than forcing it, so this resolution adds the reason rather than a new mechanism.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: the scanner's committed in-tree path, the single command a reader runs, and its pasted output showing BOTH the strict and the loose count with each test's definition printed alongside AND the LINE METRIC named (`ast.unparse` lines, raw span, or other). A report of one number without its test named FAILS, and so does a line figure without its metric: this area has now produced an unreproducible figure TWICE, including in this plan as authored, and review measured differences of more than 2x between metrics on the same symbol.
  - Required evidence: the scanner's counts RECONCILED against the corrected figures in F-01/F-02, with any difference explained as drift (state the commit) rather than left unremarked. The scanner is authoritative; the point is that a reader can see which figures moved and why.
  - Observed evidence: ONE COMMAND, by path: `python3 tools/runner_fork_scan.py`. THE SCANNER WAS EXTENDED, NOT DUPLICATED: it already existed at `tools/runner_fork_scan.py` (committed by the `hostdedup` Set) and `tests/test_hostdedup_identical_lift.py::TheCommittedScannerIsInTreeAndAgrees` requires it BY PATH while recording that "two independent implementations of 'is this a fork?' that can disagree are worse than one", so a second in-fence scanner would have left that live test cross-checking the wrong file. Decision `09-gqo6if-D1` records this and the out-of-fence path. Pasted output at execution HEAD `2d04ef8b`, BOTH TESTS WITH THEIR DEFINITIONS AND THE LINE METRIC NAMED IN THE OUTPUT ITSELF:

        RESIDUE, UNDER TWO TESTS (both reported; neither is 'the' number)
          line metric: ast.unparse lines with docstrings stripped, measured on the AGY side
          STRICT: neither side references `runner_shared` ANYWHERE in its body (residue_class == NEITHER-DELEGATES)
            -> 8 symbols, 64 lines
          LOOSE: neither side is a single-statement `runner_shared` delegation (i.e. not a sanctioned thin wrapper)
            -> 20 symbols, 602 lines

          by delegation class:
            BOTH-DELEGATE         49  ...
            ONE-SIDE-DELEGATES     1  handle_audit_command
            NEITHER-DELEGATES      8  _add_output_mode_flags, _lane_reclaim_prompt, _record_forced_stop, build_verify_and_continue_notice, classify_recovery_disposition, disable_lane_prompt, enforce_dependency_preflight, route_recovery_turn

    The per-symbol table follows in the same output with each symbol's oc lines, agy lines and host-token-normalised similarity. `--json` exposes the same fields (`strict_test`, `loose_test`, `line_metric`, `strict_residue`, `loose_residue`) so the definitions cannot be separated from the counts by a consumer either.
  - Observed evidence: RECONCILED AGAINST F-01/F-02, with the movement EXPLAINED rather than left unremarked. F-01's "58 symbols co-defined" REPRODUCES EXACTLY at 58. Everything else MOVED and the cause is a commit, not measurement drift: `12a5c05b` ("lift(li44r9): give 16 byte-identical runner symbols one definition each", 2026-09-22) landed AFTER this plan was reviewed and shared sixteen of the eighteen symbols this plan's own cluster items name as lift targets. So F-01's delegation split (32 both / 1 one-side) is now 49 both / 1 one-side / 8 neither, and F-02's strict 23-25 and loose 36-37 are now 8 and 20. Verified per symbol: of the 18 named across E-04/E-06/E-07/E-08, 16 are pure single-statement delegations on BOTH sides with the implementation in `runner_shared` (table in research `fedqe6`). This is the plan's own stated reason for making the scanner authoritative over its prose, and decision `09-gqo6if-D2` records acting on it.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the `aw research new` artifact path (tool-created), plus the full per-symbol table quoted, each row carrying two line counts, a similarity, a SHARE/HOST-SPECIFIC decision, and for every HOST-SPECIFIC row a one-sentence capability difference naming what one host does that the other does not. A row justified by a similarity number alone FAILS, per E-02's own instruction.
  - Observed evidence: TOOL-CREATED, never hand-named: `aw research new --kind findings --slug runner-residue-per-symbol-decisions --set runresidue --apply` wrote `.aw/records/research/20260922-runresidue-00-fedqe6-runner-residue-per-symbol-decisions.findings.md`. `aw research index --check` reports NO finding against it (the manifest findings it does report are pre-existing, on archived 202607 docs). Committed in `294b3d68`.
  - Observed evidence: EVERY residue symbol carries a decision, each with two line counts, a similarity, a decision, and for every HOST-SPECIFIC row a one-sentence capability difference. The eight STRICT residue rows:

      | Symbol | oc/agy | sim | Decision | Capability sentence (abridged; full text in `fedqe6`) |
      |---|---|---|---|---|
      | `disable_lane_prompt` | 3/3 | 1.000 | HOST-SPECIFIC-BY-PIN | each host WRITES ITS OWN module-level `_LANE_PROMPT_DISABLED`, which only that host's reader consults |
      | `_lane_reclaim_prompt` | 29/29 | 0.951 | HOST-SPECIFIC-BY-PIN | READS that per-host flag; the other half of the same pin |
      | `_add_output_mode_flags` | 6/6 | 0.921 | HOST-SPECIFIC-BY-CAPABILITY | oc's `-vv` shows "diff hunks and diagnostics", agy's shows "raw tool parameters"; the two event streams genuinely carry different things |
      | `_record_forced_stop` | 11/11 | 0.999 | THREE-WAY-FORK, FILED | a `runner_shared` copy already exists and is byte-different from BOTH hosts; choosing among three bodies is the reconciliation OQ-02 excludes |
      | `enforce_dependency_preflight` | 8/6 | 0.265 | MIS-LAYERED | agy delegates to `oc_runipd` (a PEER HOST): ONE body exists, so it is not duplication; re-homing is `1f7xno`'s declared scope |
      | `route_recovery_turn` | 16/3 | 0.144 | MIS-LAYERED | same shape, plus a dead `runner_shared` copy |
      | `classify_recovery_disposition` | 23/3 | 0.082 | MIS-LAYERED | same, AND the dead shared copy uses a DIFFERENT snapshot predicate, so pointing the hosts at it would change recovery routing on both |
      | `build_verify_and_continue_notice` | 26/3 | 0.084 | MIS-LAYERED | same, and its destination is formally CONTESTED in `test_runner_layering.py::MOVE_UNSETTLED`, assigned to `1f7xno` |

    Plus `handle_audit_command` (58/4, 0.062, ONE-SIDE-DELEGATES) recorded HOST-SPECIFIC-BY-CAPABILITY: oc IMPLEMENTS the audit verb and agy REFUSES it with exit 2 pointing the operator at the other host, deliberately (plan `mp289j`). That is the maintainer's test met exactly: one host does A, the other NOT A.
  - Observed evidence: NO ROW IS JUSTIFIED BY A SIMILARITY NUMBER, and the table demonstrates why no threshold would have worked: it contains a 0.999 pair and a 0.921 pair that are BOTH legitimately unshared, while a 0.976 pair (`reconcile_disposition`) is a DEFECT. Counts reconcile with E-01: 8 strict rows above, 8 in the scanner's `NEITHER-DELEGATES` class, and `tests/test_runresidue_residue.py::TheResidueIsFullyAccountedFor` asserts that bijection in BOTH directions so the table cannot silently drift from the census.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: `git diff --stat` showing one implementation and two shells; the scanner re-run showing `reclaim_lanes_on_interrupt` no longer in NEITHER-DELEGATES; the behavioral pins for it passing both before and after; and `python3 -m pytest tests/test_runner_refork_guard.py` green (baseline `17 passed`) with a statement of WHICH guard form was used, re-export row or delegation pin, and why it matches the binding shipped. A new `REFORK_TABLE` row for a shell-bound symbol FAILS this item, because that table requires the owner's own object (F-08). Paste all four.
  - Observed evidence: `git diff --stat` for commit `2d04ef8b` - ONE implementation, TWO shells:

        agent_workflows/agy_runipd.py               | 265 +++------------------------
        agent_workflows/oc_runipd.py                | 265 +++------------------------
        agent_workflows/runner_shared.py            | 269 ++++++++++++++++++++++++++++
        tests/test_rununify_run_queue.py            |  27 ++-
        tests/test_worktree_lease_merged_reclaim.py |  84 +++++++--
        tools/runner_fork_scan.py                   | 148 +++++++++++++++

    MY METRIC, STATED as the item demands: 73 `ast.unparse` lines on EACH side before the lift (252 by raw source span; the plan's authored "174" and its review's "98" match neither, which is exactly why the metric is named). Host-token-normalised similarity 0.998. The two bodies differed in ONE statement and only in its SPELLING: `f"Reason: {reason}."` on oc against `"Reason: {0}.".format(reason)` on agy, confirmed by unified diff of the two normalized bodies.
  - Observed evidence: SCANNER RE-RUN shows the symbol OUT of the residue under both tests. `python3 tools/runner_fork_scan.py --symbols reclaim_lanes_on_interrupt`:

        co-defined in both runners : 1
        sanctioned thin wrappers   : 1 (NOT forks)
        REAL FORKS                 : 0
        STRICT ... -> 0 symbols, 0 lines
        LOOSE  ... -> 0 symbols, 0 lines
          by delegation class:
            BOTH-DELEGATE          1  reclaim_lanes_on_interrupt
            NEITHER-DELEGATES      0  -

  - Observed evidence: BEHAVIORAL PINS PASSING BEFORE AND AFTER. The pre-change baseline over the seven affected suites (`test_worktree_lease_merged_reclaim.py`, `test_lane_allocation_idempotent.py`, `test_review_lane_isolation.py`, `test_runner_shared.py`, `test_runner_refork_guard.py`, `test_rununify_run_queue.py`, `test_hostdedup_identical_lift.py`) was `453 passed in 85.74s`, taken BEFORE any edit. After the lift and the two guard re-bases, the SAME seven files: `453 passed in 133.54s`. Same files, same count. The end-to-end reclaimer behavior on BOTH hosts is owned by `test_worktree_lease_merged_reclaim.py` (`21 passed`), which drives the real function against real git worktrees.
  - Observed evidence: `python3 -m pytest tests/test_runner_refork_guard.py` -> `17 passed`, matching the review baseline exactly, and NO `REFORK_TABLE` row was added. WHICH GUARD FORM AND WHY: a DELEGATION pin, not a re-export row. That table requires a listed symbol to have NO top-level definition in the runner AND to expose the OWNER'S OBJECT (`assertIs`); this symbol is bound as a host SHELL because it must inject two per-host callables, so it is a top-level definition and is not the shared object, and a row would fail BOTH halves - exactly F-08's measured point. Verified directly: `oc_runipd.reclaim_lanes_on_interrupt is runner_shared.reclaim_lanes_on_interrupt` -> False. The delegation is instead pinned in `tests/test_rununify_run_queue.py` (the entry MOVED from `STILL_DOUBLE_DEFINED` to `THIN_WRAPPERS_OVER_RUNNER_SHARED`, which is the re-base that file's own header prescribes; `64 passed`) and in `tests/test_runresidue_residue.py::TheAnchorSymbolIsSharedAndStillBehaves`. No assertion was weakened; decision `09-gqo6if-D3b` records both re-bases.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: for each of the six remainder-cluster symbols, either one implementation plus two shells (shown by `git diff --stat` and the scanner) or E-02's recorded HOST-SPECIFIC decision quoted; plus any name SKIPPED as already-shared with its measured evidence (review found `reconcile_interrupted` fully delegating at similarity 1.000, per F-09). Lifting a symbol the scanner reports as already delegating FAILS this item.
  - Observed evidence: EVERY SYMBOL IN THIS CLUSTER WAS SKIPPED AS ALREADY-SHARED, WITH MEASURED EVIDENCE, and that is the required outcome rather than a shortfall: this item's own preamble states the membership lists are ILLUSTRATIVE and that "any symbol named below that the scanner reports as already delegating must be SKIPPED and NAMED as skipped, not lifted", and this V-item makes lifting such a symbol a FAILURE. Measured per symbol with `python3 tools/runner_fork_scan.py --symbols ...`, each reported `BOTH-DELEGATE` with both sides a pure single-statement delegation and the implementation in `runner_shared`:

        _escalation_recorder            oc(pure-deleg) | agy(pure-deleg) | runner_shared
        _budget_breach_recorder         oc(pure-deleg) | agy(pure-deleg) | runner_shared
        build_isolation_notice          oc(pure-deleg) | agy(pure-deleg) | runner_shared

    Shared by commit `12a5c05b` (`li44r9`), which landed after this plan was reviewed. NOTHING WAS LIFTED HERE, so no already-delegating symbol was touched.
  - Observed evidence: THE TWO REMAINING NAMES ARE RECORDED HOST-SPECIFIC, with E-02's decisions quoted. `disable_lane_prompt` (3/3, 1.000) and `_lane_reclaim_prompt` (29/29, 0.951) are HOST-SPECIFIC-BY-PIN: `disable_lane_prompt` mutates a module-level `_LANE_PROMPT_DISABLED` through `global` that only its OWN module's `_lane_reclaim_prompt` reads, so a shared body would set a flag nobody reads and prompt suppression on a repeated interrupt would silently stop working, whose only symptom is an unattended run pausing on a question nobody can answer. That is pinned by FOUR existing guards (`tests/test_runner_shared.py::UnmovableSymbolTests`, `tests/test_hostdedup_identical_lift.py::TheDeliberatelyUnliftedSymbol`, and this plan's own new pins), and this plan's conventions forbid weakening an assertion to make a shell fit. Decision `09-gqo6if-D5` records the analysis, including that unifying the PAIR together is the one legitimate future route and why it was not taken here. `_add_output_mode_flags` (6/6, 0.921) is HOST-SPECIFIC-BY-CAPABILITY: the help strings describe different observable per-host behavior (oc `-vv` "diff hunks and diagnostics" against agy "raw tool parameters"), not mere wording, so OQ-01's wording-only rule does not reach it.
  - Observed evidence: `build_isolation_notice`, which this item flagged as the likeliest genuine host difference at 0.295, is measured ALREADY SHARED (both sides pure delegation), so the concern is moot; it is named here rather than left unaddressed.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: one implementation per `SHARE` symbol in the lock/base cluster, PLUS explicit evidence that spec `c4gd2h` R2's observable release is unchanged - the `flock` still dropped AND the lock file still removed - demonstrated rather than asserted, since a stranded lock makes the repository look permanently busy. Any symbol left forked named with its reason. A lift with no release evidence FAILS.
  - Observed evidence: ALL THREE LOCK/BASE SYMBOLS ARE ALREADY ONE IMPLEMENTATION, measured, so this item had nothing to lift and nothing was changed. `python3 tools/runner_fork_scan.py --symbols run_lock locked_run evaluate_clean_base_for_launch` reports all three `BOTH-DELEGATE`, each side a pure single-statement delegation, implementation in `runner_shared`:

        run_lock                        oc(pure-deleg) | agy(pure-deleg) | runner_shared
        locked_run                      oc(pure-deleg) | agy(pure-deleg) | runner_shared
        evaluate_clean_base_for_launch  oc(pure-deleg) | agy(pure-deleg) | runner_shared

    Shared by `12a5c05b` (`li44r9`). Per this V-item's own rule, lifting an already-delegating symbol would FAIL, so they are named as skipped.
  - Observed evidence: SPEC `c4gd2h` R2's OBSERVABLE RELEASE IS UNCHANGED, and the strongest available evidence is structural rather than a fresh demonstration: this plan made NO edit to `run_lock`, `locked_run`, `runner_shutdown.py` or any lock path (commit `2d04ef8b` touches `runner_shared.py`, the two drivers, two test files and the scanner; the only `runner_shared` addition is `reclaim_lanes_on_interrupt`). Because the acquisition and release already live in ONE shared body, there is no second copy for a divergence to hide in. The existing gates confirming the behavior still pass: `tests/test_runner_shutdown.py` and `tests/test_concurrent_driver_guard.py` are green inside the full-suite run below, which includes its real two-process contention tests (`RealTwoProcessContentionTests::test_a_KILLED_holder_does_not_strand_the_lock`, `::test_the_lock_is_reacquirable_after_the_holder_exits`, `::test_a_second_holder_is_genuinely_EXCLUDED_and_the_holder_is_NAMED`), which are precisely the observable-release assertions - a stranded `flock` or a surviving lock file reds them.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: EITHER one shared `set_plan_approved` with the per-host actor arriving through the descriptor with no default, plus a pasted test asserting the recorded actor in BOTH directions (an oc approval records the oc command, an agy approval the agy one); OR E-02's HOST-SPECIFIC decision with its capability sentence. A lift without the both-directions attribution test FAILS, because the value lands in a plan's PERMANENT workflow history and a silent misattribution is unrecoverable.
  - Observed evidence: `set_plan_approved` IS ALREADY ONE IMPLEMENTATION, so no lift was available and none was performed. `python3 tools/runner_fork_scan.py --symbols set_plan_approved` reports `BOTH-DELEGATE`, both sides a pure single-statement delegation, implementation in `runner_shared`; shared by `12a5c05b` (`li44r9`). Per this V-item's structure, the alternative branch applies: there is no "lift with no attribution test" to fail, because there is no lift.
  - Observed evidence: THE MISATTRIBUTION HAZARD THIS ITEM WAS WRITTEN TO GUARD IS ALREADY RESOLVED, and the mechanism is the one this item prescribed. `runner_shared.dispatch_turn` binds `set_plan_approved = getattr(driver_module, "set_plan_approved", None)` with NO fallback default, so the per-host actor arrives through the host rather than being defaulted in shared code - exactly the "no default" property the item demanded, reached by the descriptor seam the `hostdedup` Set established rather than by a second mechanism. `tools/runner_fork_scan.py`'s own module docstring records the hazard and the measurement behind it (`"aw oc run --full-auto"` against `"aw agy run --full-auto"`, where "a lift performed on the identity verdict alone would have misattributed every Antigravity auto-approval in permanent plan history"), and its `--closure` report exists to surface exactly that class. This plan added NO new attribution test because it performed no lift; asserting a both-directions attribution for code it did not touch would be evidence for work not done.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: the scanner re-run showing the NEITHER-DELEGATES class reduced to EXACTLY the HOST-SPECIFIC set E-02 recorded, quoted side by side so a reader can check the two sets match; every stop-cluster member either shared or named with its capability sentence; evidence that `c4gd2h` R19's refusal-to-blindly-resume behavior is unchanged; and the `install_stop_triggers` decision (0.493, the most divergent member) recorded before the rest of the cluster moved. A NEITHER-DELEGATES set that does not match E-02's HOST-SPECIFIC set FAILS this item, in either direction.
  - Observed evidence: SEVEN OF THE EIGHT STOP/SIGNAL SYMBOLS ARE ALREADY ONE IMPLEMENTATION, measured, and named as skipped rather than lifted. `python3 tools/runner_fork_scan.py --symbols ...` reports each `BOTH-DELEGATE` with both sides a pure delegation and the implementation in `runner_shared`: `_record_checkpoint_stop`, `_record_deliberate_stop`, `_observe_between_turn_stop`, `install_stop_triggers`, `handle_stop_command`, `terminate_process`, `requeue_interrupted`. Shared by `12a5c05b` (`li44r9`). THE ITEM'S ORDERING INSTRUCTION IS THEREFORE MOOT AND IS RECORDED AS SUCH: `install_stop_triggers`, which this item singles out at 0.493 as the most divergent member to decide first, is already shared, so there was no decision to take before moving the others.
  - Observed evidence: THE EIGHTH, `_record_forced_stop` (11/11, similarity 0.999), IS LEFT FORKED WITH ITS REASON. The two host bodies differ ONLY in an annotation QUOTING style (`stop: runner_stop.StopNowForce` against `stop: 'runner_stop.StopNowForce'`), so it is not a capability difference; what stops it being lifted here is that a `runner_shared` copy ALREADY EXISTS and is byte-different from both, making it a THREE-WAY fork (`python3 tools/runner_fork_scan.py --triples` names it). Choosing which of three bodies is canonical is a reconciliation, which OQ-02 excludes from an extraction plan whose validation rests on nothing changing. Filed on backlog `2yjc5l` with the other dead-shared-copy cases rather than left as prose.
  - Observed evidence: SPEC `c4gd2h` R19 IS UNCHANGED, on structural grounds this plan can actually evidence: NO stop-path symbol was edited (commit `2d04ef8b` adds only `reclaim_lanes_on_interrupt` to `runner_shared` and replaces two host bodies with shells), and the seven shared stop symbols already have ONE body each, so there is no second copy in which the recorded stop state could diverge. The suites that assert the refusal-to-blindly-resume behavior are green inside the full-suite run below: `tests/test_runner_stop.py`, `test_runner_stop_levels12.py`, `test_runner_stop_level3.py`, `test_runner_stop_level4.py`, `test_runner_stop_triggers.py`.
  - Observed evidence: THE BIJECTION, QUOTED SIDE BY SIDE so a reader can check the two sets match. Scanner `NEITHER-DELEGATES` at execution HEAD (8): `_add_output_mode_flags`, `_lane_reclaim_prompt`, `_record_forced_stop`, `build_verify_and_continue_notice`, `classify_recovery_disposition`, `disable_lane_prompt`, `enforce_dependency_preflight`, `route_recovery_turn`. E-02's recorded decision set in research `fedqe6` (8): the SAME eight names, each with a decision (2 HOST-SPECIFIC-BY-PIN, 1 HOST-SPECIFIC-BY-CAPABILITY, 1 THREE-WAY-FORK-FILED, 4 MIS-LAYERED-OWNED-BY-`1f7xno`). The two sets are EQUAL. This is not asserted by eye only: `tests/test_runresidue_residue.py::TheResidueIsFullyAccountedFor` checks it in BOTH directions (`test_every_strict_residue_symbol_has_a_recorded_decision` and `test_no_decision_is_recorded_for_a_symbol_that_LEFT_the_residue`), so the plan's under-reporting and over-reporting failure modes are both gated going forward.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: for each touched symbol, the behavioral test named, shown passing BEFORE the change (pinning present behavior) and AFTER; the test FILE PATH shown to be one this plan owns (not `tests/test_rununify_characterization.py`, per F-10); evidence the file contains NO source-text, line-count, `SequenceMatcher` or AST-shape assertion (per F-07, the form `d4dd6b88` retired); plus the bare `python3 -m pytest` summary with every failure classified pre-existing or attributable against a same-session baseline. A green suite offered without the before-pins FAILS this item: F-05 records that both suites stayed green through an agy-side behavior change once already. An ABSOLUTE-GREEN claim also fails, since two unrelated failures exist at review HEAD.
  - Observed evidence: THE PINS LIVE IN A FILE THIS PLAN OWNS: `tests/test_runresidue_residue.py` (new, 13 tests, `13 passed`). NOT `tests/test_rununify_characterization.py`, which is plan `40it5e` E-03's undelivered deliverable and whose creation by two plans with no dependency edge is F-10's recorded race. Decision `09-gqo6if-D6` records the choice.
  - Observed evidence: NO SOURCE-TEXT, LINE-COUNT, `SequenceMatcher` OR AST-SHAPE ASSERTION, per F-07 (the FORM `d4dd6b88` and `7ebc2964` retired four days before this plan was authored). Every assertion is BEHAVIORAL (call the symbol, observe its effect) or a DELEGATION-IDENTITY check consumed FROM the committed scanner, which is the same seam `tests/test_hostdedup_identical_lift.py` already consumes so the repository keeps ONE census rather than two that can disagree. Verified by inspection of the file: it contains no `getsourcelines`, no `SequenceMatcher`, no `inspect.getsource`, and no assertion over a line count or a similarity ratio; the numbers it reads are the scanner's structured `census()` fields.
  - Observed evidence: PINS PASSING BEFORE AND AFTER, per symbol touched. Only one symbol was touched (`reclaim_lanes_on_interrupt`). Its behavior is pinned by the pre-existing both-hosts suites, run BEFORE any edit: `453 passed in 85.74s` across the seven affected files. After the change: `453 passed in 133.54s`, same files, same count. The new file adds: each host reaches the ONE shared implementation; the shared body REFUSES (TypeError) without its per-host prompt callables, which is the property the no-default injection exists to create; prompt suppression still works PER HOST after the lift (the flag each host sets is the flag it reads, and the suppressed reader returns None without touching stdin); and an empty lane set is a no-op driven through EACH HOST'S OWN SHELL, so a shell that dropped an argument or passed the wrong callable would red.
  - Observed evidence: THE PINS WERE MUTATION-TESTED rather than assumed to bite. Injecting one statement into the oc shell so it is no longer a pure delegation reds exactly the two intended tests with self-explaining messages: `TheAnchorSymbolIsSharedAndStillBehaves::test_each_host_reaches_the_ONE_shared_implementation` ("a real body on either side is a RE-FORK of the symbol this plan shared") and `TheResidueIsFullyAccountedFor::test_the_anchor_symbol_is_NOT_in_the_residue_any_more` -> `2 failed, 11 passed`. Reverted with `git checkout --`, then `13 passed` again.
  - Observed evidence: THE SUITE DELTA, judged on failing-node delta against a same-session baseline taken the same way, never on an absolute green. Baseline BEFORE any edit, bare `python3 -m pytest`:

        1 failed, 8688 passed, 3 skipped, 2 xfailed, 6 warnings in 221.27s (0:03:41)
        FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped

    AFTER all changes, bare `python3 -m pytest`:

        1 failed, 8701 passed, 3 skipped, 2 xfailed, 6 warnings in 266.13s (0:04:26)
        FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped

    ZERO NEW FAILING NODE IDS; the one failure is the SAME node in both runs and is classified PRE-EXISTING: it is the ambient `OPENCODE_CONFIG_CONTENT` leak F-05's suite rule already names, and `env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py` gives `76 passed`. Neither test was edited. NOTE the review-time second failure (`test_orchestrator_retirement.py::RealRepositorySets`) did NOT occur in this lane and so is not claimed either way. Passed count rose by 13, which is exactly this plan's new file.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
- Right-sizing note (added at review, PR-007): the authored plan carried FIVE E-items, one of which (E-04) covered 18 symbols across FOUR unrelated clusters with four independent test surfaces, and the linter's `IPD-Z602` density advisory flagged it. It is now EIGHT items: E-04 (low-risk remainder), E-06 (lock/base, which owns spec `c4gd2h` R2's observable release), E-07 (`set_plan_approved` alone, because it writes permanent history through a per-host actor), and E-08 (stop/signal, last because it is both the riskiest and the least similar cluster). The order is least-risky-first deliberately, so the group most likely to hold a real capability difference runs against the most accumulated evidence. The residual `IPD-Z602` is a COUNT advisory on eight leaves, which is the expected consequence of splitting and is not a density problem: each item now names one cluster and one test surface.

EXECUTION CONTRACT. Commit ONLY files this plan changed, path-scoped; never `git add -A`; never push.
When reporting tests passed, paste the ACTUAL runner output. Do NOT mark an `E-*` item performed for work
not done, and do NOT fill a `V-*` `Observed evidence` block with anything but observed output.

THE HONESTY RULE THAT MATTERS MOST HERE is the residue count, AND THIS PLAN'S OWN FIRST DRAFT BROKE IT,
which is why the rule is stated as a measured lesson rather than as advice. The figure has now been wrong
TWICE in this area: once as a NAME-level count (58 symbols / 2711 lines, which treats a genuinely shared
function as duplicated whenever each host keeps a wrapper), and once in THIS PLAN as authored (7 / 170 strict
and 20 / 667 loose, which reproduced under NEITHER test at the plan's OWN cited HEAD `f763be8c`; review
measured 25 / 444 and 37 / 1103 there, 23 / 391 and 36 / 1122 at review HEAD). The anchor's "174 lines each"
matched no metric either (98 `ast.unparse`, 252 raw span). So: never report a residue figure without naming
the test AND the line metric that produced it, re-derive every figure with E-01's committed scanner at
execution HEAD rather than quoting this document, never let a similarity score stand in for a per-symbol
decision, and if the two tests disagree report BOTH rather than picking the flattering one.

TWO FAILURE MODES POINT IN OPPOSITE DIRECTIONS AND BOTH ARE LIVE HERE. Under-reporting the residue would
declare the directive met when it is not. OVER-reporting it would send an executor to "unify" code that is
already one implementation, which is how `reconcile_interrupted` (a two-line delegation on both sides,
similarity 1.000) ended up in a list of lift targets. The defence against both is the same: the scanner
decides membership, and any name in this plan's prose that disagrees with the scanner is reported as a
correction rather than acted on.

SCOPE FENCE. Touch ONLY the paths in `- Scope-Paths:`. Change NO behavior; if a symbol's copies differ
behaviorally, report it and leave it forked (OQ-02). Do not touch the five large host-shaped functions. If
the work genuinely requires a path outside the fence, make the edit and justify it, since `aw ipd finalize`
refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-
unmodified path carries a `--scope-ack`.

POST-GATE LIFECYCLE. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` item
must carry observed evidence before the plan moves to `.aw/records/plans/executed/`. The runner owns the
terminal transition; a worker-role process is refused by `AW-LIFECYCLE-ROLE-001`.
