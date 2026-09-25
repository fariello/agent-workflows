# IPD: Distinguish verification that never ran from verification that ran inconclusively and refuse a stale plan path loudly

- Date: 2026-09-08
- Kind: child
- Concern: `unverified` is written for THREE materially different facts and a reader cannot tell them apart. RE-MEASURED at review HEAD `34c26b95`, `verify_disp` is assigned `"unverified"` at exactly three sites in `oc_runipd.py` (`:6645` unparseable outcome JSON with nonzero exit, `:6647` NO outcome file written at all, `:6649` the turn raised `KeyboardInterrupt` or `StallTimeout`), with the matching triple in `agy_runipd.py` (`:3696`, `:3698`, `:3700`). "The verifier ran and could not conclude", "the verifier never wrote its verdict", and "the verifier turn was killed" are three different problems with three different remedies, and all three read as one benign-looking caveat.
  THE TWO OUTER SITES ARE OWNED BY OTHER PLANS IN THIS SET, WHICH NARROWS THIS PLAN'S REAL TARGET TO ONE SITE PLUS THE LABELLING. Site 1 (the `except Exception` unparseable arm) is `1bfppy` E-02's, which routes it through a fail-closed verdict mapping; site 2 (the no-outcome-file `else`) is the one this plan uniquely owns; site 3 (the interrupt) is arguably owned by the indeterminate machinery (OQ-01, now resolved below). So this plan ADDS NAMES to all three but must CHANGE the behavior of only the ones no sibling is changing. `1bfppy` is `reviewed` with `- Readiness: go-pending-approval` and `bxx9af` now declares `- Item-Dependencies: executed:1bfppy`; this plan should read both on disk before editing, because three plans converging on one fifteen-line block is the real execution hazard here, larger than any single item below.
  THIS IS THE SURVIVING HALF OF BACKLOG `t74o5q`. THAT ITEM'S CENTRAL MECHANISM IS ALREADY FIXED AND ITS 23 MEASURED FAILURES CANNOT RECUR. The item's root cause was that the verify prompt cited a `pending/` path the self-finalize step had already invalidated. That was fixed at commit `1549c018` ("fix(runner): re-resolve current plan path before verification turn", authored 2026-08-27 22:42:41 -0400, i.e. 2026-08-28 02:42:41 UTC), which re-resolves through `resolve_plan_path` immediately before building the prompt and passes the RE-RESOLVED value to both `build_verifier_prompt` and the child launch. RE-VERIFIED at review: `oc_runipd.py:6579-6584` re-resolves, `:6586` passes `current_plan_path` to `build_verifier_prompt`, and `:6600-6604` passes it to `run_opencode`; the agy twin is `:3636-3640`. THE FIX PREDATES THE ITEM, which the item itself now records: it was filed 2026-08-30 02:02 UTC (commit `f4a1b5d8`), and all 23 failing turns are in three runs created 2026-08-25T03:51Z (13), 2026-08-25T10:58Z (3) and 2026-08-28T00:29Z (7), every one BEFORE the fix.
  THE OBSOLESCENCE SCAN WAS RE-RUN AT REVIEW AND REPRODUCES EXACTLY, with the corpus grown: 140 run directories (was 135), 58 verify session logs (was 57), 35 outcome files (was 34), and still EXACTLY 23 logs containing `File not found: .../pending/<plan>.ipd.md`, distributed exactly as this plan states (13/3/7 in those three named runs). The decisive half is stronger than the plan claimed: 105 runs were created AFTER the fix timestamp and ZERO of them contain such a log. So the item's fix (1) is DEAD, and its tests (a), (c) and (d) are already satisfied (the regression `tests/test_oc_runipd.py::VerifierPromptTests::test_resolve_plan_path_handles_transition_to_executed` shipped in the same commit and passes today: re-run at review, `1 passed`).
  WHAT SURVIVES IS THE ITEM'S FIX (3) AND (4), AND THEY ARE REAL. Fix (3): a verifier that exits without writing its outcome file must be a recorded HARD failure, not a quiet `unverified`. Fix (4): the `except DriverError: current_plan_path = plan_path` fallback (re-verified at review, `oc_runipd.py:6583-6584`, agy `:3639-3640`) still SILENTLY substitutes a known-stale path when re-resolution fails, which is the same class of defect the fix removed from the happy path but left on the error path.
  NOTE A SECOND, UNMENTIONED INSTANCE OF THE SAME PATTERN, so the executor does not "fix" it by accident or miss it deliberately: the SAME re-resolve-then-fall-back shape appears again for the FINALIZE step (`oc_runipd.py:6716-6718` computing `current_plan_for_finalize`, agy `:3766-3767`). It is a different call site with a different consumer and is NOT this plan's fix (4). Read it, state that you identified it, and leave it alone; if it deserves the same treatment that is a follow-up, not a silent widening of this fence.
- Scope: Split `unverified` into distinguishable recorded facts so "verification never ran" is not reported as "verification was inconclusive", and make the stale-path fallback refuse loudly instead of proceeding with a path it knows may be wrong. EXCLUDES the verdict MAPPING for a verdict that WAS written (sibling `1bfppy`, this Set's Order 05, which owns the fail-closed table); excludes re-fixing the prompt path (already fixed at `1549c018`); excludes the model/rate-card record (`vlf75p`) and the unconsumed-evidence defect (`rbftpl`); excludes changing whether the verifier turn runs at all.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_runner_refork_guard.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: runverdict
- Order: 6
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: fzxfph
- Blocks-Release: next
- From-Backlog: t74o5q

## Workflow history
- 2026-09-22 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: fzxfph verified (set runverdict, attempt 1).
- 2026-09-22 validated (aw oc run, opencode/its_direct/pt3-claude-opus-5-1m-us): ALL FIVE E-ITEMS PERFORMED, ALL FIVE V-ITEMS PASS with pasted evidence. `aw ipd lint --phase pre-transition` conforming. Suite bare in this lane: `1 failed, 8325 passed, 3 skipped, 2 xfailed`, against a BASELINE MEASURED IN THIS SAME LANE BEFORE ANY EDIT of `1 failed, 8309 passed, 3 skipped, 2 xfailed`; the one failure is the SAME NODE ID on both sides (`tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`) and is ENVIRONMENTAL, not this plan's: it asserts a non-isolated turn inherits no `OPENCODE_CONFIG_CONTENT`, and THIS RUNNER exports that variable into my own turn, so it fails for any agent executing under `aw oc run` and passes immediately with the variable unset (`env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py` -> `76 passed`). NOTE the plan's expected baseline failure (`test_reporting_contract` tripping over another party's untracked `opencode-recovery/*.md` files) did NOT occur; those files are absent from this lane.
  THE TREE HAD MOVED UNDER THE PLAN IN TWO WAYS THAT CHANGED THE WORK, both re-measured rather than assumed. FIRST, `1bfppy` HAS LANDED: it is `- Status: executed` in `executed/` (the plan was authored expecting `reviewed`), so its verdict table, its `except` unparseable arm and its refusal wording are all present, and this plan's E-01/E-02 correctly added only an annotation to that arm rather than a second name. SECOND, the SIX write sites are FOUR: commit `70a2059f` unified `execute_item` into `runner_shared.execute_item_core`, so the per-host duplication the plan counted no longer exists. Neither is a shortfall; both are recorded in V-01 with the evidence.
  THE HONEST RECONCILIATION OF `1bfppy`'s "FREE FIELD". That plan's in-tree note said it minted no name for the unparseable case so this executor would have "a free field to name and nothing to reconcile". It needed no new name: a verdict that WAS written belongs to the verdict table by construction, so fact 1's code is an ALIAS (`VERIFY_ABSENCE_VERDICT_UNREADABLE = VERDICT_REFUSAL_CODE_UNREADABLE`), asserted structurally so the two cannot drift. That keeps `VERIFY_ABSENCE_CODES` a CLOSED set over all four facts while spelling one fact once.
  FOUR FACTS SHIPPED, NOT THREE, and the fourth is E-03's rather than scope creep: an unresolvable plan means verification was NOT ATTEMPTED, which an operator acts on differently from a verifier that ran and produced nothing. `verify_disp` DELIBERATELY KEEPS `unverified` at every site, because a novel token renders as a bare `-` in `aw runs` (measured) which is exactly how "no verification ran" already renders; the distinction rides on the refusal record and a new `verify_absence` field, both of which already render through `r2i1b1`'s plumbing, so `run_viewer.py` needed no `--scope-reason`. NO GATE CHANGED: `integration_is_earned` is untouched, and its validation-OFF limit is recorded rather than overclaimed (V-02 pastes both paths).
  TWO INSTRUCTIONS FOLLOWED THAT AN EXECUTOR WOULD BE TEMPTED TO SKIP. The interrupt case is labelled UNKNOWN OUTCOME and explicitly NOT a failure, per spec `c4gd2h` R22, after confirming by my own AST reading that the verify handler writes no `stopped` record and so `runner_stop.is_indeterminate` never sees it (OQ-01). And the byte-identical TWIN fallback at the finalize site was found, left untouched (proven: its only appearance in the diff is inside a comment), and given a durable carrier as backlog `rfhiu2` rather than merely mentioned.
  DEFECT FOUND AND FILED: backlog `rfhiu2`, the finalize-side stale-path fallback. Classified `followup` and NOT `bug`, deliberately: the verify-side twin was filed on 23 measured occurrences, while this is a hazard read from source with no user-perceptible impact measured, and the repository's own rule is that an unmeasured hunch is not a bug. The reclassification trigger is written into the item. Also brought the plan's eight deferred rows into conformance with `check.ipd-uncarried-obligation` (two `- Carrier:` handoffs, six reasoned `- Carrier-Declined:`).
- 2026-09-13 approved (aw set): status set to approved
- 2026-09-09 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-F01..PR-F10 all FIXED; OQ-01 and OQ-02 resolved from evidence; readiness go-pending-approval

- 2026-09-09 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-F01..PR-F10, all ten FIXED, none deferred. Readiness `go-pending-approval`. Record: `.aw/records/reviews/20260908-runverdict-06-fzxfph-distinguish-verification-that-never-ran-from-verification-th.review.md`. `aw ipd lint --phase author` conformed BEFORE semantic review and `--phase review-finalize` conforms after, so nothing here was structural. DISCLOSURE: same agent/model authored this plan, so this is a SELF-REVIEW resting on RE-MEASUREMENT.
  THE OBSOLESCENCE ANALYSIS IS THIS PLAN'S BEST WORK AND IT REPRODUCED IN FULL, which is worth stating first because it is the hardest kind of finding to trust second-hand. Re-scanned at review with the corpus grown to 140 run directories, 58 verify logs and 35 outcome files: still EXACTLY 23 `File not found` logs, in exactly the three named pre-fix runs with exactly the 13/3/7 split, and the decisive half is stronger than claimed, since 105 runs were created AFTER the fix timestamp with ZERO occurrences. The `1549c018` regression re-ran `1 passed`. So refusing to graduate the item's fix (1) and tests (a)/(c)/(d) was correct, and the two surviving fixes are genuinely live at HEAD.
  THE HEADLINE DEFECT IS THAT BOTH OPEN QUESTIONS WERE ANSWERABLE FROM CODE, AND ONE ANSWER INVERTS AN INSTRUCTION (PR-F01, PR-F02). OQ-01 asked whether the interrupt site is already covered by the indeterminate machinery, and E-02 told the executor to "leave it alone and say so" if it is. Measured: `is_indeterminate` reads `item["stopped"]["certainty"]`, that record is written ONLY on the execute turn's stop paths, and the verify handler SWALLOWS the exception writing no record, so the predicate returns False and the site is UNPROTECTED. The site therefore belongs in the split; what R22 actually forbids is the LABEL, so the correct outcome is unknown-outcome rather than failure. OQ-02 asked whether an agy twin of the path regression exists: it does not (zero `resolve_plan_path` occurrences in the agy test module), so writing it is required, not conditional, and doubly so because E-03 edits that exact agy fallback.
  THREE PLANS EDIT THIS FIFTEEN-LINE BLOCK AND THIS PLAN COORDINATED WITH ONE (PR-F03). `1bfppy` owns the verdict mapping AND the `except` unparseable arm that this plan also names; `bxx9af` adds an evidence predicate and possibly its own `verification_status` token to the same region and declares `- Item-Dependencies: executed:1bfppy`. Both are `reviewed`/`go-pending-approval`. E-01's overlap check now runs against BOTH siblings, and the fence assigns the `except` arm away from this plan.
  TWO CLAIMS WERE BROADER THAN THE CODE SUPPORTS. The "an `unverified` turn already does not auto-merge" guarantee holds only when validation is ON: measured, the validation-OFF branch of `integration_is_earned` never reads `verify_disp`, so a passing suite still integrates, and oc defaults `validate` FALSE while agy defaults its verifier ON (PR-F04). And a novel token renders as a bare `-` in `aw runs`, identical to "no verification ran", because two `run_viewer` branches match literal values, while `run_viewer.py` is not in this plan's `Scope-Paths` (PR-F05).
  ALSO FIXED: the silent-fallback shape occurs TWICE per host, and the twin at the finalize site was unmentioned, so E-03 now identifies and deliberately spares it (PR-F06); `run_state` was confirmed to have NO token for any of the three facts, retiring an investigation the plan left open (PR-F07); the spec row's pass criterion was misquoted (the "valid evidence-linked envelope" phrase belongs to `RUN-HOST-ATTEMPT`) and its retry obligation is answerable, since no driver-side retry loop exists at all (PR-F08); every line citation had drifted within one day, including six this review re-derived (PR-F09); and E-05 rested on a guard test that does not check what it claimed, plus a stale baseline naming a module that now passes (PR-F10). Two decisions recorded (D-1, D-2), both `Reversible: yes`.

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `t74o5q` as a NARROWED plan; the item carries `- Blocks-Release: next` and this plan inherits that gate. THE OBSOLESCENCE FINDING IS THE MOST IMPORTANT THING IN THIS HISTORY, because it removes most of the item's stated work and all of its urgency. The item's headline ("40% of verifier turns never ran") describes 23 turns in three runs, all created before commit `1549c018` (2026-08-28 02:42 UTC) fixed the exact mechanism it names, and the item was written 2026-08-30, two days AFTER the fix. Measured rather than inferred: every one of the 23 short `File not found` logs is in a run created 2026-08-25 or 2026-08-28T00:29Z; zero runs created after the fix contain one; the fix's own regression test ships in `tests/test_oc_runipd.py` and passes today; and the re-resolved path now reaches BOTH the prompt and the child launch, which the item said it did not. So the item's fix (1) and its tests (a), (c) and (d) are DEAD and are NOT graduated. The item's own "NOT A RESOLUTION-LOGIC DEFECT" paragraph was already half-right and half-stale: it correctly said `resolve_plan_path` was fine, and incorrectly said "the resolved value is not what reaches the CHILD PROCESS", which was true before `1549c018` and is false at HEAD.
  WHAT THIS PLAN GRADUATES IS THE ITEM'S FIX (3) AND (4) AND ITS TEST (b), each re-verified as live at HEAD `44d4950d`. Fix (3) survives because `verify_disp = "unverified"` is genuinely written for three distinct facts at three sites per host, which I located and read rather than trusting. Fix (4) survives verbatim: the silent fallback to a known-stale `plan_path` is still there on the error path, at `oc_runipd.py:6376-6377` and `agy_runipd.py:3640-3641`. Its fix (2) ("order the turn so verification happens BEFORE the plan is moved") is NOT graduated and is recorded as deferred with the reason: `1549c018` solved the same problem by re-resolution rather than reordering, so reordering the self-finalize sequence now would be a second solution to a solved problem, with real blast radius on the `driver_begin`/`driver_finalize` transaction.
  ORDERING RELATIVE TO SIBLING `1bfppy` (Order 05, the verdict mapping): INDEPENDENT, declared as no dependency. That plan owns the case where a verdict WAS written and is mis-mapped; this plan owns the case where no verdict was written at all. They touch adjacent lines in the same block, which is a coordination note and not a dependency, and the runner isolates each item in its own worktree.

## Goal

Make the run record say WHICH of three things happened when verification did not produce a verdict, and stop the verifier launching against a path the runner knows may be stale.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: distinguish the three facts

- [x] E-01 ENUMERATE AND NAME THE THREE FACTS currently collapsed into `unverified`, as a closed set in `runner_shared.py`, and record at each write site which fact it records. FIND THEM BY SYMBOL, inside `execute_item_core`'s `v_outcome_file` block in `runner_shared.py` (`:11850`, previously duplicated in `oc_runipd.py:6645/6647/6649` and `agy_runipd.py:3696/3698/3700`). Note that with `execute_item` unified into `runner_shared.execute_item_core` (commit `70a2059f`), this block already lives in `runner_shared.py`.
  SITE THE NAMES IN `runner_shared.py`, NOT IN `oc_runipd.py`. `agy_runipd` already imports 48 names from `oc_runipd` (AST-measured at review; 47 at authoring, so re-derive rather than quoting either) and zero flow back, so adding these to oc for agy to import would deepen the layering defect backlog `cnwy8g` owns.
  `run_state.py` HAS NO TOKEN FOR ANY OF THE THREE FACTS, MEASURED AT REVIEW, so the gap this item told the executor to check for is CONFIRMED and needs no investigation pass. Its full vocabulary is exactly `pending, runnable, running, performed, blocked, failed, verifying, verified, correction_required, cancelled, complete`: there is no "never ran", no "unparseable", and no "interrupted". It also imports no first-party module (AST-verified), so consuming it cannot create a cycle, but there is nothing here to consume for these three facts. STATE THAT EXPLICITLY and mint the minimum: the repository already carries three overlapping vocabularies (`TERMINAL_STATES`, `run_state.ALL_STATES`, and the `verify_disp` strings) and a fourth is a real cost, so justify each name you add rather than adding a parallel enum.
  COORDINATE WITH BOTH SIBLINGS, NOT ONE, AND READ THEIR STATUS ON DISK. `1bfppy` (verdict mapping) is `reviewed`/`go-pending-approval` and owns the `except` unparseable arm; `bxx9af` (evidence consumption) is `reviewed`/`go-pending-approval`, declares `- Item-Dependencies: executed:1bfppy`, and adds an evidence predicate plus possibly a new `verification_status` token to the SAME block. So up to three plans name conditions in one fifteen-line region. If either has landed, its names are authoritative for its cases and this plan's cover only what remains; paste a set intersection proving no value is classified twice, against BOTH siblings rather than only `1bfppy`.
  - Depends on: none
  - Expected outcome: a closed named set in `runner_shared.py` distinguishing the three facts, each write site annotated with which it records; the confirmed `run_state` gap stated and each new name justified rather than a parallel enum added; no overlap with EITHER sibling's names, proven by set intersection against both.
  - Execution state: performed

- [x] E-02 WRITE THE DISTINGUISHED FACT AT THE THREE SITES in `runner_shared.execute_item_core` (previously 6 sites across two files, now unified into `runner_shared.py`) so the run record carries which one occurred, and make "verification never ran" a RECORDED HARD failure rather than a quiet caveat. This is the item's fix (3).
  DO NOT CHANGE WHETHER THE RUN CONTINUES, and this is the boundary that keeps this plan small. `integration_is_earned` (find by NAME; `oc_runipd.py:3740` at review, and agy calls the SAME shared function) ALREADY refuses integration when validation is ON and `verify_disp != "verified"`, with an explicit reason ("a green suite deliberately does NOT override an explicit verifier verdict"), and `self_finalize` is gated on the earned verdict, so an `unverified` turn already does not auto-merge and its lane is already preserved. So "hard failure" here means RECORDED AND REPORTED AS SUCH, not a new refusal. Confirm that gate still holds after your change and paste it; do NOT add a second refusal on top of it.
  KNOW THE LIMIT OF THAT GUARANTEE BEFORE CLAIMING IT, measured at review by calling the real predicate: on the validation-ON path ANY non-`verified` token refuses (`unverified`, a new never-ran token, `blocked` and `None` all give `earned=False signal=verifier-declined`), but the validation-OFF branch NEVER READS `verify_disp` at all, so with a passing suite a novel token still gives `earned=True signal=driver-run-suite`. oc defaults `validate` FALSE while agy defaults its verifier ON, so the "already does not auto-merge" claim holds on agy's default and on oc only under `--validate`. State that boundary rather than asserting an unconditional one.
  A NEW TOKEN MUST ALSO RENDER, OR IT IS WORSE THAN THE ONE IT REPLACES. `run_viewer.py:1350-1360` badges only `verified` and `failed`, and `:1617-1631` maps `verified` to `yes`, the set `(unverified, verify-failed, failed)` to `no`, and EVERYTHING ELSE to a bare `-`. So a novel never-ran token renders as `-`, which is exactly how "no verification ran" already renders and is the opposite of this plan's purpose. `run_viewer.py` is NOT in this plan's `Scope-Paths`, so either reuse a token those branches already recognize, or add the path with a `--scope-reason` and extend them. Decide and say which.
  THE INTERRUPT SITE IS NOT COVERED BY THE INDETERMINATE MACHINERY, MEASURED AT REVIEW, which resolves OQ-01 and this instruction with it. `runner_stop.is_indeterminate` (`runner_stop.py:1527`) reads `item["stopped"]["certainty"]`, and that record is written ONLY by `_record_forced_stop`/`_record_deliberate_stop` on the EXECUTE turn's stop path (`oc_runipd.py:5223`, `:6373`, `:7166`). The verify site at `:6649` SWALLOWS `KeyboardInterrupt` and writes no `stopped` record at all, so `is_indeterminate` returns False there and the machinery never sees it. THE CONSEQUENCE CUTS THE WAY THE PLAN FEARED, NOT THE WAY IT HOPED: the site is unprotected, so labelling it is legitimate, but spec `c4gd2h` R22's prohibition on fabricating a disposition still applies, which means the honest label is INDETERMINATE or "interrupted, outcome unknown", NOT a failure. Do not classify a killed verify turn as a verification failure.
  - Depends on: E-01
  - Expected outcome: all three sites in `runner_shared.execute_item_core` record the distinguished fact; the never-ran case is reported as a hard failure rather than a caveat; the interrupt case labelled as unknown-outcome rather than a failure, with the measured reason stated; the run's continue/refuse behavior and lane preservation UNCHANGED and proven so, with the validation-OFF limit stated rather than overclaimed; whichever token is chosen shown to render as something other than `-` in `aw runs`.
  - Execution state: performed

### Task group 2: refuse the stale path instead of using it

- [x] E-03 MAKE THE STALE-PATH FALLBACK REFUSE LOUDLY. `except DriverError: current_plan_path = plan_path` (re-verified in `runner_shared.execute_item_core:11790`, previously `oc_runipd.py:6583-6584`, agy `:3639-3640`) silently substitutes a path captured earlier in the turn when re-resolution fails. That is the item's fix (4), and it is the last surviving piece of the original path defect: commit `1549c018` fixed the HAPPY path by re-resolving, and left this ERROR path substituting a value it knows may be wrong.
  A REFUSAL, NOT A CRASH, AND NOT A SILENT SKIP. An unresolvable plan means verification CANNOT be performed, which E-01 already gives a name to; record that fact and report it rather than launching a child against a path that may not exist. Reuse E-01's vocabulary; do not invent a fourth outcome here.
  THERE IS A SECOND, IDENTICAL FALLBACK AT THE FINALIZE SITE AND IT IS OUT OF SCOPE. Measured at review: `current_plan_for_finalize = resolve_plan_path(...)` / `except DriverError: current_plan_for_finalize = plan_path` in `runner_shared.execute_item_core` (previously `oc_runipd.py:6716-6721` and `agy_runipd.py:3766-3771`), byte-identical in shape to the verify one. It feeds `aw ipd finalize`, not the verifier launch, so it has a different consumer and a different failure model. IDENTIFY IT, SAY YOU FOUND IT, AND LEAVE IT ALONE: fixing it is a follow-up, and fixing only the verify one while an identical hole sits 130 lines below is worth stating rather than hiding.
  STATE WHEN THIS CAN ACTUALLY FIRE, because a refusal on an unreachable branch is dead code. `resolve_plan_path` (`runner_shared.py:1433`, not `:1119`) raises `DriverError` only when the id6 resolves to zero files or to more than one; it tries the id6 selector, then the configured path, then an `rglob` over three roots. Determine and record which real conditions produce that (a plan deleted mid-turn, an id6 collision, a lane worktree missing the plan) and cite the one you can actually construct in a test.
  DO NOT REORDER THE SELF-FINALIZE SEQUENCE. The item's fix (2) proposed moving verification before the plan move; that is NOT this plan's scope, because `1549c018` solved the same problem by re-resolution and reordering the `driver_begin`/`driver_finalize` transaction now would be a second solution to a solved problem.
  - Depends on: E-01
  - Expected outcome: an unresolvable plan produces a named recorded refusal instead of a launch against a stale path; the conditions under which it can fire are stated and at least one is constructible in a test; the self-finalize ordering is untouched; the twin fallback at the finalize site identified, reported and deliberately unchanged.
  - Execution state: performed

### Task group 3: prove and fence

- [x] E-04 TEST ALL THREE FACTS AND THE REFUSAL, per host, from FIXTURES rather than the live run tree. `.aw/records/runs/` is gitignored with zero tracked files (`.aw/.gitignore:14`; `git ls-files` empty), so a test built on the real corpus passes in this checkout and fails in CI, in a fresh clone and in every lane worktree.
  ASSERT THE HISTORICAL CASE IS ALREADY FIXED RATHER THAN RE-FIXING IT. The item's test (d) asked for a regression proving the 23 historical cases would now run; that regression ALREADY EXISTS and passes (`tests/test_oc_runipd.py::VerifierPromptTests::test_resolve_plan_path_handles_transition_to_executed`, shipped in `1549c018`, re-run at review: `1 passed`). Do NOT write a second one. Instead paste that test's passing output as the evidence that the dead half of the item is genuinely dead.
  THE AGY TWIN DOES NOT EXIST, MEASURED AT REVIEW, so OQ-02 is resolved and this is now an instruction rather than a question: `tests/test_agy_runipd_cli.py` contains ZERO occurrences of `resolve_plan_path` and no analogue of that test. Adding one is IN SCOPE and is the honest gap, because `resolve_plan_path` is shared (so the resolution logic is covered once) while each host has its OWN call site and its OWN `except DriverError` fallback, and a shared function does not prove a call site passes its result onward. That is doubly true here since E-03 edits exactly that agy fallback.
  ADD THE PRE-FIX CONTRAST FOR WHAT THIS PLAN DOES CHANGE. For each of the three facts, show that before the change all three produced the same recorded value and after it they do not. Without that contrast a test asserting three distinct values proves nothing about the defect.
  - Depends on: E-02, E-03
  - Expected outcome: per-host tests for the three facts and the refusal, fixture-driven; the existing `1549c018` regression pasted as passing; the agy twin ADDED (measured absent at review); the pre-fix contrast pasted.
  - Execution state: performed

- [x] E-05 PIN THE SHARING SYMMETRICALLY AND MUTATION-CHECK IT. Register every symbol this plan adds in `tests/test_runner_refork_guard.py`'s `REFORK_TABLE` with BOTH runners listed (`Owned("<name>", "runner_shared", BOTH)`), and assert object identity across `oc_runipd`, `agy_runipd` and `runner_shared`.
  THREE OF THAT MODULE'S TESTS FIRE FROM ONE WELL-FORMED ROW, verified at review by reading it: `runner_shared` is already a legal owner in `_MODULES` (`:161-167`), `test_no_runner_redefines_an_already_extracted_symbol` (`:265`) is the AST half, `test_every_runner_attribute_is_the_owning_modules_object` (`:287`) is the identity half, and `test_the_owning_module_really_defines_every_tabled_symbol` (`:316`) catches a typo'd owner. BUT `test_the_table_covers_both_runners` (`:336`) asserts only that the table AS A WHOLE covers both runners, which it already does, so it will NOT verify that YOUR row lists both; do not read its passing as proof of that.
  GREP IS NOT EVIDENCE OF SHARING. It cannot distinguish a shared object from a textually identical copy, which is exactly how `render_stream` was extracted and then re-forked in the other driver with nothing noticing; the one-sided versions of this guard were RETIRED for that reason. Mutation-check: define a local copy in `agy_runipd`, show the guard FAILS, revert, show it passes, and confirm the revert with `git diff --exit-code` on both drivers so no mutation is left in the repository's two highest-contention files.
  - Depends on: E-04
  - Expected outcome: a `REFORK_TABLE` row covering both runners; object-identity assertions across all three modules; the guard demonstrated to fail under a re-fork mutation and cleanly reverted; the AST-measured oc-to-agy import count NOT INCREASED against a before-value you measure yourself (48 at review, 47 at authoring, so assert the non-increase rather than a literal).
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE PATH DEFECT IS FIXED AND THE FIX'S SHAPE IS THE PRECEDENT. `1549c018` re-resolves through `resolve_plan_path` immediately before use and passes the re-resolved value to both the prompt and the child. That is the pattern; this plan extends it to the error path rather than replacing it.
- `resolve_plan_path` IS SHARED AND DISPOSITION-AGNOSTIC (`runner_shared.py:1433`): it resolves by id6 through `selectors.resolve_selectors` first, then the configured path, then an `rglob` over three roots, raising `DriverError` only on zero or multiple matches.
- THE SILENT-FALLBACK SHAPE OCCURS TWICE PER HOST, NOT ONCE: the verify site (`oc_runipd.py:6583-6584`, agy `:3639-3640`) and the FINALIZE site (`oc_runipd.py:6716-6721`, agy `:3766-3771`). Only the first is this plan's fix (4).
- AN `unverified` TURN ALREADY DOES NOT AUTO-MERGE, BUT ONLY WHEN VALIDATION IS ON. `integration_is_earned` refuses when `validate` is truthy and the verdict is not `verified`; its validation-OFF branch never reads `verify_disp`, so a passing driver-run suite still integrates (measured by calling the predicate). oc defaults `validate` FALSE and agy defaults its verifier ON, so the guarantee is host-dependent. This plan improves the RECORD, not the gate.
- A DELIBERATE STOP MUST NOT BE RELABELLED A FAILURE, AND THE VERIFY SITE IS NOT COVERED BY THE MACHINERY THAT ENFORCES IT. Spec `c4gd2h` R22 forbids fabricating a disposition and `runner_stop.is_indeterminate` (`runner_stop.py:1527`) marks a force-cut item unknown-outcome, but it reads `item["stopped"]["certainty"]`, which is written only on the EXECUTE turn's stop path (`oc_runipd.py:5223`, `:6373`, `:7166`). The verify `except (KeyboardInterrupt, StallTimeout)` swallows the exception and writes no `stopped` record, so the predicate returns False there. Labelling that site is therefore legitimate, and R22 still means the label must be unknown-outcome, NOT failure.
- A NEW `verification_status` TOKEN RENDERS AS `-` IN `aw runs` unless the two literal-matching branches are extended (`run_viewer.py:1350-1360`, `:1617-1631`). `run_viewer.py` is NOT in this plan's `Scope-Paths`.
- THE IMPORT DIRECTION IS ONE-WAY: `agy_runipd` imports 48 names from `oc_runipd` (48 at review, 47 at authoring; re-derive); `oc_runipd` imports zero from agy. Shared symbols go in `runner_shared`.
- `run_state.py` IMPORTS NO FIRST-PARTY MODULE (AST-verified) but has NO TOKEN for any of this plan's three facts. Its full vocabulary is `pending, runnable, running, performed, blocked, failed, verifying, verified, correction_required, cancelled, complete`. Neither driver imports it (AST walk, zero matches). Sibling `1bfppy` is wiring it in for the adjacent case.
- `.aw/records/runs/` IS GITIGNORED with zero tracked files (`.aw/.gitignore:14`). Use fixtures: a live-tree test fails in CI and in a fresh clone, not merely in a lane.
- THREE PLANS IN THIS SET TOUCH THE SAME BLOCK: `1bfppy` (verdict mapping plus the `except` arm), `bxx9af` (evidence predicate, depends on `1bfppy`), and this one (the no-outcome-file `else`, the interrupt label, the stale-path refusal). Both siblings are `reviewed`/`go-pending-approval`. Read their status on disk before editing.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals. Measured at review: `1 failed, 5919 passed, 3 skipped, 2 xfailed`, the failure being the ENVIRONMENTAL `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which scans the working tree and trips over 189 untracked `opencode-recovery/*.md` files belonging to another party. It is NOT the `test_orchestrator_retirement` failure this plan names; that module gives `112 passed`. Do not quote these figures, and do not delete those untracked files to go green.

## Findings

| Id | Severity | Location (F-1..F-8 re-measured at review HEAD `34c26b95`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | OBSOLETE | `oc_runipd.py:6579-6586`, `:6600-6604`; agy `:3636-3640` | THE ITEM'S CENTRAL DEFECT IS FIXED. The verify prompt and the child launch both receive the RE-RESOLVED path, fixed at `1549c018` (authored 2026-08-27 22:42:41 -0400 = 2026-08-28 02:42:41 UTC), two days BEFORE the item was filed (2026-08-30 02:02 UTC, commit `f4a1b5d8`, which the item itself now records). | `git log` on the fix; source read at both hosts; commit timestamps |
| F-2 | OBSOLETE | 140 run directories | All 23 `File not found` verifier logs are in three runs created 2026-08-25T03:51Z (13), 2026-08-25T10:58Z (3), 2026-08-28T00:29Z (7), every one BEFORE the fix. RE-SCANNED AT REVIEW with the corpus grown (140 dirs, 58 verify logs, 35 outcome files): still exactly 23, same distribution, and 105 runs were created AFTER the fix with ZERO occurrences. | scanned every `sessions/*verify*` across all runs and partitioned by run-id timestamp against the fix time |
| F-3 | OBSOLETE | `tests/test_oc_runipd.py` | The item's requested test (d) ALREADY EXISTS and passes: `VerifierPromptTests::test_resolve_plan_path_handles_transition_to_executed`, shipped in the same commit as the fix. | re-run at review: `1 passed` |
| F-4 | HIGH | `oc_runipd.py:6645`, `:6647`, `:6649`; agy `:3696`, `:3698`, `:3700` | `verify_disp` is set to `"unverified"` for THREE materially different facts (unparseable JSON, no outcome file at all, turn killed) with three different remedies, indistinguishable in the record. | source read, both hosts |
| F-5 | HIGH | `oc_runipd.py:6583-6584`, agy `:3639-3640` | `except DriverError: current_plan_path = plan_path` still SILENTLY substitutes a known-stale path when re-resolution fails. The happy path was fixed; the error path was not. | source read, both hosts |
| F-6 | MED | `oc_runipd.py:3740` | An `unverified` turn already does not auto-merge and its lane is preserved, so this plan changes the RECORD rather than the gate, which is why it is small. SEE F-11 for the limit of that guarantee. | source read of `integration_is_earned` |
| F-7 | MED | `run_state.py:28-36`; both drivers | A verification state vocabulary exists and neither driver imports it, so a fourth ad-hoc vocabulary is a real risk. MEASURED: it has NO token for any of this plan's three facts (its full set is `pending, runnable, running, performed, blocked, failed, verifying, verified, correction_required, cancelled, complete`), so the gap E-01 was told to check for is confirmed. | AST walk, zero matches in both drivers; enumerated the tokens in-process |
| F-8 | LOW | backlog `t74o5q` | The item's ordering advice ("fix this first, it fired 23 times") is obsolete, and its claim that "the resolved value is not what reaches the CHILD PROCESS" was true before `1549c018` and is false at HEAD. | F-1, F-2 |
| F-9 | HIGH | this plan versus siblings `1bfppy` and `bxx9af` | **THREE PLANS IN THIS SET EDIT THE SAME FIFTEEN-LINE BLOCK AND THIS PLAN COORDINATES WITH ONLY ONE.** `1bfppy` (verdict mapping) owns the `except` unparseable arm that this plan's E-01/E-02 also name; `bxx9af` (evidence consumption) adds a predicate and possibly a new `verification_status` token to the same region and declares `- Item-Dependencies: executed:1bfppy`. Both are `reviewed`/`go-pending-approval`. This plan names only `1bfppy` and only in prose, so a set-intersection check against one sibling would still let two plans name the same condition. | read all three plans' E-items and front matter |
| F-10 | HIGH | `runner_stop.py:1527`, `:1482`; `oc_runipd.py:5223`, `:6373`, `:6649` | **THE INTERRUPT SITE IS NOT COVERED BY THE INDETERMINATE MACHINERY, WHICH RESOLVES OQ-01 AND INVERTS ITS LEAN.** `is_indeterminate` reads `item["stopped"]["certainty"]`, and that record is written only by the EXECUTE turn's forced/deliberate stop paths. The verify `except (KeyboardInterrupt, StallTimeout)` SWALLOWS the exception and writes no `stopped` record, so the predicate returns False. So the site is unprotected and labelling it is legitimate, but spec `c4gd2h` R22 still forbids fabricating a disposition, which means the correct label is unknown-outcome, NOT a verification failure. | read the predicate, the record builder and every `stopped` writer |
| F-11 | MED | `integration_is_earned`; `oc_runipd.py:3045`, `agy_runipd.py:2047` | **THE "ALREADY DOES NOT AUTO-MERGE" GUARANTEE IS CONDITIONAL AND HOST-DEPENDENT.** Called the real predicate: with `validate=True` every non-`verified` token refuses, but the validation-OFF branch never reads `verify_disp`, so with a passing suite a novel token still gives `earned=True signal=driver-run-suite`. oc defaults `validate` FALSE; agy defaults its verifier ON. E-02 asserts the guarantee unconditionally. | executed the predicate on both paths with four tokens |
| F-12 | MED | `run_viewer.py:1350-1360`, `:1617-1631` | **A NEW TOKEN RENDERS AS A BARE `-` IN `aw runs`**, which is exactly how "no verification ran" renders, inverting this plan's purpose. Two branches match literal values (`verified`/`failed`, then `verified` -> `yes`, `(unverified, verify-failed, failed)` -> `no`, else `-`). `run_viewer.py` is NOT in this plan's `Scope-Paths`. | source read of both branches |
| F-13 | MED | `oc_runipd.py:6716-6721`, agy `:3766-3771` | **THE SILENT-FALLBACK SHAPE OCCURS TWICE PER HOST.** An identical `except DriverError: current_plan_for_finalize = plan_path` guards the FINALIZE re-resolution ~130 lines below the verify one. Different consumer, so out of scope, but fixing one while an identical hole sits nearby should be stated rather than hidden. | source read, both hosts |
| F-14 | LOW | `tests/test_agy_runipd_cli.py` | **NO AGY TWIN OF THE `1549c018` REGRESSION EXISTS**, which resolves OQ-02: that file contains ZERO occurrences of `resolve_plan_path`. Adding one is in scope, and is more clearly warranted than the question implied because E-03 edits that exact agy fallback. | grep of the agy test module |
| F-15 | LOW | `tests/test_runner_refork_guard.py:161-167`, `:265`, `:287`, `:316`, `:336` | E-05 is cheaper than written and one premise is wrong: three of the module's tests fire from one well-formed row, but `test_the_table_covers_both_runners` asserts only that the TABLE covers both runners (which it already does), so it will not verify the new row lists both. | source read |
| F-16 | LOW | `tests/test_reporting_contract.py` | The stated suite baseline is stale in both halves: measured `1 failed, 5919 passed, 3 skipped, 2 xfailed`, and `test_orchestrator_retirement` now gives `112 passed`. The one failure is environmental, caused by 189 untracked `opencode-recovery/*.md` files belonging to another party in this shared checkout. | bare `python3 -m pytest`; module re-run alone |

## Proposed changes (ordered, validatable)

1. E-01 names the three collapsed facts in `runner_shared.py`, stating the confirmed `run_state` gap and proving no overlap with EITHER sibling's names.
2. E-02 writes the distinguished fact at all six sites, reports the never-ran case as a hard failure and the interrupt case as unknown-outcome, changes no gate, and states the validation-OFF limit rather than overclaiming.
3. E-03 makes the verify stale-path fallback refuse with a named recorded reason, states when it can fire, and reports the twin finalize fallback without touching it.
4. E-04 tests all three facts and the refusal per host from fixtures, pastes the existing `1549c018` regression as evidence the dead half is dead, and ADDS the agy twin (measured absent).
5. E-05 pins the sharing symmetrically and mutation-checks the guard, reverting cleanly.

## Deferred / out of scope (with reason)

- NOT GRADUATED AS OBSOLETE, and recorded in the backlog item itself rather than only here: the item's fix (1) (pass the plan by stable id / re-resolve before launch) and its tests (a), (c) and (d). All were delivered by `1549c018` on 2026-08-28, before the item was written, and the regression test ships with it and passes. Re-implementing them would be work an existing commit already declares.
  - Carrier-Declined: DELIVERED, not deferred. Commit `1549c018` shipped fix (1) on 2026-08-28 and its regression test (`tests/test_oc_runipd.py::VerifierPromptTests::test_resolve_plan_path_handles_transition_to_executed`) passes today, re-run at execution (`1 passed`). An obligation that an existing commit already discharges is not outstanding work, and filing a carrier would assert work that is done.
- THE ITEM'S FIX (2) (order the turn so verification happens BEFORE the plan is moved, or have the mover publish the new path back). NOT graduated, deliberately. `1549c018` solved the same problem by re-resolution, so reordering now is a second solution to a solved problem, and it would reach into the `driver_begin`/`driver_finalize` transaction (`oc_runipd.py:894`, `:976`), which has its own receipt and scope-reconciliation gates. If a future defect shows re-resolution is insufficient, reordering is the right response then.
  - Carrier-Declined: DECIDED AGAINST on the merits, not postponed. `1549c018` solved the same problem by re-resolution, so reordering the `driver_begin`/`driver_finalize` transaction would be a second solution to a solved problem with real blast radius on its receipt and scope-reconciliation gates. There is no residual work to carry; if a future defect shows re-resolution insufficient, that defect is the trigger and reordering is its response.
- THE VERDICT MAPPING for a verdict that WAS written: sibling plan `1bfppy` (`reviewed`, `go-pending-approval`). That plan owns the fail-closed table AND the `except` unparseable arm; this one owns the absence of a verdict, the interrupt label and the stale-path refusal. Adjacent lines, separate concerns, but NOT cleanly separable on the `except` arm: see F-9 and E-01/E-02, which now require reading both siblings on disk.
  - Carrier-Declined: DISCHARGED BY A SIBLING THAT HAS LANDED. `1bfppy` is `- Status: executed` in `.aw/records/plans/executed/` (read on disk at validation), and its table, its `except` arm and its refusal wording are all present in this tree. Nothing is outstanding.
- THE MODEL AND RATE-CARD RECORD: sibling plan `w33lrl` (from backlog `vlf75p`). VERIFIER EVIDENCE NEVER CONSUMED: sibling plan `bxx9af` (from backlog `rbftpl`, `reviewed`/`go-pending-approval`, which declares `- Item-Dependencies: executed:1bfppy` and may add its own `verification_status` token to this same block).
  - Carrier: bxx9af
- THE TWIN SILENT FALLBACK AT THE FINALIZE SITE (F-13). Same shape, different consumer (`aw ipd finalize` rather than the verifier launch), so out of this plan's fix (4). Identified and reported by E-03 rather than fixed. CARRIER: backlog `rfhiu2` (`.aw/records/backlog/open/20260922-rfhiu2-01-rfhiu2-finalize-stale-plan-path-fallback.backlog.md`), filed at execution, so this does NOT vanish when this plan reaches `executed`. Classified `followup` rather than `bug` because no occurrence was measured (the verify-side twin had 23; this is a hazard read from source), with the reclassification trigger recorded in the item.
  - Carrier: rfhiu2
- EXTENDING `run_viewer.py`'s TWO LITERAL-MATCHING BRANCHES (F-12). Out of scope because `run_viewer.py` is not declared, which CONSTRAINS E-02's token choice rather than being a free deferral: either reuse a token those branches recognize, or declare the path with a `--scope-reason`.
  - Carrier-Declined: RESOLVED BY THIS PLAN'S TOKEN CHOICE rather than deferred, which is what the row itself says it constrains. E-02 reused `unverified` (measured rendering `no`, not `-`), so no `run_viewer.py` change is owed and the path was deliberately NOT added to `Scope-Paths`. The three-way distinction rides on the refusal record, which `r2i1b1` already renders in both surfaces. Sibling `bxx9af` carries the question for its own novel token if it picks one.
- CHANGING WHETHER THE VERIFIER TURN RUNS. The `validate` default and its per-host resolution belong to pending plans `tm2cz8`/`ybkmzp` (`hostdefault`) and `kgpptv` (`runprofile` Order 06).
  - Carrier-Declined: NOT THIS PLAN'S SUBJECT AND ALREADY OWNED. The `validate` default belongs to pending plans `tm2cz8`/`ybkmzp` (`hostdefault`) and `kgpptv` (`runprofile` Order 06), each a live carrier of its own; naming it here bounds this plan's scope rather than incurring a debt.
- ADDING A NEW REFUSAL BEYOND THE STALE-PATH ONE. The integration gate already refuses correctly; a second refusal on top would be redundant and could strand work the existing gate handles.
  - Carrier-Declined: AN EXPLICIT NON-GOAL, and E-02 measured why. `integration_is_earned` already refuses every non-`verified` token on the validation-ON path (pasted in V-02), so a second refusal would be redundant and could strand work the existing gate handles correctly. Nothing outstanding.

## Scope check

- Over-scope: `runner_shared.py` is in scope ONLY to hold the named facts. Do NOT edit `run_state.py`, `verify_roles.py`, `runner_stop.py` or the `driver_begin`/`driver_finalize` transaction. Do NOT change `integration_is_earned`. Do NOT re-fix the prompt path. Do NOT fix the twin finalize fallback (F-13).
- Under-scope: stated rather than left as `none`. The distinguished facts are recorded and reported to a human but are NOT made machine-readable in `--json`/`--agent` (that surface belongs to plan `r2i1b1`, now `approved`, whose E-03 must first extract five duplicated predicate copies). A rejected or never-run turn is also NOT requeued; that is sibling `1bfppy`'s OQ-01, which its own review resolved as leaving no spec gap. The `aw runs` rendering of any new token is also not improved here, which is why E-02 must pick a token that already renders (F-12).

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS not totals. Cases belong in `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py`; the sharing guard in `tests/test_runner_refork_guard.py`. Fixtures, never the gitignored live run tree. `tests/test_oc_runipd.py::VerifierPromptTests::test_resolve_plan_path_handles_transition_to_executed` must keep passing untouched: it is the existing regression for the already-fixed half and this plan must not disturb it.
ALSO RUN `python3 -m pytest tests/test_runner_stop_triggers.py tests/test_runner_refork_guard.py tests/test_runner_shared.py` EXPLICITLY and paste it. The first is included because E-02 touches the interrupt classification and the indeterminate contract lives in `runner_stop`, so an accidental interaction with the stop machinery shows up there as a named failure rather than as a node-id diff to interpret.

## Spec / documentation sync

Spec `25kzda` (`.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`, `- Status: approved`) governs verification, and this plan moves the code TOWARD it rather than amending it, so no spec file is declared in `- Scope-Paths:`. The relevant approved text, quoted rather than paraphrased and CORRECTED at review: §4.2's `RUN-FRESH-VERIFIER` row (`:648`) inspects the "Verifier session ID, parentage, packet digest, verifier findings envelope", its pass criterion is that the "Verifier used a fresh session with no executor-session inheritance and addressed the frozen predicates", its failure message is `[RUN-FRESH-VERIFIER] <item> has no valid independent verification attempt`, and its action is `RETRY, then FAIL ITEM`. NOTE the "valid evidence-linked envelope" phrase this plan attributed to the row is actually `RUN-HOST-ATTEMPT`'s wording, not this row's. The row does describe the never-ran case this plan names, and it already calls it a failure, so recording it as one needs no amendment.
THE RETRY QUESTION IS ANSWERED RATHER THAN LEFT TO THE EXECUTOR. §4.1 (`:586`) defines the RETRY action as "enter `correction_required`, issue a bounded correction packet, and retry the checker while the frozen retry budget remains", and a retry mechanism does not exist in either driver: `resolve_retry_budget` is called once per host and frozen into run options, but neither driver ever reads `options["retry_budget"]` back (measured, zero occurrences). So implementing the spec's retry would mean BUILDING the retry loop, which is plainly outside a labelling plan. Recording the failure without retrying is therefore an honest partial implementation of the row, not a violation to escalate; state it that way and do not open a maintainer question about it.
ONE THING STILL TO CHECK: the spec quotes operator-facing recovery strings verbatim, so if this plan's new reason text collides with one, reflect it. Do NOT edit §4.2's finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, and the spec says so in prose above the table (`:634-638`), so editing a cell IS a code change.

## Open questions

### OQ-01: Does the interrupt site belong in the three-fact split at all, or is it already owned by the indeterminate machinery?

- Blocking: no
- Status: resolved
- Owner: this plan's executor (to apply the resolution; the reading itself is done)
- Resolution or deferral rationale: RESOLVED AT REVIEW BY READING THE CODE, and the answer inverts the question's lean. THE MACHINERY DOES NOT REACH THIS SITE. `runner_stop.is_indeterminate` (`runner_stop.py:1527`) reads `item["stopped"]["certainty"]` and nothing else; that record is built only by `runner_stop.forced_stop_disposition`/`stopped_disposition` (`:1482`) and written only on the EXECUTE turn's stop paths (`oc_runipd.py:5223` inside `_record_deliberate_stop`, `:6373` calling `_record_forced_stop`, and `:7166`). The verify-turn handler at `oc_runipd.py:6649` SWALLOWS `KeyboardInterrupt`/`StallTimeout` and writes no `stopped` record at all, so `is_indeterminate` returns False for a killed verify turn and every level-4 gate passes over it.
  SO THE SITE IS UNPROTECTED AND BELONGS IN THE SPLIT, which is the opposite of "leave it alone because it is already covered". BUT spec `c4gd2h` R22's prohibition on fabricating a disposition applies with FULL force precisely because nothing else is asserting one: the driver did not observe where the verify turn was cut, so the honest label is INDETERMINATE or "interrupted, outcome unknown", NOT a verification failure. E-02 now carries that instruction directly.
  WHAT REMAINS FOR THE EXECUTOR is only to apply it and paste the reading, not to decide it. Note the plan's citation for `reconcile_interrupted` was stale (`:6782`; it is `:6995` at review), which does not change the conclusion since that function reads the same `stopped` record.

### OQ-02: Does an agy twin of the `1549c018` path regression exist, and if not is adding one in scope?

- Blocking: no
- Status: resolved
- Owner: this plan's executor (to write the twin; the question itself is answered)
- Resolution or deferral rationale: RESOLVED AT REVIEW BY GREP: NO TWIN EXISTS. `tests/test_agy_runipd_cli.py` contains ZERO occurrences of `resolve_plan_path` and no analogue of `test_resolve_plan_path_handles_transition_to_executed`, which `1549c018` added to `tests/test_oc_runipd.py` only. ADDING ONE IS IN SCOPE, and the case is stronger than the question implied: `resolve_plan_path` is SHARED (`runner_shared.py:1433`) so the resolution logic is covered once, but each host has its OWN call site and its OWN `except DriverError` fallback, a shared function does not prove a call site passes its result onward, and E-03 EDITS that exact agy fallback. Shipping an edit to an untested call site is the gap this closes. E-04 now states the twin is required rather than conditional.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the named fact set as written and its location in `runner_shared.py`. Paste the annotation at each of the six write sites. State whether `run_state.py`'s existing vocabulary was consumed and for which facts; since it was measured at review to have NO token for any of the three, confirm that and justify each name you minted rather than asserting a gap you did not re-check. Paste BOTH siblings' `- Status:` lines and directories read at validation time (`1bfppy` AND `bxx9af`), and paste proof this plan's names do NOT overlap either one's (two set intersections, each printed empty).
  - Observed evidence: THE NAMED FACT SET, in `agent_workflows/runner_shared.py` immediately after `verdict_refusal_text` (the verdict block's last symbol), under the banner `WHY THERE WAS NO VERDICT TO MAP (runverdict-06, fzxfph)`. Four codes plus one accessor, verified in-process:
    ```
    $ python3 -c "from agent_workflows import runner_shared as rs; print(rs.VERIFY_ABSENCE_CODES)"
    ('verifier-verdict-unreadable', 'verification-never-recorded', 'verification-interrupted', 'verification-not-attempted')
    ```
    FOUR FACTS, NOT THREE, and the fourth is E-03's rather than an invention: `VERIFY_ABSENCE_PLAN_UNRESOLVABLE` is a distinct fact from `..._NO_OUTCOME_FILE` on a distinction an operator acts on differently (there a verifier ran and produced nothing, so re-run it; here no verifier ran at all because the runner could not say which plan to verify, so find the plan first).
    THE WRITE SITES ARE FOUR, NOT SIX, AND THAT IS A TREE CHANGE RATHER THAN A SHORTFALL. The plan says "six sites across two files"; `execute_item` was unified into `runner_shared.execute_item_core` by commit `70a2059f`, so the per-host duplication the plan counted no longer exists. Annotated sites, `grep` at validation time:
    ```
    $ grep -n 'attempt\["verify_absence"\]\|item\["verify_absence"\]' agent_workflows/runner_shared.py
    18525:                attempt["verify_absence"] = VERIFY_ABSENCE_PLAN_UNRESOLVABLE
    18526:                item["verify_absence"] = VERIFY_ABSENCE_PLAN_UNRESOLVABLE
    18629:                            attempt["verify_absence"] = (
    18632:                            item["verify_absence"] = VERIFY_ABSENCE_VERDICT_UNREADABLE
    18672:                        attempt["verify_absence"] = VERIFY_ABSENCE_NO_OUTCOME_FILE
    18673:                        item["verify_absence"] = VERIFY_ABSENCE_NO_OUTCOME_FILE
    18737:                    attempt["verify_absence"] = VERIFY_ABSENCE_TURN_INTERRUPTED
    18738:                    item["verify_absence"] = VERIFY_ABSENCE_TURN_INTERRUPTED
    ```
    `run_state.py` WAS RE-MEASURED AND NOT CONSUMED, FOR NO FACT. The review's finding reproduces exactly:
    ```
    $ python3 -c "from agent_workflows import run_state; print(run_state.ALL_STATES)"
    frozenset({'complete', 'verified', 'failed', 'performed', 'correction_required', 'runnable', 'cancelled', 'verifying', 'running', 'blocked', 'pending'})
    ```
    No token for "never ran", none for "unparseable", none for "interrupted". JUSTIFICATION FOR MINTING RATHER THAN BINDING, which is the argument the item asked for and not merely the gap: `run_state`'s tokens name WHERE AN ITEM SITS in its lifecycle, while these name WHY ONE TURN PRODUCED NO VERDICT, which is a property of a turn and not a state an item occupies. Binding `failed` here would assert the ITEM failed when only its verification did. And no fourth parallel enum was added: nothing dispatches on these codes, `verify_disp` keeps its existing three-value contract untouched, and each code exists to be READ by a human through the refusal record that already renders.
    ONE NAME WAS DELIBERATELY *NOT* MINTED. `VERIFY_ABSENCE_VERDICT_UNREADABLE` is an ALIAS (`= VERDICT_REFUSAL_CODE_UNREADABLE`), not a new string, so the closed set covers all four facts without spelling one fact twice:
    ```
    fact 1 code IS 1bfppy's object  : True (alias, so it cannot drift)
    ```
    This is the honest reconciliation of `1bfppy`'s in-tree note, which said it left "a free field to name". It needed no new name: a verdict that WAS written belongs to the verdict table by construction.
    BOTH SIBLINGS READ ON DISK AT VALIDATION TIME:
    ```
    $ grep -n "^- Status:" .aw/records/plans/executed/20260908-runverdict-05-1bfppy-*.ipd.md .aw/records/plans/pending/20260908-runverdict-05-bxx9af-*.ipd.md
    .../executed/20260908-runverdict-05-1bfppy-...ipd.md:17:- Status: executed
    .../pending/20260908-runverdict-05-bxx9af-...ipd.md:10:- Status: approved
    ```
    So `1bfppy` HAS LANDED (directory `executed/`, and its code is present in this tree: `map_verdict`, `verdict_refusal_text` and the `except` arm are all in place), which is a change from the plan's authoring assumption that it had not. Its names are therefore authoritative for its cases and this plan covers only what remains. `bxx9af` is `approved` and still in `pending/`, so NOT landed.
    TWO SET INTERSECTIONS, EACH PRINTED EMPTY:
    ```
    names THIS plan mints          : ['verification-interrupted', 'verification-never-recorded', 'verification-not-attempted']
    1bfppy's names (landed)         : ['BLOCKED', 'CONFORMING', 'CORRECTION_REQUIRED', 'NOT CONFORMING', 'VERIFIED', 'blocked', 'unverified', 'verified', 'verifier-declined', 'verifier-verdict-unreadable']
    intersection vs 1bfppy          : [] <- EMPTY
    bxx9af candidate token (pending): ['unevidenced']
    intersection vs bxx9af          : [] <- EMPTY
    ```
    (`bxx9af`'s candidate token is read from its own OQ-02, which recommends `unevidenced` conditionally; since that plan has not executed, the check is against its declared candidate.)
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste, for each of the three facts, the recorded value in a real `state.json` queue entry, showing three DISTINCT values where there was one. Paste the PRE-FIX contrast showing all three were previously identical. Paste `integration_is_earned`'s refusal for a never-ran turn and proof the lane is preserved, AND paste the MEASURED validation-OFF result for the same token (call the real predicate) showing it does NOT refuse there, so the record states the guarantee's true boundary rather than an unconditional claim. Confirm OQ-01's resolution by pasting your own reading that the verify site writes no `stopped` record, and confirm the interrupt case is labelled unknown-outcome and NOT a failure. Paste the chosen token's rendering in `run_viewer.py`'s two literal-matching branches, showing it is not a bare `-`; if it is, state which token you reused instead or why the path was declared.
  - Observed evidence: THE RECORDED VALUES, from driving the REAL `agy_runipd.execute_item` once per fact (not from calling the vocabulary directly), each on a throwaway git repo with a conforming plan, the execute turn faked and the VERIFY turn made to produce each condition:
    ```
    === FACT 1: verdict written but UNPARSEABLE
      verification_status : 'unverified'
      verify_absence      : 'verifier-verdict-unreadable'
      status              : 'partial'
      refusal.code        : 'verifier-verdict-unreadable'

    === FACT 2: NO outcome file at all
      verification_status : 'unverified'
      verify_absence      : 'verification-never-recorded'
      status              : 'partial'
      refusal.code        : 'verification-never-recorded'
      refusal.reason      : the verifier turn produced NO outcome file, so there is no verdict at all: this turn is recorded a verification FAILURE, not an inconclusive one. Noth...

    === FACT 3: verifier turn KILLED (StallTimeout)
      verification_status : 'unverified'
      verify_absence      : 'verification-interrupted'
      status              : 'partial'
      refusal.code        : 'verification-interrupted'
      refusal.reason      : the verifier turn was INTERRUPTED before it wrote a verdict, so the outcome of verification is UNKNOWN. This is deliberately NOT recorded as a verific...

    === FACT 4: plan UNRESOLVABLE (E-03)
      verification_status : 'unverified'
      verify_absence      : 'verification-not-attempted'
      status              : 'partial'
      refusal.code        : 'verification-not-attempted'
      refusal.reason      : verification was NOT ATTEMPTED because this item's plan file could not be re-resolved (agy001: Cannot locate IPD agy001; configured path was .aw/recor...
    ```
    THE PRE-FIX CONTRAST, which is what makes the four distinct values mean something:
    ```
    pre-fix, all four recorded: 'unverified' / 'unverified' / 'unverified' / 'unverified'
    post-fix verify_absence  : ['verifier-verdict-unreadable', 'verification-never-recorded', 'verification-interrupted', 'verification-not-attempted']
    distinct values          : 4
    ```
    NOTE WHAT DID *NOT* CHANGE, deliberately: `verification_status` is still `'unverified'` in all four rows. That is the token decision below, not an oversight.
    THE INTEGRATION GATE IS UNCHANGED, measured by CALLING the real predicate rather than reasoning about it:
    ```
    ONE shared predicate: True          # oc.integration_is_earned is agy.integration_is_earned

    --- validation ON (agy's shipped default; oc under --validate)
      verify_disp='verified'   earned=True  signal=verifier
      verify_disp='unverified' earned=False signal=verifier-declined
      verify_disp='blocked'    earned=False signal=verifier-declined
      verify_disp=None         earned=False signal=verifier-declined

    --- validation ON, verdict absent (the never-ran case) + GREEN SUITE
      earned=False signal=verifier-declined
      detail=validation is ON and the verifier did not verify (verification='unverified'); a green suite deliberately does NOT override an explicit verifier verdict
    ```
    So a never-ran turn refuses integration and its lane is preserved (`status` is `partial`, which `item_reached_success` excludes for the `execute` action: measured `rs.item_reached_success({'status':'partial','action':'execute'})` -> `False`, against a success bar of `frozenset({'executed','approved'})`). NO SECOND REFUSAL WAS ADDED on top of it.
    THE GUARANTEE'S TRUE BOUNDARY, stated rather than overclaimed, measured on the same predicate:
    ```
    --- validation OFF (oc's shipped default): THE LIMIT, verify_disp is NOT READ
      verify_disp='unverified'                     earned=True  signal=driver-run-suite
      verify_disp='verification-never-recorded'    earned=True  signal=driver-run-suite
      verify_disp=None                             earned=True  signal=driver-run-suite
    ```
    The validation-OFF branch never reads `verify_disp` at all, so with a passing driver-run suite an item still integrates regardless of token. oc defaults `validate` FALSE and agy defaults its verifier ON, so the "does not auto-merge" guarantee holds on agy's default and on oc only under `--validate`. This plan improves the RECORD, not the gate.
    OQ-01 CONFIRMED BY MY OWN READING, not by citing the review. AST-walked `execute_item_core` and listed what each `except StallTimeout:` handler assigns:
    ```
    VERIFY-BLOCK handler `except StallTimeout:` at line 18705 assigns:
        (v_reason, v_remedy)
        attempt['verify_absence']
        item['verify_absence']
        verify_disp
        disposition
      does its body mention 'stopped'? -> False

    is_indeterminate({no stopped record}) = False
      -> the level-4 machinery does NOT see a killed verify turn. OQ-01 confirmed by reading.
    ```
    (For contrast the EXECUTE turn's own `except StallTimeout:` at line 18325 also writes no `stopped` record; the records `is_indeterminate` reads come from `_record_forced_stop`/`_record_deliberate_stop` on the deliberate-stop paths.) So the site is UNPROTECTED and labelling it is legitimate.
    THE INTERRUPT CASE IS LABELLED UNKNOWN-OUTCOME AND NOT A FAILURE, which is spec `c4gd2h` R22 applied:
    ```
    $ python3 -m pytest tests/test_oc_runipd.py -o addopts="" -q -k "VerificationAbsence"
    6 passed, 237 deselected
    ```
    including `test_the_never_ran_case_is_a_failure_and_the_killed_case_is_not`, which asserts `FAILURE` appears in the never-ran reason, `UNKNOWN` in the killed one, and `FAILURE` does NOT appear in the killed one. No `stopped` record is minted from a verify-turn stall either, on purpose: that record is the EXECUTE turn's contract with the resume/reconcile gates, and writing one would tell them the ITEM was cut mid-flight when only its verification was.
    THE TOKEN CHOICE, AND IT IS A REUSE RATHER THAN A NOVEL TOKEN. Exercised `run_viewer`'s literal-matching branch on the value the runner actually writes:
    ```
      verification_status='verified'                       -> 'yes'
      verification_status='unverified'                     -> 'no'
      verification_status='verification-never-recorded'    -> '-'
    ```
    A NOVEL TOKEN WOULD RENDER AS A BARE `-`, which is exactly how "no verification ran" already renders and is the inverse of this plan's purpose. So `verify_disp` KEEPS `unverified` (rendering `no`), `run_viewer.py` was NOT added to `Scope-Paths`, and the three-way distinction rides on the REFUSAL record plus the new `verify_absence` field. That routing is not new surface: `r2i1b1` already plumbed refusals into the run summary's diagnostics block and `aw runs`' `Issue` column, and `tests/test_oc_runipd.py::VerificationAbsenceTests::test_the_refusal_is_recorded_where_aw_runs_already_reads_it` asserts every one of the four codes round-trips through the shared `refusal_of_item` reader.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the refusal as written and the ACTUAL output when a plan cannot be re-resolved, showing it names the reason and does NOT launch a child. Paste the constructed test case that makes `resolve_plan_path` raise, and state which real-world condition it represents. Paste proof no child process was launched (assert on the argv or the absence of a session log, not on prose). Paste the twin finalize fallback (`current_plan_for_finalize`) as you found it and confirm it is UNCHANGED, so the deliberate limit is on the record rather than implied.
  - Observed evidence: THE REFUSAL AS WRITTEN. The `except DriverError:` arm in `runner_shared.execute_item_core` no longer assigns `current_plan_path = plan_path`; it sets `current_plan_path = None`, records the refusal, and the verifier launch is now guarded by `if current_plan_path is not None:`:
    ```
    current_plan_path = None
    try:
        current_plan_path = resolve_plan_path(
            plan_repo, item.get("configured_file", ""), item["id6"]
        )
    except DriverError as exc:
        v_reason, v_remedy = verify_absence_text(
            VERIFY_ABSENCE_PLAN_UNRESOLVABLE,
            plan_hint=f"{item['id6']}: {exc}",
        )
        record_refusal(
            item,
            code=VERIFY_ABSENCE_PLAN_UNRESOLVABLE,
            reason=v_reason,
            remedy=v_remedy,
        )
        attempt["verify_absence"] = VERIFY_ABSENCE_PLAN_UNRESOLVABLE
        item["verify_absence"] = VERIFY_ABSENCE_PLAN_UNRESOLVABLE
        verify_disp = VERIFY_DISP_UNVERIFIED
        disposition = "partial"
        print(pal(f"  ! IPD {item['id6']} {v_reason}", "yellow"), file=sys.stderr)
        print(pal(f"    -> {v_remedy}", "yellow"), file=sys.stderr)
    if current_plan_path is not None:
        ...build the prompt and launch the verifier...
    ```
    THE ACTUAL OUTPUT, from driving the real `agy_runipd.execute_item`:
    ```
      ! IPD agy001 verification was NOT ATTEMPTED because this item's plan file could not be re-resolved (agy001: Cannot locate IPD agy001; configured path was .aw/records/plans/pending/20260828-demo-01-agy001-demo.ipd.md), so the runner could not say which plan to verify. It deliberately did NOT fall back to the path it captured earlier in the turn: that path is known to go stale (a self-finalizing plan MOVES out of `pending/` mid-turn) and verifying against a stale path is how a verifier turn comes to report on a file that no longer exists
        -> locate the plan by its id6 with `aw find plans <id6>` and check it exists exactly once: this refusal means the id6 matched ZERO files or MORE THAN ONE. A single match that the runner could not see usually means the lane worktree does not contain the plan. Resolve that, then re-run the VERIFICATION for this item; the lane is PRESERVED and nothing was merged
    ● IPD 01/1 agy001 (execute) -> partial  (exit 0)
    ```
    PROOF NO CHILD WAS LAUNCHED, asserted on the launcher call log and the absent artifacts, not on prose. The fake launcher appends one entry per child process it is asked to spawn:
    ```
    LAUNCHER CALL LOG (each entry is one child process): ['execute']
      'verify' present?           False <- FALSE means NO verifier child was launched
      verify prompt file written? False
      verify session log exists?  no sessions/ dir at all
      recorded verify_absence   : verification-not-attempted
      recorded refusal.code     : verification-not-attempted
    ```
    For contrast, the same harness on the three other facts logs `['execute', 'verify']` and prints a `▶ Verifying agy001 (...)` line; across the four-fact run that line appears exactly 3 times (`grep -c "Verifying agy001"` -> `3`), the missing one being this case.
    THE CONSTRUCTED CONDITION AND WHAT IT REPRESENTS. The plan file is deleted DURING the execute turn, so the path captured at launch is stale and `resolve_plan_path` matches zero files:
    ```
    DriverError: Cannot locate IPD agy001; configured path was .aw/records/plans/pending/20260828-demo-01-agy001-demo.ipd.md
    ```
    REAL-WORLD CONDITION: a plan that is deleted or moved out from under the runner mid-turn, and equivalently A LANE WORKTREE THAT DOES NOT CONTAIN THE PLAN, which is this runner's own default execution shape (`isolate_worktree` defaults on). Breaking it BEFORE the turn instead would raise at an earlier call site, which is a different defect and not the one E-03 fences; the harness comment records that choice. `resolve_plan_path` raises only on zero or multiple matches, so the three producible conditions are: plan deleted/moved mid-turn (constructed here, and asserted in both committed test files), an id6 collision across two files, and a lane worktree missing the plan. The committed per-host cases are `tests/test_oc_runipd.py::VerificationAbsenceTests::test_an_unresolvable_plan_refuses_and_does_not_launch_a_verifier` and `tests/test_agy_runipd_cli.py::AgyVerificationAbsenceTests::test_an_unresolvable_plan_raises_rather_than_returning_a_stale_path`, both of which build the lane-worktree form.
    THE TWIN FINALIZE FALLBACK, FOUND AND DELIBERATELY UNCHANGED (F-13). As it stands in the tree at validation time:
    ```
    $ sed -n 19448,19456p agent_workflows/runner_shared.py
                    finalize_repo = Path(work_dir)
                    try:
                        current_plan_for_finalize = resolve_plan_path(
                            finalize_repo, item.get("configured_file", ""), item["id6"]
                        )
                    except DriverError:
                        current_plan_for_finalize = plan_path
    ```
    Byte-identical in shape to the verify one this plan fixed, and there are TWO such sites (the second at `:19653`). CONFIRMED UNCHANGED: the only reference to `current_plan_for_finalize` in this plan's diff is inside the new explanatory COMMENT, never in code:
    ```
    $ git diff a0618dbe~1 a0618dbe -- agent_workflows/runner_shared.py | grep -B2 -A2 "current_plan_for_finalize"
    +            # THE TWIN FALLBACK AT THE FINALIZE SITE IS DELIBERATELY LEFT ALONE. An identical
    +            # `except DriverError: current_plan_for_finalize = plan_path` guards the FINALIZE
    +            # re-resolution further down this same function (search `current_plan_for_finalize`). It is
    ```
    (Both matched diff lines are `+` comment lines; no `-` line touches that code.) It feeds `aw ipd finalize` rather than a verifier launch, so it has a different consumer and a different failure model, and fixing it is out of this plan's fence. NOT LOST: filed as backlog `rfhiu2` (`20260922-rfhiu2-01-rfhiu2-finalize-stale-plan-path-fallback.backlog.md`), classified `followup` rather than `bug` because no occurrence was measured, with the reclassification trigger written into the item.
    THE SELF-FINALIZE SEQUENCE IS UNTOUCHED: no reordering of `driver_begin`/`driver_finalize` appears in the diff, which is the plan's fix (2) staying deliberately not-graduated.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the new tests and their actual runner output, per host. Paste `tests/test_oc_runipd.py::VerifierPromptTests::test_resolve_plan_path_handles_transition_to_executed` PASSING, as the evidence that the item's dead half is genuinely dead. Paste the AGY TWIN passing: it was measured ABSENT at review, so a V-04 without it is incomplete rather than optional. Paste the pre-fix contrast for each of the three facts. Paste proof no test reads `.aw/records/runs/`.
  - Observed evidence: THE OC HOST, `tests/test_oc_runipd.py::VerificationAbsenceTests`, actual runner output:
    ```
    $ python3 -m pytest tests/test_oc_runipd.py -o addopts="" -k "VerificationAbsence" -v
    tests/test_oc_runipd.py::VerificationAbsenceTests::test_the_pre_fix_contrast_all_three_facts_were_one_value PASSED [ 16%]
    tests/test_oc_runipd.py::VerificationAbsenceTests::test_the_refusal_is_recorded_where_aw_runs_already_reads_it PASSED [ 33%]
    tests/test_oc_runipd.py::VerificationAbsenceTests::test_no_new_test_here_reads_the_gitignored_live_run_tree PASSED [ 50%]
    tests/test_oc_runipd.py::VerificationAbsenceTests::test_the_never_ran_case_is_a_failure_and_the_killed_case_is_not PASSED [ 66%]
    tests/test_oc_runipd.py::VerificationAbsenceTests::test_after_the_fix_the_three_facts_record_three_distinct_reasons PASSED [ 83%]
    tests/test_oc_runipd.py::VerificationAbsenceTests::test_an_unresolvable_plan_refuses_and_does_not_launch_a_verifier PASSED [100%]
    ====================== 6 passed, 237 deselected in 1.06s =======================
    ```
    THE AGY TWIN, ADDED BECAUSE IT WAS MEASURED ABSENT. `tests/test_agy_runipd_cli.py` contained ZERO occurrences of `resolve_plan_path` before this plan; it now carries the analogue of the `1549c018` regression plus the absence vocabulary:
    ```
    $ python3 -m pytest tests/test_agy_runipd_cli.py -o addopts="" -k "AgyVerificationAbsence" -v
    tests/test_agy_runipd_cli.py::AgyVerificationAbsenceTests::test_the_three_facts_are_distinguishable_from_this_host PASSED [ 20%]
    tests/test_agy_runipd_cli.py::AgyVerificationAbsenceTests::test_this_host_resolves_a_plan_that_moved_to_executed_mid_turn PASSED [ 40%]
    tests/test_agy_runipd_cli.py::AgyVerificationAbsenceTests::test_the_never_ran_case_is_a_failure_and_the_killed_case_is_unknown PASSED [ 60%]
    tests/test_agy_runipd_cli.py::AgyVerificationAbsenceTests::test_this_hosts_resolver_is_the_shared_object PASSED [ 80%]
    tests/test_agy_runipd_cli.py::AgyVerificationAbsenceTests::test_an_unresolvable_plan_raises_rather_than_returning_a_stale_path PASSED [100%]
    ======================= 5 passed, 88 deselected in 0.52s =======================
    ```
    `test_this_host_resolves_a_plan_that_moved_to_executed_mid_turn` is the twin: it resolves from `pending/`, renames the plan into `executed/`, and asserts resolution still finds it through the now-stale configured path. `test_this_hosts_resolver_is_the_shared_object` pins that the twin is a statement about THIS HOST'S BINDING rather than a second copy of the resolver.
    THE EXISTING `1549c018` REGRESSION STILL PASSES, UNTOUCHED, which is the evidence that the item's dead half is genuinely dead and was not re-fixed here:
    ```
    $ python3 -m pytest tests/test_oc_runipd.py::VerifierPromptTests::test_resolve_plan_path_handles_transition_to_executed -o addopts="" -q
    .                                                                        [100%]
    1 passed in 1.07s
    ```
    THE PRE-FIX CONTRAST is asserted as a committed test PAIR rather than only pasted: `test_the_pre_fix_contrast_all_three_facts_were_one_value` pins that the three facts collapsed to a single recorded value (the old literal `"unverified"`, spelled in the test rather than read from the module, so it stays a statement about history), and `test_after_the_fix_the_three_facts_record_three_distinct_reasons` pins that they now yield three distinct codes AND three distinct texts. The end-to-end form of the same contrast, measured through the real `execute_item`, is pasted in V-02.
    NO TEST READS THE GITIGNORED LIVE RUN TREE, asserted MECHANICALLY rather than promised. `test_no_new_test_here_reads_the_gitignored_live_run_tree` AST-walks its own class, collects every string literal that is not a docstring, and fails if any contains the run-tree path (the needle is assembled at runtime so the check does not flag itself). Every fixture in both new classes is a `tempfile.TemporaryDirectory`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the new `REFORK_TABLE` row showing BOTH runners, and `tests/test_runner_refork_guard.py` passing. Do NOT cite `test_the_table_covers_both_runners` as proof your row lists both runners: it asserts only that the table as a whole does, which it already did. Paste object-identity output for every added symbol across all three modules. Paste the MUTATION CHECK in full: define a local copy in `agy_runipd`, paste the FAILING guard output, revert, paste the passing output, and paste `git diff --exit-code` on both drivers showing no residual mutation. Paste the AST-measured oc-to-agy import count before and after, showing it did NOT INCREASE against your own measured before-value; do not assert a literal (47 at authoring, 48 at review).
  - Observed evidence: THE ROWS, SIX OF THEM, EACH LISTING BOTH RUNNERS, in `tests/test_runner_refork_guard.py`'s `REFORK_TABLE`:
    ```
    Owned("verify_absence_text", "runner_shared", BOTH),
    Owned("VERIFY_ABSENCE_CODES", "runner_shared", BOTH),
    Owned("VERIFY_ABSENCE_NO_OUTCOME_FILE", "runner_shared", BOTH),
    Owned("VERIFY_ABSENCE_TURN_INTERRUPTED", "runner_shared", BOTH),
    Owned("VERIFY_ABSENCE_PLAN_UNRESOLVABLE", "runner_shared", BOTH),
    Owned("VERIFY_ABSENCE_VERDICT_UNREADABLE", "runner_shared", BOTH),
    ```
    `test_the_table_covers_both_runners` IS EXPLICITLY NOT CITED as proof these rows list both runners; the in-tree comment above them records why (it asserts only the table's AGGREGATE `runners` set, which already equalled `BOTH`). What makes them bite is the per-row identity assertion plus the AST half, both mutation-checked below.
    THE GUARD PASSING, whole module:
    ```
    $ python3 -m pytest tests/test_runner_refork_guard.py -o addopts="" -q
    .................                                                        [100%]
    17 passed in 8.93s
    ```
    (12 before this plan, 17 after: the new `VerifyAbsenceSharingTests` adds five, all listed in V-04's sibling paste style:)
    ```
    tests/test_runner_refork_guard.py::VerifyAbsenceSharingTests::test_the_set_of_reasons_is_closed PASSED [ 20%]
    tests/test_runner_refork_guard.py::VerifyAbsenceSharingTests::test_the_vocabulary_is_reached_from_the_shared_execute_path PASSED [ 40%]
    tests/test_runner_refork_guard.py::VerifyAbsenceSharingTests::test_the_unreadable_code_is_an_alias_and_not_a_second_spelling PASSED [ 60%]
    tests/test_runner_refork_guard.py::VerifyAbsenceSharingTests::test_the_three_facts_are_distinguishable PASSED [ 80%]
    tests/test_runner_refork_guard.py::VerifyAbsenceSharingTests::test_every_code_is_the_shared_modules_object_in_both_runners PASSED [100%]
    ```
    OBJECT IDENTITY FOR EVERY ADDED SYMBOL ACROSS ALL THREE MODULES:
    ```
    OBJECT IDENTITY across all THREE modules:
      verify_absence_text                  oc is shared=True  agy is shared=True  oc is agy=True
      VERIFY_ABSENCE_CODES                 oc is shared=True  agy is shared=True  oc is agy=True
      VERIFY_ABSENCE_NO_OUTCOME_FILE       oc is shared=True  agy is shared=True  oc is agy=True
      VERIFY_ABSENCE_TURN_INTERRUPTED      oc is shared=True  agy is shared=True  oc is agy=True
      VERIFY_ABSENCE_PLAN_UNRESOLVABLE     oc is shared=True  agy is shared=True  oc is agy=True
      VERIFY_ABSENCE_VERDICT_UNREADABLE    oc is shared=True  agy is shared=True  oc is agy=True
    ```
    THE MUTATION CHECK, IN FULL. Replaced agy's import of `VERIFY_ABSENCE_NO_OUTCOME_FILE` with a textually identical LOCAL definition (the exact re-fork grep cannot detect):
    ```
    MUTATION APPLIED: agy re-forks VERIFY_ABSENCE_NO_OUTCOME_FILE as a local textually-identical copy
    $ grep -n 'VERIFY_ABSENCE_NO_OUTCOME_FILE = "verification-never-recorded"' agent_workflows/agy_runipd.py
    228:VERIFY_ABSENCE_NO_OUTCOME_FILE = "verification-never-recorded"
    ```
    THE GUARD FAILED, three tests, with the AST half naming the file and line:
    ```
    $ python3 -m pytest tests/test_runner_refork_guard.py -o addopts="" -q
    E       AssertionError: Lists differ: ['agy_runipd.py:228 re-defines `VERIFY_ABS[93 chars]LE`'] != []
    E       First extra element 0:
    E       'agy_runipd.py:228 re-defines `VERIFY_ABSENCE_NO_OUTCOME_FILE`, which `runner_shared.py` already owns as `VERIFY_ABSENCE_NO_OUTCOME_FILE`'
    =========================== short test summary info ============================
    FAILED tests/test_runner_refork_guard.py::VerifyAbsenceSharingTests::test_every_code_is_the_shared_modules_object_in_both_runners
    FAILED tests/test_runner_refork_guard.py::SymmetricReForkGuardTests::test_every_runner_attribute_is_the_owning_modules_object
    FAILED tests/test_runner_refork_guard.py::SymmetricReForkGuardTests::test_no_runner_redefines_an_already_extracted_symbol
    3 failed, 14 passed in 11.85s
    ```
    Note the new class's own identity test fires ALONGSIDE the two pre-existing halves, so the vocabulary is guarded by three independent assertions rather than one.
    REVERTED, AND THE REVERSION PROVEN BYTE-EXACT rather than assumed. Hashes taken BEFORE the mutation and again after reverting:
    ```
    (before mutation)
    f694cdc5d0d62a8f6481d28440ff1cdfa0452a95d87737e28c658702d88da7a7  agent_workflows/agy_runipd.py
    d655080311ef4524d7c84ec58a14b22e01e36d81af1b73c01b873685cb2de52f  agent_workflows/oc_runipd.py
    (after revert)
    f694cdc5d0d62a8f6481d28440ff1cdfa0452a95d87737e28c658702d88da7a7  agent_workflows/agy_runipd.py
    d655080311ef4524d7c84ec58a14b22e01e36d81af1b73c01b873685cb2de52f  agent_workflows/oc_runipd.py
    ```
    THE GUARD PASSING AGAIN, and `git diff --exit-code` clean on both of the repository's two highest-contention files:
    ```
    $ python3 -m pytest tests/test_runner_refork_guard.py -o addopts="" -q
    .................                                                        [100%]
    17 passed in 8.93s

    $ git diff --exit-code agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py && echo "..."
    GIT DIFF EXIT-CODE 0 on both drivers: no residual mutation
    ```
    THE OC-TO-AGY IMPORT COUNT DID NOT INCREASE, measured by my own AST walk rather than by asserting either of the plan's literals (47 at authoring, 48 at review, both now stale):
    ```
    BEFORE (at 3f42bb66, this lane's base): oc->agy import count: 56
    AFTER  (with this plan's changes):      oc->agy import count AFTER: 56
    ```
    Unchanged, because all six symbols are imported from `runner_shared` in BOTH hosts and none was added to `oc_runipd` for `agy_runipd` to import.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the six paths in `- Scope-Paths:`. Do NOT re-fix the verifier prompt path (already fixed at `1549c018`; re-doing it is the single most likely wasted action on this plan). Do NOT reorder the self-finalize sequence. Do NOT edit `run_state.py`, `verify_roles.py`, `runner_stop.py`, `integration_is_earned`, or the `driver_begin`/`driver_finalize` transaction. Do NOT change the verdict MAPPING or the `except` unparseable arm (sibling `1bfppy` owns both). Do NOT fix the twin finalize fallback (F-13); report it. Do NOT label the interrupt case a verification failure (F-10: R22 forbids it). Do NOT add a symbol to `oc_runipd` for `agy_runipd` to import. Do NOT add a new refusal beyond the stale-path one. Do NOT edit spec `25kzda`, and never its §4.2 finding-code table. Do NOT delete, move, or commit any untracked file you did not create, including the `opencode-recovery/*.md` transcripts that make one suite test red. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`. NOTE `run_viewer.py` is the one path a token choice might legitimately require (F-12); if so, declare it with a `--scope-reason` rather than shipping a token that renders as `-`.

THREE PLANS EDIT THIS BLOCK. `1bfppy` (verdict mapping and the `except` arm) and `bxx9af` (evidence predicate, itself dependent on `1bfppy`) are both `reviewed`/`go-pending-approval`. READ BOTH ON DISK before editing and reconcile names against BOTH, not just `1bfppy`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN, and the evidence for that instruction is this plan's own citations. MEASURED AT REVIEW, one day after authoring: the three oc `unverified` sites moved `:6432`/`:6434`/`:6436` -> `:6645`/`:6647`/`:6649`, the stale-path fallback `:6376-6377` -> `:6583-6584`, `integration_is_earned` `:3684` -> `:3740`, `reconcile_interrupted` `:6782` -> `:6995`, and `resolve_plan_path` `runner_shared.py:1119` -> `:1433`. Find `execute_item`'s `v_outcome_file` block, `resolve_plan_path`, `build_verifier_prompt`, `integration_is_earned`, `reconcile_interrupted`, and `runner_stop.is_indeterminate` by name.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved fzxfph --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION, close backlog `t74o5q`, which this plan carries as `- From-Backlog:` and whose `- Blocks-Release: next` gate it inherits. The item's obsolete halves are recorded in the item itself, so closing it does not silently drop work: the surviving fixes (3) and (4) ship here and fixes (1) and (2) are recorded as already-delivered and deliberately-not-done respectively.
