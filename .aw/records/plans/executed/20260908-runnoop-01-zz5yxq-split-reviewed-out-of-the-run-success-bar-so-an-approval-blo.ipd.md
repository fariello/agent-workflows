# IPD: Split reviewed out of the run success bar so an approval-blocked queue is not a silent success

- Date: 2026-09-08
- Kind: child
- Concern: `reviewed` is simultaneously a routing decision meaning "execute this" and a completion decision meaning "this already succeeded", and the two cannot both be right. MEASURED at HEAD `44d4950d` by running the deciding expressions against the real symbols: `action_for("child", "reviewed")` returns `'execute'` (`runner_shared.py:2735`, delegating to `determine_action` at `:2727`, which routes everything not `to-review`/`draft` to `execute`); the queue builder freezes that item's queue status as `"reviewed"` rather than `"queued"`, because `reviewed` is absent from the admission tuple `("to-review", "draft", "approved", "auto-approved")` (`oc_runipd.py:3011`, `agy_runipd.py:2026`); and `"reviewed" in SUCCESS_STATES` is `True` (`oc_runipd.py:327`, `agy_runipd.py:388`). So the item is never dispatched AND is counted as a success: `runner_stop.deliberate_stop_exit_code(["reviewed"], success_states=SUCCESS_STATES, stopped=False)` returns `0`.
  THE OBSERVED COST (backlog `em0z50`, 2026-08-29): `aw oc run wtiso` with all 8 `wtiso` plans at `- Status: reviewed` printed the run id, the state dir, and `No OpenCode session was captured for this run.` and exited 0. `aw runs <id>` showed `8 steps: 8 reviewed`, `action=execute`, `Attempts: 0` on every row, an empty `outcomes/`, and a single `run-created` event. The operator believed 8 plans were queued.
  THE CONSTANT IS DUPLICATED, NOT SHARED, which changes the work: measured `oc.SUCCESS_STATES is agy.SUCCESS_STATES` -> `False`, `==` -> `True`. Both hosts must be edited and the equality pinned, or the next fix reaches one host only. `EXECUTION_SUCCESS_STATES` already exists for the execution-success question (`oc_runipd.py:328`, `agy_runipd.py:389`) and is already used correctly in three places, so the vocabulary this plan needs is largely present.
- Scope: Make an execute-action item whose plan is `reviewed`-but-unapproved carry a NEEDS-APPROVAL disposition that is NOT a member of the success bar, on BOTH hosts, and make the run's exit code reflect it. Classify EVERY `SUCCESS_STATES` call site rather than substituting wholesale, because the constant answers five different questions. EXCLUDES making a `reviewed` plan executable (that is the auto-approval bridge, shipped by `97df1z`, deliberately not widened); excludes the per-artifact line (child 02) and the end-of-run summary (child 03); excludes any change to `determine_action`'s routing.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_runner_shared.py, tests/test_rununify_run_queue_characterization.py, tests/test_rununify_initialize_run_characterization.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: runnoop
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: zz5yxq
- Blocks-Release: next
- From-Backlog: em0z50

## Workflow history
- 2026-09-18 executed (aw oc run): aw oc run self-finalize: zz5yxq verified (set runnoop, attempt 1). [Scope reconciliation - out-of-scope tests/test_runner_refork_guard.py: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope tests/test_rununify_run_queue.py: changed by the plan's approved execution (auto-reconciled by aw oc run); in-scope-unmodified tests/test_agy_runipd_cli.py: declared-but-unmodified (auto-acknowledged by aw oc run)]
- 2026-09-18 executed (opencode its_direct/pt3-claude-opus-5-1m-us): ATTEMPT 2, on lane `aw/lane/zz5yxq_attempt2` at base `70a2059f`, commit `8ea21b29` (9 files, +668/-14). ALL SEVEN E-ITEMS PERFORMED AND ALL SEVEN V-ITEMS CARRY PASTED EVIDENCE; `aw ipd lint --phase pre-transition` reports `outcome: clean` exit 0 with one pre-existing advisory (`check.ipd-uncarried-obligation`, about this plan's own Deferred rows, not about new work). SUITE: `8122 passed, 3 skipped, 2 xfailed` bare, against a pre-change baseline measured in the SAME worktree of `8114 passed, 3 skipped, 2 xfailed`. BOTH FULLY GREEN, so the failing-node-id comparison is trivially empty-to-empty; the +8 is this plan's new tests. THE THREE FAILURES THAT KILLED ATTEMPT 1 DID NOT RECUR, and the reason attempt 2 could see clearly is that both contributing conditions were fixed upstream in the meantime (the `AW_EXECUTION_ROLE=worker` pytest leak, `f1a6e94c`, and the two environmental failures the plan's Step 0 recorded).
  TWO DESIGN DEVIATIONS, both forced by measurement and both recorded as decisions rather than absorbed silently. FIRST AND MOST IMPORTANT (DECISION 2-zz5yxq-D1): E-02 specifies `EXECUTION_SUCCESS_STATES` for the execute branch, and THAT IS WRONG HERE. Implemented literally, it FAILS `tests/test_rununify_run_queue_characterization.py::TheExitCodeReflectsTheRealOutcome::test_the_exit_code_reads_SUCCESS_STATES_not_EXECUTION_SUCCESS_STATES` with `AssertionError: 0 == 0`, because that test exists to pin `substantially-complete` as a NONZERO exit. `EXECUTION_SUCCESS_STATES` answers the DEPENDENCY question ("may a dependent run?"), for which `substantially-complete` counts; this is the REPORTING question, for which it deliberately does not. So the literal plan would have fixed one silent success by introducing another. The bar shipped is a new derived constant `EXECUTE_REPORTING_SUCCESS_STATES = frozenset(SUCCESS_STATES - {"reviewed"})`, derived by SUBTRACTION so it cannot drift, which narrows exactly one status for exactly one action. The SELECTION SHAPE is still the established `action != "review"` idiom, as E-02 requires. SECOND (DECISION 2-zz5yxq-D2): E-07 named three tests pinning the old contract; there were FOUR. `tests/test_rununify_run_queue.py::TheClosureClassificationIsPinned` also pinned it, and repairing its census surfaced a REAL PRE-EXISTING FORK the table had never classified (`_integrate_stranded_lanes`, measured NOT the same object across hosts), which was classified rather than papered over by lowering `CLOSURE_TOTAL`. E-07's own third test (`..._reads_SUCCESS_STATES_not_...`) needed NO change, because `reviewed` was never removed from `SUCCESS_STATES` (F-5) - it is UNTOUCHED, passing, and is the test that caught the literal-E-02 attempt.
  THE TREE HAD DRIFTED IN A WAY THAT CHANGES E-01's SHAPE, reported because the plan's F-6/F-9 measurements no longer hold: `SUCCESS_STATES` is NO LONGER a per-host pair (`rununify` `tx6q0h` relocated it into `runner_shared`; measured `oc.SUCCESS_STATES is agy.SUCCESS_STATES` -> True), so there is ONE classification comment rather than two, and E-04's pin for it is the STRONGER `assertIs` instead of an equality. `EXECUTION_SUCCESS_STATES` is still duplicated (`is` -> False, `==` -> True) and takes the equality pin as planned. Questions (2), (3) and (4) had also MOVED INTO SHARED CODE before this plan ran (`execute_item_core`, `render_continuation_hint`), so the hosts' remaining bare-name reads are only questions (1) and (5), not the "six in oc and four in agy" V-01 expected. E-02 sited the predicate in the PREFERRED home (`runner_shared`), not via the `oc`-owned re-export F-10 permits, because no circular-import pressure existed; consequently E-04's identity pin went to `tests/test_runner_refork_guard.py`'s `REFORK_TABLE` (whose contract fits a `runner_shared`-owned symbol exactly) rather than to `_SHARED_NAMES`.
  SCOPE: two paths outside `- Scope-Paths:` were changed and need a `--scope-reason` at finalize: `tests/test_runner_refork_guard.py` (E-04's identity pin, which the plan explicitly anticipated as an executor's siting decision) and `tests/test_rununify_run_queue.py` (the fourth old-contract test, above). E-03 reused the SHIPPED token `needs_input` per OQ-01, so NO spec file was edited and `TERMINAL_STATES` was NOT widened (the fact is carried beside the status; `interrupted` precedent). Both E-06 mutations were performed and both guards FAILED under them and PASSED after revert. Backlog `em0z50` was deliberately NOT closed (its fixes (b)/(c) are children 02/03). Two new backlog items filed from the defect report: `mh60nd` (wire the drivers to `aggregate_run_exit` for the spec's exit 3, OQ-02's follow-on) and `7l1ggb` (the closure census's missing-direction assertion). NOT FINALIZED BY ME: `aw ipd begin`/`finalize` are REFUSED to a worker-role process (`AW-LIFECYCLE-ROLE-001`), so the runner owns the transition.
- 2026-09-18 amended (opencode its_direct/pt3-claude-opus-5-1m-us): EXECUTION ATTEMPT 1 FAILED ON A SCOPE GAP THIS PLAN CREATED, and the gap is now closed rather than left for the next executor to rediscover. Run `run-20260918T050013Z-2604174` executed this plan on lane `aw/lane/zz5yxq`, did REAL work (1 commit, ~560 lines, all 6 E-items performed and all 6 V-items recorded passing, `aw ipd lint` conforming) and wrote `disposition: "executed"`, but did NOT finalize, so the driver recorded `partial` and that blocked all three siblings (`7ewc74`, `m85gxh`, `bsc457`), taking the run to BLOCKED with 0 of 4 executed. CAUSE, measured on the lane before it was deleted: its suite reported `3 failed, 7997 passed`, and all three failures were tests PINNING THE OLD CONTRACT this plan changes, two of them in files this plan never named. `- Scope-Paths:` now adds `tests/test_rununify_run_queue_characterization.py` and `tests/test_rununify_initialize_run_characterization.py`, and new E-07/V-07 require the three tests to be updated as a DELIBERATE contract change with a recorded reason, explicitly forbidding deletion of an assertion to green the suite. CONTRIBUTING CONDITION, since it explains why the agent could not see the 3 among the noise: at that HEAD a runner turn's suite also carried 31 phantom failures from `AW_EXECUTION_ROLE=worker` leaking into pytest (backlog `1uq1cu`/`xqa4hw`, fixed in `f1a6e94c`), so the agent saw `31 failed` and could not distinguish its own 3. The lane, its branch (`25eb8c44`) and its stale begin receipt (frozen at base `6ff7a7ba` while HEAD had moved 36 commits, and whose work CONFLICTED on all three test files) were deleted at the maintainer's direction; its outcome, execution report and decisions register remain in the run record. NO `- Status:` CHANGE: this plan stays `approved` and is re-runnable as authored plus E-07.
- 2026-09-13 approved (aw set): status set to approved
- 2026-09-08 reviewed (aw set): /plan-review round 1 complete: APPROVE WITH REVISIONS APPLIED; PR-901..PR-909, all FIXED in place. Both open questions resolved from shipped code (OQ-01 needs_input is already the shipped token; OQ-02 exit 3 machinery already agrees with the spec, drivers unwired). Review record written; aw ipd lint --phase review-finalize conforms.
- 2026-09-08 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-901..PR-909. Reviewed at HEAD `6cd66049`. Record: `.aw/records/reviews/20260908-runnoop-01-zz5yxq-split-reviewed-out-of-the-run-success-bar-so-an-approval-blo.review.md`. `aw ipd lint --phase author` conformed CLEAN with no advisory. THE DIAGNOSIS AND ITS SHARPEST CONSTRAINT BOTH HOLD, re-executed rather than re-read: `'reviewed' in SUCCESS_STATES` True, `action_for('child','reviewed')` `'execute'`, `deliberate_stop_exit_code(["reviewed"], ...)` `0`, `oc.SUCCESS_STATES is agy.SUCCESS_STATES` False while `==` True, and the F-5 warning is real (the in-tree docstring records run `run-20260904T042705Z-1025943` killing Orders 02-05 the instant Order 01 reached `reviewed`). Do not weaken F-5. THE FINDING THAT CHANGES THE MOST WORK IS PR-901: agy DOES NOT DEFINE `edge_satisfied` OR `cascade_dependency_blocked`, it RE-EXPORTS oc's objects (`agy.edge_satisfied is oc.edge_satisfied` -> True, `__module__` `agent_workflows.oc_runipd`), so E-01's "agy twin at `:2275`" names a line that is a docstring about argv, agy has NO dependency call sites at all, and its real `SUCCESS_STATES` uses are FOUR not five. That also inverts E-02's siting rule (PR-902): this repository's established convention for exactly this family is ONE definition in `oc_runipd` RE-EXPORTED with `as <same-name>` and pinned by object identity in `tests/test_runner_item_dependencies.py::_SHARED_NAMES`, with an in-file comment recording that `ruff` stripped 6 such re-exports once and the symmetry test caught it; `runner_shared` is not the only legal home and the plan's flat prohibition would fork a family that is deliberately unforked. BOTH OPEN QUESTIONS ARE RESOLVED FROM SHIPPED CODE rather than left to the executor: OQ-01's deciding grep was run and `needs_input` is ALREADY the shipped token (`run_gates.GATE_STATUS_NEEDS_INPUT`, `run_evidence.AGGREGATE_NEEDS_INPUT`), so it is not merely spec-available but in use for this exact meaning; and OQ-02's exit code is 3, because `run_evidence._CLASSIFICATION_EXITS` already transcribes the spec table with `needs_input: 3` and `_CLASSIFICATION_PRIORITY` already makes 3 outrank 1, so nothing needs reconciling and the plan's fear of an unreconciled table is obsolete. Also corrected: every oc line number in E-01 had drifted (six sites, all wrong); the oc-to-agy import count is 43/48 not 47; the `test_runner_shared.py` wrapper count is 8 not 5; and the "roughly 32 tests fail in a lane worktree" baseline is stale.
- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `em0z50` fix (a); inherits its `- Blocks-Release: next`. Every line number in this plan was measured at HEAD `44d4950d` by grep on the SYMBOL, and every behavioral claim was produced by RUNNING the expression rather than reading it. Three measurements changed the design from what the backlog item assumed. FIRST, the item cites `SUCCESS_STATES` at `oc_runipd.py:90`; it is at `:327`, and the agy twin at `:388` is a SEPARATE object, so "audit every use and its agy twin" is two edits plus an equality pin, not one edit. SECOND, there are SEVEN `SUCCESS_STATES` reads in oc and FIVE in agy answering FIVE DIFFERENT questions, and one of them (the orchestrator dispatch bar at `oc_runipd.py:3504`) already passes `EXECUTION_SUCCESS_STATES` deliberately, so a blanket substitution would both over- and under-reach; E-01 classifies them first and the classification is the deliverable, not a step. THIRD, and this is the finding most likely to be missed: `cascade_dependency_blocked` (`oc_runipd.py:4217-4219`) and `edge_satisfied` (`:3373`) BOTH select between the two constants on `item.get("action") != "review"`, and the docstring at `:4186` records a MEASURED failure from hardcoding the execution bar there ("a review-mode Set run was simply impossible to complete", run `run-20260904T042705Z-1025943`). So `reviewed` MUST remain in the review-action bar; only the EXECUTE-action bar may lose it. A fix that removed `reviewed` from `SUCCESS_STATES` outright would re-break review-mode Set runs, which is why E-01 forbids that shape explicitly.

## Goal

Stop a `reviewed`-but-unapproved execute item from being recorded and counted as a success, on both hosts, without making it executable and without re-breaking review-mode Set runs.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: classify before changing

- [x] E-01 CLASSIFY EVERY `SUCCESS_STATES` READ IN BOTH HOSTS and record the classification in the code as a comment at the constant's definition, naming which question each site asks. Locate the sites by grep on the SYMBOL, never by the line numbers in this plan: every oc coordinate below was RE-MEASURED at review and every one had drifted.
  THE SITE INVENTORY, CORRECTED. In `oc_runipd.py` there are 8 textual occurrences of the bare name, of which one is the DEFINITION (`:336`) and one is inside a COMMENT (`:4243`), leaving SIX real reads: `:3377` in `edge_satisfied`, `:4275` in `cascade_dependency_blocked`, `:6943` and `:6946` the finish glyph and its color, `:7496` the exit code, `:7577` the continuation hint's `all_success`. In `agy_runipd.py` there are 5, of which one is the definition (`:408`), leaving FOUR: `:4013`/`:4016` the glyph pair, `:4515` the exit code, `:4589` the `all_success` twin. The plan previously said seven and five, and named an agy `edge_satisfied` twin at `:2275`; that line is a docstring about argv handling.
  AGY HAS NO DEPENDENCY CALL SITES AT ALL, and this is the correction that most changes the work. `agy_runipd` does not DEFINE `edge_satisfied` or `cascade_dependency_blocked`; it RE-EXPORTS oc's objects (`agy_runipd.py:350`, `:368`, in a `from agent_workflows.oc_runipd import (...)` block using the `as <same-name>` form). Measured: `agy.edge_satisfied is oc.edge_satisfied` -> `True`, `__module__` -> `agent_workflows.oc_runipd`; same for `cascade_dependency_blocked`. So there is exactly ONE implementation of question (1) and it is already shared. Do not go looking for an agy copy to edit, and do not "add" one.
  THE FIVE QUESTIONS, so the classification is not re-derived: (1) IS A PREREQUISITE SATISFIED IN THIS RUN (`edge_satisfied`, `cascade_dependency_blocked`, oc-only and already shared with agy by re-export) - these already select between the two constants on `item.get("action") != "review"` and MUST KEEP `reviewed` for the review action; (2) DID THE RUN SUCCEED OVERALL (the exit code, one site per host); (3) SHOULD THIS ROW SHOW A CHECKMARK (the glyph pair, one pair per host); (4) IS THERE ANYTHING LEFT TO RESUME (`all_success` in the continuation hint, one per host); (5) the ORCHESTRATOR DISPATCH BAR, which already passes `EXECUTION_SUCCESS_STATES` explicitly and is NOT a `SUCCESS_STATES` read at all, listed only so a reader does not "fix" it. NOTE THE CONSEQUENCE FOR THE HOSTS' SYMMETRY: questions (2), (3) and (4) exist on BOTH hosts; question (1) exists ONCE. A classification comment that implies a per-host pair for (1) would be wrong.
  DO NOT REMOVE `reviewed` FROM `SUCCESS_STATES`. That is the tempting one-line fix and it is WRONG, with measured evidence in-tree: the docstring at `cascade_dependency_blocked` (re-locate by symbol; the plan's `:4186-4198` has drifted to roughly `:4242-4254`) records that hardcoding `EXECUTION_SUCCESS_STATES` there made a review-mode Set run impossible to complete (run `run-20260904T042705Z-1025943`: a 6-item all-`review` run of the `wslayout` Set reviewed Orders 00 and 01, then killed Orders 02-05 the instant Order 01 reached `reviewed`). `SUCCESS_STATES` IS the review-action bar and `reviewed` belongs in it. The defect is that the EXECUTE-action sites read it too. VERIFIED AT REVIEW: that docstring is still present and still says so, and the comment at the `:4275` site explicitly warns "do NOT hardcode EXECUTION_SUCCESS_STATES here (that made a review-mode Set run impossible)".
  - Depends on: none
  - Expected outcome: a comment at each constant's definition in BOTH hosts naming, per call site, which of the five questions it answers and which bar is correct for it, and recording that question (1) has ONE implementation shared by re-export rather than a per-host pair; no behavior change in this item.
  - Execution state: performed

### Task group 2: split the bar for the execute action

- [x] E-02 GIVE THE EXECUTE-ACTION SITES AN ACTION-AWARE BAR, using the selection shape `edge_satisfied` and `cascade_dependency_blocked` already use (`item.get("action") != "review"`) rather than inventing a second idiom. The sites to change are the ones E-01 classified as questions (2), (3) and (4): the exit code, the glyph pair, and `all_success`. An item whose `action` is `execute` and whose status is `reviewed` must NOT satisfy any of the three.
  SITE THE PREDICATE ONCE. `runner_shared.py` is the PREFERRED home and remains the default: it already holds `determine_action` (`:2969`) and `action_for` (`:2977`), which is exactly this family of decision, and both hosts already import it.
  BUT DO NOT TREAT "NEVER IN `oc_runipd`" AS ABSOLUTE, because this repository's established convention for THIS PARTICULAR FAMILY is the opposite and the plan's flat prohibition would fork something deliberately unforked. The action-aware bar's existing implementations (`edge_satisfied`, `cascade_dependency_blocked`) live in `oc_runipd` and are RE-EXPORTED to agy with the `as <same-name>` form (`agy_runipd.py:350`, `:368`), pinned by object identity in `tests/test_runner_item_dependencies.py::_SHARED_NAMES` (which lists both). The in-file comment there records WHY the form matters: `ruff` removed 6 of those re-exports on one commit attempt and the symmetry test caught it, and losing one would make a later fix reachable through only one driver. So the real requirement is ONE DEFINITION plus an OBJECT-IDENTITY PIN, not a particular file. If the predicate must sit beside `edge_satisfied` to reuse its `is_exec` selection without a circular import, siting it in `oc_runipd` and re-exporting is CORRECT and is what the neighbours do; say which you chose and why. What is genuinely forbidden is a second copy in agy.
  THE IMPORT-COUNT ARGUMENT IS ALSO MIS-STATED and should not be the deciding factor: the count is 43 names at top level and 48 counting five function-local ones (AST-measured at HEAD `6cd66049`), not 47, and adding one re-export to a family the identity test already pins is not the layering defect `cnwy8g` owns. Report the count before and after; do not let a wrong number drive the siting.
  - Depends on: E-01
  - Expected outcome: ONE definition of the predicate with an object-identity pin proving both hosts see the same object; the chosen home stated with its reason; a `reviewed` execute item fails all three of exit-code success, checkmark glyph, and `all_success`; a `reviewed` REVIEW item still satisfies all three, unchanged.
  - Execution state: performed

- [x] E-03 RECORD THE NEEDS-APPROVAL DISPOSITION ON THE QUEUE ITEM so it is durable in run state rather than only reflected in an exit code. The queue builder already distinguishes the case: an item whose plan status is not in the admission tuple gets queue status `"reviewed"` (`oc_runipd.py:3011`, `agy_runipd.py:2026`), which is where the needs-approval fact is already implicit. Make it EXPLICIT and name it, so children 02 and 03 have a token to print and count.
  THE TOKEN IS `needs_input` AND OQ-01 IS RESOLVED; do not re-litigate it. The question said the deciding grep "must be run, not guessed"; review RAN it, and the answer is stronger than the question anticipated. `needs_input` is not merely available in spec §5.6, it is ALREADY THE SHIPPED TOKEN FOR THIS EXACT MEANING in two first-party modules: `run_gates.GATE_STATUS_NEEDS_INPUT = "needs_input"` (`run_gates.py:31`, used at `:157` and `:214`) and `run_evidence.AGGREGATE_NEEDS_INPUT = "needs_input"` (`run_evidence.py:1839`), whose own comment reads "Human input or explicit acknowledgement is required (spec 5.6 exit 3)" and whose docstring at `:1966` glosses the item flag as "True when a human gate stopped the item (spec `:938`)". So the question's own escape hatch, "a new token is defensible if `needs_input` is already load-bearing for a different case", is CLOSED: it is load-bearing for the SAME case. Reuse it, amend no spec, and declare no spec file in `- Scope-Paths:`.
  PREFER WIRING THE EXISTING CARRIER OVER INVENTING A FIELD. Since `run_evidence.AggregatedItem` already carries a `needs_input: bool` flag that `aggregate_run_exit` reads, check whether the durable fact can be expressed through that existing vocabulary before adding a new queue-item key. If it cannot (the drivers do not construct `AggregatedItem` today, measured), say so and record what you added instead.
  DO NOT ADD A NEW MEMBER TO `TERMINAL_STATES` WITHOUT CHECKING ITS READERS. `TERMINAL_STATES` is consulted by `cascade_dependency_blocked` and `decide_orchestrator_dispatch` (re-locate both by symbol; the plan's `:4216` and `runner_shared.py:2756` have drifted), so a new member changes dependency and retirement behavior. Measure those readers before adding, and if the queue status `"reviewed"` already suffices as the durable carrier, prefer annotating the item over widening the set. NOTE `interrupted` IS ALREADY A PRECEDENT for a status the runner uses that is NOT in `TERMINAL_STATES` (measured: `'interrupted' in TERMINAL_STATES` -> False), so a needs-approval fact carried outside that set is consistent with how the runner already works and is the cheaper shape.
  - Depends on: E-02
  - Expected outcome: the queue item carries an explicit, named needs-approval fact readable by a later reporting child, using the SHIPPED token `needs_input`; whether the existing `run_evidence` carrier was reusable is stated either way; `TERMINAL_STATES` readers are measured before any widening, and no spec file is edited.
  - Execution state: performed

- [x] E-04 PIN THE CROSS-HOST EQUALITY of `SUCCESS_STATES` and `EXECUTION_SUCCESS_STATES` so a future one-sided edit fails a test. Measured today: `is` -> `False`, `==` -> `True` for both pairs. This plan does NOT unify them into one object (that is `rununify`'s job and `cnwy8g`'s layering correction), so the equality assertion is the only thing standing between here and a silent divergence.
  ASSERT THE SHARED PREDICATE BY OBJECT IDENTITY TOO, not by grep: the predicate E-02 adds must resolve to the SAME object from every module that exposes it. Grep cannot tell a shared object from a textually identical copy, which is precisely how `render_stream` was re-forked.
  PUT THE IDENTITY PIN WHERE ITS NEIGHBOURS LIVE, and choose deliberately between two existing homes rather than inventing a third. `tests/test_runner_item_dependencies.py::_SHARED_NAMES` already pins `edge_satisfied` and `cascade_dependency_blocked` by `assertIs` across both drivers and is the natural home if the predicate joins that family; `tests/test_runner_refork_guard.py`'s `REFORK_TABLE` is the home for a symbol OWNED by `runner_shared` or `render_stream`, but note its contract asserts BOTH no top-level definition in the runner AND attribute identity, so a re-exported-from-oc symbol cannot be listed there (a row naming `oc_runipd` as a runner that must not define it would be self-contradictory). Pick the home that matches E-02's siting decision and say which.
  - Depends on: E-02
  - Expected outcome: a test asserting `oc.SUCCESS_STATES == agy.SUCCESS_STATES` and the same for `EXECUTION_SUCCESS_STATES`, which FAILS if either is edited alone; plus an object-identity assertion for the new predicate, sited in whichever of the two existing guard modules matches E-02's siting, with the choice stated.
  - Execution state: performed

### Task group 3: prove it on the measured case

- [x] E-05 ADD THE REGRESSION TEST FOR THE MEASURED INCIDENT: a run whose selector resolves ONLY to `reviewed`-not-approved plans must not count those steps as successes and must not exit 0. Build it from the real queue-entry shape rather than a hand-written dict where possible, so the test breaks if the queue builder's admission tuple changes.
  ALSO ADD THE CONTROL, and it is the load-bearing half: an all-`review`-action run whose items reach `reviewed` must STILL succeed and STILL exit 0, because that is the case the in-tree docstring at `oc_runipd.py:4186` records as having been broken once by exactly the fix this plan makes. A test suite that only covers the execute case would pass over a re-broken review-mode Set run.
  - Depends on: E-03, E-04
  - Expected outcome: two tests per host, one asserting the execute case is no longer a silent success and one asserting the review case is unchanged; both pass.
  - Execution state: performed

- [x] E-06 MUTATION-CHECK BOTH NEW GUARDS. A guard that cannot fail is not evidence. For E-04's equality pin, edit one host's constant and show the test FAILS, then revert. For E-05's execute-case test, revert the E-02 predicate to the unconditional `SUCCESS_STATES` read and show the test FAILS, then restore.
  - Depends on: E-05
  - Expected outcome: each guard demonstrated to fail under the mutation it exists to catch, and to pass after revert.
  - Execution state: performed

- [x] E-07 UPDATE THE THREE TESTS THAT PIN THE BEHAVIOR THIS PLAN CHANGES, and update them as a DELIBERATE contract change with the reason recorded, never by deleting an assertion to make a suite green. MEASURED 2026-09-18 on lane `aw/lane/zz5yxq` (the first execution attempt, since deleted): the lane's own suite reported `3 failed, 7997 passed`, and all three failures are tests asserting the OLD behavior rather than defects in the new code. (1) `tests/test_rununify_run_queue_characterization.py::TheExitCodeReflectsTheRealOutcome::test_the_exit_code_reads_SUCCESS_STATES_not_EXECUTION_SUCCESS_STATES` asserts `set(module.SUCCESS_STATES) == {"reviewed", "approved", "executed"}` (`:1257-1259`), which is exactly the membership E-02 changes. (2) `tests/test_rununify_initialize_run_characterization.py::TheFrozenQueueEntryShapeIsIdenticalOnBothHosts::test_both_hosts_freeze_the_same_twelve_keys` pins a 12-key `EXPECTED_KEYS` frozenset (`:600-615`) that E-03's durable `needs_input` key makes 13; its own failure message says "a key added or removed here is a compatibility change", which is precisely what E-03 is, so the constant and the test NAME both move. (3) `tests/test_oc_runipd.py::ContinuationHintTests::test_single_session_success` builds its success fixture as `queue=[{"status": "reviewed"}]` (`:1979`) and asserts the hint contains no "resume"; under the new bar a `reviewed` execute item is no longer a success, so the FIXTURE must be changed to a genuinely successful status (`executed`) rather than the assertion relaxed. For each, state in the test's own docstring or comment that the old value was the pre-`zz5yxq` contract and why the new one is correct, so a later reader does not read the edit as a weakening.
  - Depends on: E-02, E-03
  - Expected outcome: the three named tests assert the NEW contract, each carrying a recorded reason; the bare suite's failing NODE IDS are unchanged from the pre-change baseline apart from these three now passing.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE ACTION-AWARE BAR IS AN ESTABLISHED IDIOM, NOT AN INVENTION. `edge_satisfied` (`oc_runipd.py:3365`) and `cascade_dependency_blocked` (`:4217-4219`) both write `EXECUTION_SUCCESS_STATES if is_exec else SUCCESS_STATES` with `is_exec = item.get("action") != "review"`. Reuse that exact shape; a second idiom for one decision is how two functions came to give opposite answers before (the docstring at `:4186` records it).
- THE IMPORT DIRECTION IS ONE-WAY AND MUST STAY SO. `agy_runipd` imports 43 names from `oc_runipd` at top level and 48 counting five function-local ones (AST-measured at HEAD `6cd66049`; the plan's earlier "47" matched neither); `oc_runipd` imports zero from agy. `runner_shared` is the PREFERRED home for a new shared symbol.
- BUT THE `oc`-OWNED RE-EXPORT IS A LEGITIMATE, PINNED PATTERN FOR THIS FAMILY, not a defect to avoid (F-9, F-10). `edge_satisfied` and `cascade_dependency_blocked` are defined in `oc_runipd` and bound into agy with `as <same-name>`, pinned by `assertIs` in `tests/test_runner_item_dependencies.py::_SHARED_NAMES`. The invariant this repository actually enforces is ONE DEFINITION plus an IDENTITY PIN. A blanket "never in `oc_runipd`" rule would either forbid siting the new predicate beside the code it must agree with, or push it into `runner_shared` at the cost of a circular-import risk; decide on the merits and pin identity either way.
- `runner_shared` ALREADY OWNS THE ROUTING DECISIONS: `determine_action` (`:2969`) and `action_for` (`:2977`) live there precisely so the two hosts cannot route differently. (The plan's `:2727`/`:2735` have drifted; `:2725-2740` is now inside `find_unauthored_child_rows`.) The comment in `oc_runipd` records the measured divergence that forced the move (`agy.determine_action('approved')` returned `'execute'` where oc's did not).
- `EXECUTION_SUCCESS_STATES` ALREADY EXISTS and is already the correct bar in three places, so this plan mostly makes more sites use the constant that is already right, rather than inventing a state.
- THE BASELINE MUST BE MEASURED IN THE EXECUTING WORKTREE, not quoted from here, and THE FIGURES BELOW ARE THE RE-MEASURED ONES because the plan's original pair was wrong in both halves. Measured bare at review (HEAD `ef1e1fbe`): `2 failed, 5864 passed, 3 skipped, 2 xfailed in 88.84s`, and `test_orchestrator_retirement` PASSES now. The two failures are `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` (environmental: an `rglob` that ignores `.gitignore`; backlog `8kttqq`; do NOT delete the untracked directory it walks, which may be another agent's work) and `tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130` (a `TimeoutExpired` under parallel load; that file passes 47/47 alone). The "roughly 32 tests fail in a lane worktree" figure is also stale: `tests/test_run_viewer.py` now passes 69/69 here. Compare failing NODE IDS, never totals, and do not report either pre-existing failure as yours.
- Suite bare: `python3 -m pytest`. Do not add `-n0`, a second `-q`, or `-p no:randomly`; `pyproject.toml` `addopts` already supplies the intended flags.

## Findings

| Id | Severity | Location (measured at HEAD `44d4950d`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `oc_runipd.py:327`, `agy_runipd.py:388` | `reviewed` is a member of `SUCCESS_STATES`, which is the "already succeeded" bar. | `"reviewed" in oc.SUCCESS_STATES` -> `True` |
| F-2 | HIGH | `runner_shared.py:2727`, `:2735` | The same status routes to `action=execute`, so one status carries two contradictory meanings. | `action_for("child","reviewed")` -> `'execute'` |
| F-3 | HIGH | `oc_runipd.py:7296`, `agy_runipd.py:4509` | The run exit code is computed against `SUCCESS_STATES`, so an all-`reviewed` queue exits 0 having done nothing. | `runner_stop.deliberate_stop_exit_code(["reviewed"], success_states=SUCCESS_STATES, stopped=False)` -> `0` |
| F-4 | HIGH | `oc_runipd.py:3011`, `agy_runipd.py:2026` | The admission tuple omits `reviewed`, so such an item is frozen as queue status `"reviewed"` and never dispatched. Both hosts, byte-identical expression. | source read, both hosts |
| F-5 | BLOCKER-IF-IGNORED | `oc_runipd.py:4186-4198` | REMOVING `reviewed` FROM `SUCCESS_STATES` WOULD RE-BREAK REVIEW-MODE SET RUNS. The in-tree docstring records the measured failure (run `run-20260904T042705Z-1025943`, `wslayout`, Orders 02-05 killed the instant Order 01 reached `reviewed`) caused by hardcoding the execution bar at that site. `SUCCESS_STATES` IS the review-action bar. | in-tree docstring citing a real run id |
| F-6 | MED | measured | The two constants are duplicated per host, equal but not identical, so a one-sided edit is silent. | `oc.SUCCESS_STATES is agy.SUCCESS_STATES` -> `False`; `==` -> `True` |
| F-7 | MED | `oc_runipd.py:3504` | The orchestrator dispatch bar already passes `EXECUTION_SUCCESS_STATES` explicitly and is NOT a `SUCCESS_STATES` read, so it needs no change and must not be "fixed". | source read |
| F-8 | MED | spec §5.6; `run_gates.py:31`; `run_evidence.py:1839` | The approved spec's per-item outcome vocabulary has no `needs-approval` token, but `needs_input` fits exactly. STRENGTHENED AT REVIEW BY RUNNING THE DECIDING GREP: `needs_input` is ALREADY THE SHIPPED TOKEN for this meaning, in `run_gates.GATE_STATUS_NEEDS_INPUT` and `run_evidence.AGGREGATE_NEEDS_INPUT` ("Human input or explicit acknowledgement is required (spec 5.6 exit 3)"). So this is not a choice between two defensible names; it is reuse of an existing one. OQ-01 resolved. | grep over `agent_workflows/` for the token |
| F-9 | HIGH | `agy_runipd.py:350`, `:368`; measured identity | **AGY DEFINES NEITHER DEPENDENCY FUNCTION; IT RE-EXPORTS OC'S OBJECTS.** `agy.edge_satisfied is oc.edge_satisfied` -> `True`, `__module__` -> `agent_workflows.oc_runipd`; same for `cascade_dependency_blocked`. So agy has NO dependency call sites, its real `SUCCESS_STATES` uses are FOUR not five, and the plan's "agy `edge_satisfied` twin at `:2275`" points at a docstring about argv. Question (1) has ONE implementation, already shared. | `python3 -c` identity check; the import block read |
| F-10 | HIGH | `agy_runipd.py:295-303`; `tests/test_runner_item_dependencies.py:1633-1664` | **RE-EXPORT FROM `oc_runipd` IS THE ESTABLISHED CONVENTION FOR THIS FAMILY, so E-02's flat "never in `oc_runipd`" prohibition is wrong as an absolute.** The `as <same-name>` form is deliberate and its in-file comment records that `ruff` stripped 6 of these re-exports once and the cross-driver symmetry test caught it immediately; `_SHARED_NAMES` pins both dependency functions by `assertIs`. The real requirement is ONE DEFINITION plus an IDENTITY PIN, not a particular file. | the comment and the test read |
| F-11 | MED | `run_evidence.py:1847-1853`, `:2173-2175` | **THE EXIT-3 MACHINERY ALREADY EXISTS AND ALREADY AGREES WITH THE SPEC**, so OQ-02's feared "unreconciled conflict" is obsolete: `_CLASSIFICATION_EXITS` maps `needs_input: 3`, `_CLASSIFICATION_PRIORITY` makes 3 outrank 1, and `aggregate_run_exit` raises the candidate from an item flag. THE GAP IS ONLY THAT THE DRIVERS NEVER CALL IT (zero call sites in either runner, measured), which is why this plan emits 1 and records 3 as the wiring follow-on. | source read; grep for call sites |
| F-12 | MED | spec `25kzda:484` | The current behavior VIOLATES §3.2, which requires a `reviewed` IPD unattended to "Stop `needs_input`. Exact recovery names the human approval command" and forbids "treating model approval as human approval". That is a stronger warrant than "under-reported" and should be cited in validation. | spec read |
| F-13 | LOW | measured | `'interrupted' in TERMINAL_STATES` -> `False`, so a runner status living OUTSIDE that set is already precedent; E-03 need not widen `TERMINAL_STATES` to carry a durable fact. | `python3 -c` on the constant |

## Proposed changes (ordered, validatable)

1. E-01 classifies the twelve call sites and records the classification at both constants, changing no behavior.
2. E-02 adds ONE shared action-aware predicate in `runner_shared` and routes the exit code, the glyph pair, and `all_success` through it on both hosts.
3. E-03 makes the needs-approval fact explicit and durable on the queue item, under a name the spec already has or a spec-amended one.
4. E-04 pins the cross-host equality and the new predicate's object identity.
5. E-05 tests the measured execute case AND the review-mode control that a naive fix breaks.
6. E-06 mutation-checks both guards.

## Deferred / out of scope (with reason)

- MAKING A `reviewed` PLAN EXECUTABLE. That is the auto-approval bridge (executed plan `97df1z`, `reviewed -> auto-approved` under `--full-auto`), deliberately not widened here. This plan makes the no-op HONEST, not absent.
- The per-artifact output line (child 02 `m85gxh`) and the end-of-run summary (child 03 `bsc457`). This child owns only what a disposition MEANS.
- Unifying the two duplicated constants into one shared object: `rununify` owns the extraction and `cnwy8g` owns the layering. This plan pins their equality instead, which is the cheap durable guard.
- Any change to `determine_action`'s routing. Routing a `reviewed` plan to `execute` is arguably also wrong, but changing it would alter which items a selector picks up, which is a different and larger decision.
- The `render_stream` COMPLETED tuple (`:1872`) and the diagnostics allowlist (`:2152`). The tuple is a RENDERER-local copy of the same idea and pending plan `r2i1b1` is editing that block; child 03 handles the renderer side after `r2i1b1`'s fence is known. Recorded here rather than silently left out, because a reader will notice `reviewed` in that tuple and wonder.

## Scope check

- Over-scope: none. `runner_shared.py` is in scope ONLY to hold the new shared predicate (if E-02 sites it there). Do NOT change `determine_action` or `action_for`.
- Under-scope: stated rather than left as `none`. This child does not make the needs-approval fact appear in `aw runs`, in `--json`, or in the summary table; those are children 02/03 and pending plan `r2i1b1`.
- Under-scope, NAMED AT REVIEW so it is not mistaken for an oversight: the run does NOT return the spec's exit 3 for this case after this plan. The machinery exists and already agrees with the spec (`run_evidence._CLASSIFICATION_EXITS` maps `needs_input: 3`, with 3 outranking 1), but the DRIVERS never call `aggregate_run_exit`, so reaching 3 means wiring them to the shipped aggregator. This plan emits 1, which fixes the measured silent 0, and OQ-02 records the wiring as a discoverable follow-on. Deliberate: wiring the aggregator would change every run's exit classification, far beyond a `reviewed`-item fix.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS not totals (see the corrected baseline in Step 0).
`tests/test_runner_shared.py` holds the cross-host wrapper pins. CORRECTED AT REVIEW: its `INJECTED` map covers EIGHT symbols, not five, and its own comment says so explicitly ("THE COUNT IS 8, NOT THE PLAN'S 5"), the three additions being `git_head`/`git_status`/`git_common_dir` because they call `run_checked` inside the same seam. `test_no_call_site_was_rewritten` counts call sites for those wrapped symbols, so if this plan's edits add or remove one, the count moves and the test says so; reflect it rather than working around it.
`tests/test_runner_refork_guard.py`'s `REFORK_TABLE` is ONE of two possible homes for the new identity pin and is NOT automatically the right one: its contract asserts both that the listed runner has no top-level definition AND that the runner attribute is the owner's object, so it cannot describe a symbol DEFINED in `oc_runipd` and re-exported to agy. `tests/test_runner_item_dependencies.py::_SHARED_NAMES` is the home for that shape. Choose per E-02's siting and say which.
Also run and paste the focused surface: `python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_runner_shared.py tests/test_runner_refork_guard.py tests/test_runner_item_dependencies.py tests/test_runner_stop_level3.py tests/test_runner_stop_level4.py`. The stop-level modules matter because this plan touches the exit-code site they assert.

## Spec / documentation sync

Spec `25kzda` (`.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`, `- Status: approved`) §5.6 owns the per-item outcome vocabulary and the run exit-code table. TWO OBLIGATIONS FOLLOW.
FIRST, OQ-01 decides whether this plan amends it. If E-03 reuses `needs_input`, NO amendment is needed and this section records that; if E-03 needs a new token, the spec file MUST be added to `- Scope-Paths:` before execution, because the runners announce declared spec edits before a run starts and the finalize scope gate reconciles declared against actual.
SECOND, THE EXIT-CODE QUESTION IS SETTLED (OQ-02, resolved) AND NEEDS NO SPEC WORK. §5.6's exit table is already transcribed into `run_evidence._CLASSIFICATION_EXITS` with `needs_input: 3`, and `_CLASSIFICATION_PRIORITY` already makes 3 outrank 1, so the spec and the code AGREE and there is nothing to reconcile. The only gap is that the DRIVERS do not call `aggregate_run_exit` (zero call sites, measured), so this plan emits 1 from the site it changes (which fixes the silent 0) and records 3 as the intended value reachable by wiring the aggregator, a follow-on outside this fence. Do NOT edit `_CLASSIFICATION_EXITS`, and do NOT edit §4.2's finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.
THIRD, AND THIS STRENGTHENS THE PLAN'S WARRANT rather than adding work: §3.2's per-status table makes the current behavior a SPEC VIOLATION, not merely an under-report. For a `reviewed` IPD the unattended action is "Stop `needs_input`. Exact recovery names the human approval command" and the forbidden unattended action is "Self-approval or treating model approval as human approval" (spec `:484`). Counting such an item as a success and exiting 0 is the opposite of that requirement, so this plan moves shipped code INTO compliance with an approved spec. Cite that row in V-02 rather than arguing the case from first principles.

## Open questions

### OQ-01: Does the needs-approval disposition take spec `25kzda` §5.6's `needs_input` name, or a new token requiring a spec amendment?

- Blocking: no
- Status: resolved
- Owner: reviewer (resolved at review 2026-09-08 by running the deciding grep)
- Resolution or deferral rationale: RESOLVED: `needs_input`, no spec amendment, no spec file in `- Scope-Paths:`. The question correctly said the grep "must be run, not guessed", so review ran it, and the result is stronger than either branch anticipated. `needs_input` is not merely present in the approved vocabulary; it is ALREADY THE SHIPPED TOKEN FOR THIS EXACT MEANING in two first-party modules: `run_gates.GATE_STATUS_NEEDS_INPUT = "needs_input"` (`run_gates.py:31`, used at `:157`, `:214`) and `run_evidence.AGGREGATE_NEEDS_INPUT = "needs_input"` (`run_evidence.py:1839`), the latter commented "Human input or explicit acknowledgement is required (spec 5.6 exit 3)" and its item flag glossed "True when a human gate stopped the item". The question's escape hatch (a new token is defensible if `needs_input` is load-bearing for a DIFFERENT case) is therefore closed: it is load-bearing for the SAME case, which is the strongest possible argument for reuse. Spec `25kzda` also names `needs_input` for this row three times (§3.2 `:484`, §5.6 `:1035-1042`, §11 `:1099`), and the parent orchestrator's OQ-01 was resolved identically. If an executor still believes a new token is required, that is a spec amendment and a maintainer decision; STOP rather than choose.

### OQ-02: Should the run's exit code for an all-needs-approval queue be 1 or spec `25kzda`'s 3?

- Blocking: no
- Status: resolved
- Owner: reviewer (resolved at review 2026-09-08 from shipped code)
- Resolution or deferral rationale: RESOLVED: the intended code is 3, and the plan's stated obstacle no longer exists. The question feared an "unreconciled conflict" requiring the executor to prefer 1; measured, the reconciliation is ALREADY DONE IN CODE. `run_evidence._CLASSIFICATION_EXITS` transcribes spec §5.6's run exit table with `needs_input: 3` (`run_evidence.py:1847-1853`, whose comment says "THE ONLY PLACE INTEGERS APPEAR ... Deliberately NOT `run_cli.py`'s inspection-command constants, which mean different things at 3 and 4" - i.e. the two tables were deliberately separated rather than left in conflict), `_CLASSIFICATION_PRIORITY` already makes `needs_input` OUTRANK `item_failure` so 3 beats 1, and `aggregate_run_exit` already raises the `needs_input` candidate from `any(result.item.needs_input ...)` with the reason "a human gate requires input". HONEST LIMIT, which is why this stays non-blocking rather than becoming a requirement: the DRIVERS do not call `aggregate_run_exit` today (measured: zero call sites in either `oc_runipd` or `agy_runipd`; the only mention is a comment), so returning 3 from a driver run means WIRING the drivers to the shipped aggregator, which is larger than this plan's fence. THEREFORE: emit 1 from the exit-code site this plan changes, which fixes the measured silent-0 defect, and record that 3 is the spec-and-code-intended value reachable only by wiring the aggregator, so the follow-on is discoverable rather than lost. Do NOT invent a third exit code and do NOT edit `_CLASSIFICATION_EXITS`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the classification comment as written at BOTH constants. Paste a fresh grep of `SUCCESS_STATES` in both hosts showing the site count and, for each site, which of the five questions the comment assigns it. THE EXPECTED COUNTS ARE SIX REAL READS IN OC AND FOUR IN AGY (excluding each definition and oc's one in-comment mention); if your count differs, say so and explain, since both files are edited by live runs. Paste the identity check `agy.edge_satisfied is oc.edge_satisfied` -> `True` and state explicitly that question (1) has ONE implementation shared by re-export, so the comment does not imply a per-host pair.
  - Observed evidence: |
      THE CLASSIFICATION AS WRITTEN. The tree DRIFTED since this plan was authored in a way that
      changes E-01's shape, so this is reported before the comment: `SUCCESS_STATES` is NO LONGER a
      per-host pair. `rununify` Order 04 (`tx6q0h`) relocated it into `runner_shared` and both hosts
      now re-export the SAME object, so there is ONE definition and therefore ONE classification
      comment, not two. Measured:
        $ python3 -c "from agent_workflows import oc_runipd as oc, agy_runipd as agy, runner_shared as rs; \
            print(oc.SUCCESS_STATES is agy.SUCCESS_STATES, oc.SUCCESS_STATES is rs.SUCCESS_STATES)"
        True True
      The comment is therefore sited at `runner_shared.SUCCESS_STATES` (grep `THE CALL-SITE
      CLASSIFICATION`), where it names all five questions and, per call site, which bar is correct.
      `EXECUTION_SUCCESS_STATES` is still per-host and the comment says so explicitly.

      FRESH GREP, `SUCCESS_STATES` in both hosts (`grep -n SUCCESS_STATES agent_workflows/<host>.py`):
        oc_runipd.py:465  SUCCESS_STATES = runner_shared.SUCCESS_STATES        <- re-export, not a defn
        oc_runipd.py:466  EXECUTION_SUCCESS_STATES = {...}                     <- definition
        oc_runipd.py:3523 required_states = EXECUTION_SUCCESS_STATES if is_exec else SUCCESS_STATES
                                                                               <- QUESTION (1), edge_satisfied
        oc_runipd.py:3706 success_states=EXECUTION_SUCCESS_STATES              <- QUESTION (5), orch dispatch
        oc_runipd.py:4408,4409,4414,4437 in DOCSTRING/COMMENT prose (not reads)
        oc_runipd.py:4439,4441 EXECUTION_SUCCESS_STATES / else SUCCESS_STATES  <- QUESTION (1), cascade
        oc_runipd.py:6663 success_states=EXECUTION_SUCCESS_STATES              <- QUESTION (5)
        oc_runipd.py:6806,6808 in the new zz5yxq COMMENT prose (not reads)
        agy_runipd.py:544  SUCCESS_STATES = runner_shared.SUCCESS_STATES       <- re-export
        agy_runipd.py:545  EXECUTION_SUCCESS_STATES = {...}                    <- definition
        agy_runipd.py:3474 success_states=EXECUTION_SUCCESS_STATES             <- QUESTION (5)
        agy_runipd.py:3601 in the new zz5yxq COMMENT prose (not a read)

      THE COUNT DIFFERS FROM THE PLAN'S EXPECTED "SIX IN OC AND FOUR IN AGY", and this V-item
      requires me to say so and explain. The plan expected the glyph pair, the exit code and the
      `all_success` read to be found IN EACH HOST. They are not there any more: all three moved into
      SHARED code before this plan ran. The glyph pair and the exit-code/`all_success` bodies now live
      in `runner_shared` (`execute_item_core`, `render_continuation_hint`), so questions (3) and (4)
      have ONE site each serving BOTH hosts rather than a per-host pair, and question (2)'s per-host
      site now passes a shared projection rather than reading the constant by name. So the remaining
      BARE-NAME reads in the hosts are only questions (1) and (5). This is a relocation, not a missing
      site: every one of the five questions is still asked, and each is named in the comment with
      where it now lives.

      QUESTION (1) HAS ONE IMPLEMENTATION, SHARED BY RE-EXPORT, as the plan's F-9 states:
        $ python3 -c "from agent_workflows import oc_runipd as oc, agy_runipd as agy; \
            print(agy.edge_satisfied is oc.edge_satisfied, agy.cascade_dependency_blocked is oc.cascade_dependency_blocked)"
        True True
      The classification comment states this explicitly ("ONE IMPLEMENTATION, not a per-host pair")
      so it does not imply a per-host pair. NO BEHAVIOR WAS CHANGED BY E-01.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the new predicate as written and its ACTUAL location, stating which home E-02 chose and why (`runner_shared` preferred, or `oc_runipd` with a pinned re-export if it must sit beside `edge_satisfied`). Paste a `python3 -c` showing it resolves to the SAME object from every module that exposes it. Then paste FOUR evaluations: a `reviewed` EXECUTE item failing all three of exit-code success, checkmark glyph, and `all_success`; and a `reviewed` REVIEW item satisfying all three. Show the exit code for an all-`reviewed`-execute queue is nonzero, pasting the actual returned integer, and state that it is 1 per OQ-02 with 3 recorded as the aggregator-wiring follow-on. CITE spec `25kzda:484` (§3.2's `reviewed` row requiring "Stop `needs_input`") as the requirement this satisfies, so the change is justified against the approved contract rather than from first principles.
  - Observed evidence: |
      THE PREDICATE AND ITS ACTUAL LOCATION. Three functions in `agent_workflows/runner_shared.py`,
      the plan's PREFERRED home, plus the constant they select:

        EXECUTE_REPORTING_SUCCESS_STATES: frozenset[str] = frozenset(
            SUCCESS_STATES - {"reviewed"}
        )

        def success_states_for_action(action: str | None) -> Container[str]:
            return SUCCESS_STATES if action == "review" else EXECUTE_REPORTING_SUCCESS_STATES

        def item_reached_success(item: Mapping[str, Any]) -> bool:
            status = item.get("status")
            return isinstance(status, str) and status in success_states_for_action(
                item.get("action")
            )

        def exit_code_statuses(queue: Sequence[Mapping[str, Any]]) -> list[str]:
            projected: list[str] = []
            for item in queue:
                status = item.get("status")
                if status == "queued":
                    projected.append("queued")
                elif item_reached_success(item):
                    projected.append(EXIT_SUCCESS_TOKEN)
                else:
                    projected.append(str(status))
            return projected

      WHICH HOME AND WHY: `runner_shared`, not `oc_runipd`. The plan permitted either (F-10) and made
      the deciding factor whether the predicate must sit beside `edge_satisfied` to reuse its
      selection without a circular import. It does not: the selection is one comparison on
      `item["action"]`, `runner_shared` already owns `determine_action`/`action_for` (the same family
      of decision), and both hosts already import it. So the PREFERRED home was available and is used,
      and the `oc`-owned re-export escape hatch was not needed. Both hosts bind the names with the
      `as <same-name>` form; there is NO second copy in agy.

      ONE OBJECT FROM EVERY MODULE THAT EXPOSES IT:
        $ python3 -c "from agent_workflows import oc_runipd as oc, agy_runipd as agy, runner_shared as rs; \
            [print(n, getattr(oc,n) is getattr(rs,n), getattr(agy,n) is getattr(rs,n), getattr(rs,n).__module__) \
             for n in ('success_states_for_action','item_reached_success','item_needs_approval','exit_code_statuses')]"
        success_states_for_action True True agent_workflows.runner_shared
        item_reached_success      True True agent_workflows.runner_shared
        item_needs_approval       True True agent_workflows.runner_shared
        exit_code_statuses        True True agent_workflows.runner_shared

      THE FOUR EVALUATIONS THIS V-ITEM DEMANDS. A `reviewed` EXECUTE item fails all three of the
      execute-action sites, and a `reviewed` REVIEW item satisfies all three:
        (a) EXIT CODE, driven through the REAL loop on BOTH hosts
            (`AnApprovalBlockedQueueIsNotASilentSuccess::test_a_reviewed_EXECUTE_item_is_not_counted_as_a_success`):
            an all-`reviewed`-EXECUTE queue returns the ACTUAL INTEGER 1, with `self.turns == []`
            proving no turn ran; the review control returns 0.
        (b) CHECKMARK GLYPH: `item_reached_success({"action":"execute","status":"reviewed"})` -> False
            (so the glyph is the non-success bullet), and `{"action":"review",...}` -> True.
        (c) `all_success`: `ContinuationHintTests::test_a_reviewed_but_unapproved_execute_item_offers_RESUME_not_inspect`
            asserts the EXECUTE case renders `aw oc run resume ...` and NOT `aw runs`, while the
            REVIEW case still renders `aw runs run-xyz` and not `resume`.
        Direct evaluation of the shared bar:
        $ python3 -c "from agent_workflows import runner_shared as rs; \
            [print(a, rs.item_reached_success({'action':a,'status':'reviewed'})) for a in ('execute','review')]"
        execute False
        review True

      THE ACTUAL RETURNED INTEGER IS 1, per OQ-02, and 3 is recorded as the aggregator-wiring
      follow-on:
        $ python3 -c "from agent_workflows import runner_shared as rs, runner_stop; \
            q=[{'action':'execute','status':'reviewed'}]*2; \
            print(runner_stop.deliberate_stop_exit_code(rs.exit_code_statuses(q), success_states={rs.EXIT_SUCCESS_TOKEN}, stopped=False))"
        1
      Spec `25kzda` 5.6's exit 3 for `needs_input` is reachable only by wiring the drivers to
      `run_evidence.aggregate_run_exit`, which neither driver calls; that is outside this fence and
      recorded in the constant's docstring so the follow-on is discoverable.

      THE REQUIREMENT THIS SATISFIES, cited rather than argued from first principles: spec `25kzda`
      3.2 (`:484`), the `reviewed` row, requires the unattended action to be "Stop `needs_input`.
      Exact recovery names the human approval command" and forbids "Self-approval or treating model
      approval as human approval". Counting such an item a success and exiting 0 was the opposite of
      that requirement, so this moves shipped code INTO compliance with an approved spec.

      A DEVIATION FROM E-02 AS WRITTEN, REPORTED BECAUSE IT CHANGES THE DESIGN. E-02 says to use
      `EXECUTION_SUCCESS_STATES` for the execute branch, "the selection shape `edge_satisfied` and
      `cascade_dependency_blocked` already use". I used the SELECTION SHAPE but NOT that SET, and the
      reason is measured, not stylistic: those two answer the DEPENDENCY question ("may a dependent
      run now?"), for which `substantially-complete` legitimately counts. This is the REPORTING
      question, for which it deliberately does NOT, and that is a PINNED CONTRACT. I implemented E-02
      literally first, and it FAILED an existing test:
        FAILED tests/test_rununify_run_queue_characterization.py::TheExitCodeReflectsTheRealOutcome::
               test_the_exit_code_reads_SUCCESS_STATES_not_EXECUTION_SUCCESS_STATES
        AssertionError: 0 == 0 : oc_runipd: the exit code is computed from SUCCESS_STATES, which does
        NOT contain substantially-complete; a 0 here means the wrong constant was used
      That test exists precisely to pin `substantially-complete` as a NONZERO exit. So the literal
      E-02 would have fixed one silent success (`reviewed`) by introducing another
      (`substantially-complete`). The bar used is therefore `SUCCESS_STATES - {"reviewed"}`, DERIVED BY
      SUBTRACTION so it cannot drift from `SUCCESS_STATES`, which narrows exactly the one status for
      exactly the one action the plan set out to fix and widens nothing. Recorded as DECISION
      2-zz5yxq-D1.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the durable needs-approval fact as it appears in a real `state.json` queue entry, not as a code snippet. The name is `needs_input` (OQ-01 resolved at review); paste the token as actually written and confirm it matches `run_gates.GATE_STATUS_NEEDS_INPUT` byte for byte, so the runner and the gate vocabulary cannot drift. State whether the existing `run_evidence.AggregatedItem.needs_input` carrier was reusable, either way. If `TERMINAL_STATES` was widened, paste the measurement of its readers (`cascade_dependency_blocked` and `decide_orchestrator_dispatch`) showing the widening changed neither dependency nor retirement behavior; if it was not widened, say so and cite the `interrupted` precedent.
  - Observed evidence: |
      THE DURABLE FACT IN A REAL `state.json`, not a code snippet. Drove each host's REAL
      `initialize_run` with `--prepare-only` over a temp repo holding one `- Status: reviewed` plan
      (`rev001`) and one `- Status: approved` plan (`app002`), then read the frozen queue off disk:

        === agent_workflows.oc_runipd: run-20260918T214549Z-400247/state.json queue ===
        {"id6": "rev001", "initial_status": "reviewed", "action": "execute", "status": "reviewed", "needs_input": true}
        {"id6": "app002", "initial_status": "approved", "action": "execute", "status": "queued", "needs_input": false}
        === agent_workflows.agy_runipd: run-20260918T214549Z-400247/state.json queue ===
        {"id6": "rev001", "initial_status": "reviewed", "action": "execute", "status": "reviewed", "needs_input": true}
        {"id6": "app002", "initial_status": "approved", "action": "execute", "status": "queued", "needs_input": false}

      THE TOKEN, BYTE FOR BYTE against the two modules that already own it (OQ-01 resolved):
        $ python3 -c "from agent_workflows import runner_shared as rs, run_gates, run_evidence; \
            print(repr(rs.NEEDS_INPUT_TOKEN), rs.NEEDS_INPUT_TOKEN == run_gates.GATE_STATUS_NEEDS_INPUT, \
                  rs.NEEDS_INPUT_TOKEN == run_evidence.AGGREGATE_NEEDS_INPUT)"
        'needs_input' True True
      Pinned by `tests/test_runner_shared.py::CrossHostSuccessBarEqualityTests::
      test_the_needs_input_token_is_the_one_the_package_already_ships`, which asserts against those
      modules rather than against a literal repeated in the test, so the runner and the gate
      vocabulary cannot drift. NO SPEC FILE WAS EDITED.

      WAS `run_evidence.AggregatedItem.needs_input` REUSABLE? NO, and the plan required an answer
      either way. `AggregatedItem` is an INPUT type to `run_evidence.aggregate_run_exit`, and measured,
      neither driver constructs one or calls that aggregator (zero call sites; the only mention in
      either runner is a comment). So there is no existing carrier reaching durable run state to wire
      up. What I added instead is a boolean on the queue entry under the SAME token, so when the
      drivers are later wired to the aggregator the value maps onto `AggregatedItem.needs_input`
      without a rename.

      `TERMINAL_STATES` WAS NOT WIDENED, and the `interrupted` precedent the plan cites is why:
        $ python3 -c "from agent_workflows import runner_shared as rs; \
            print('interrupted' in rs.TERMINAL_STATES, 'needs_input' in rs.TERMINAL_STATES)"
        False False
      The fact is carried BESIDE the status rather than AS one, so `cascade_dependency_blocked` and
      `decide_orchestrator_dispatch` (the two readers the plan names) see an unchanged vocabulary and
      neither dependency nor retirement behavior moves. The queue status stays `reviewed`, which
      `runner_shutdown.KNOWN_ITEM_STATUSES` already admits, so Phase 0's R3 ledger-coherence check and
      a resume are both unaffected.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the equality test and the object-identity assertion, and paste them PASSING. Then paste the pre-change measurement (`is` -> False, `==` -> True) so the reader can see what the test pins and what it deliberately does not.
  - Observed evidence: |
      THE PINS, in `tests/test_runner_shared.py::CrossHostSuccessBarEqualityTests`, PASSING:
        $ python3 -m pytest tests/test_runner_shared.py::CrossHostSuccessBarEqualityTests -o addopts="" -q
        ....                                                                     [100%]
        4 passed in 0.23s

      THE PRE-CHANGE MEASUREMENT, so a reader can see what the test pins and what it deliberately
      does not:
        $ python3 -c "from agent_workflows import oc_runipd as oc, agy_runipd as agy; \
            print('SUCCESS_STATES  is:', oc.SUCCESS_STATES is agy.SUCCESS_STATES, '==:', oc.SUCCESS_STATES == agy.SUCCESS_STATES); \
            print('EXECUTION_      is:', oc.EXECUTION_SUCCESS_STATES is agy.EXECUTION_SUCCESS_STATES, '==:', oc.EXECUTION_SUCCESS_STATES == agy.EXECUTION_SUCCESS_STATES)"
        SUCCESS_STATES  is: True  ==: True
        EXECUTION_      is: False ==: True
      NOTE THE FIRST LINE HAS CHANGED SINCE THE PLAN WAS WRITTEN. The plan measured `is -> False` for
      BOTH pairs; `SUCCESS_STATES` is now ONE OBJECT (relocated by `rununify` `tx6q0h`), so for it the
      test asserts the STRONGER `assertIs` against `runner_shared`'s object. `EXECUTION_SUCCESS_STATES`
      is still duplicated, so equality is the strongest true statement available and is what is
      asserted, together with an `assertIsNot` that RECORDS the present duplication so a future
      unification fails loudly instead of silently under-asserting.

      THE OBJECT-IDENTITY ASSERTION FOR THE NEW PREDICATE, by `assertIs` and not by grep:
      `test_the_action_aware_bar_is_the_SAME_OBJECT_from_every_module_that_exposes_it` checks all four
      names resolve to `runner_shared`'s object from BOTH hosts and that `__module__` is
      `agent_workflows.runner_shared`. Measured:
        success_states_for_action True True agent_workflows.runner_shared
        item_reached_success      True True agent_workflows.runner_shared
        item_needs_approval       True True agent_workflows.runner_shared
        exit_code_statuses        True True agent_workflows.runner_shared

      WHICH HOME, AND WHY, as the plan requires me to state. `tests/test_runner_refork_guard.py`'s
      `REFORK_TABLE`, plus the behavioral restatement above. The plan said `REFORK_TABLE` "cannot
      describe a symbol DEFINED in `oc_runipd` and re-exported to agy" - correct, and NOT the case
      here: E-02 sited the predicate in `runner_shared`, so the OWNER is a non-runner module and BOTH
      halves of that table's contract apply unchanged (no runner-local definition, and the runner
      attribute IS the owner's object). `_SHARED_NAMES` in
      `tests/test_runner_item_dependencies.py` is for `oc_runipd`-OWNED names and would have been the
      home only under the other siting decision, so it was correctly not used. Four rows added,
      passing:
        $ python3 -m pytest tests/test_runner_refork_guard.py -o addopts="" -q
        9 passed
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste both tests per host and their actual runner output. The REVIEW-MODE CONTROL is the load-bearing half: paste it passing and state explicitly that it covers the failure the docstring at `oc_runipd.py:4186` records (run `run-20260904T042705Z-1025943`). A V-05 that pastes only the execute case is incomplete.
  - Observed evidence: |
      BOTH TESTS, PER HOST, in `tests/test_rununify_run_queue_characterization.py::
      AnApprovalBlockedQueueIsNotASilentSuccess`. Each runs against BOTH hosts through `subTest`, so
      "two tests per host" is satisfied by parameterization rather than duplication, matching the
      file's established convention.

      BUILT FROM THE REAL QUEUE SHAPE, not a hand-written dict alone: the execute-case test asserts
      the fixture against the two REAL functions that produce it, so it breaks if the admission tuple
      changes:
        self.assertEqual(module.action_for("child", "reviewed"), "execute")
        self.assertEqual(module.runner_shared.initial_queue_status("reviewed"), "reviewed")

      ACTUAL RUNNER OUTPUT:
        $ python3 -m pytest "tests/test_rununify_run_queue_characterization.py::AnApprovalBlockedQueueIsNotASilentSuccess" -o addopts="" -q
        ...                                                                      [100%]
        3 passed in 0.44s

      THE EXECUTE CASE asserts `self.turns == []` (no turn ran), `rc != 0`, `rc == 1` (OQ-02), and that
      both statuses are still `reviewed` on disk, i.e. NO STATUS WAS REWRITTEN to manufacture the
      nonzero exit (spec `c4gd2h` R22).

      THE REVIEW-MODE CONTROL, which is the load-bearing half: `test_a_reviewed_REVIEW_item_is_still_a_success`
      drives an all-`review`-action queue whose items reach `reviewed`, and asserts BOTH items were
      dispatched AND `rc == 0`. IT COVERS THE FAILURE THE IN-TREE DOCSTRING RECORDS: run
      `run-20260904T042705Z-1025943`, a 6-item all-`review` run of the `wslayout` Set that reviewed
      Orders 00 and 01 and then killed Orders 02-05 the instant Order 01 reached `reviewed`, because
      that site hardcoded the execution bar. Its failure message names that run id, so a future
      regression points straight at the precedent. (The docstring is now at
      `cascade_dependency_blocked`, roughly `oc_runipd.py:4400-4420`, not the plan's `:4186`; re-located
      by symbol as the plan instructs.)

      A THIRD TEST states the two halves as ONE assertion so the distinction cannot be lost by editing
      one of them, and additionally pins that `substantially-complete` is STILL a non-success for
      reporting and that the execute reporting bar is exactly `{executed, approved}`.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: for EACH of the two guards, paste the mutation, the FAILING output under it, the revert, and the passing output after. Two mutations, two failures, two passes, all four outputs pasted verbatim.
  - Observed evidence: |
      TWO MUTATIONS, TWO FAILURES, TWO PASSES AFTER REVERT. All four outputs verbatim.

      MUTATION 1, for E-04's equality pin: edit ONE host's constant alone.
        agy_runipd.py: EXECUTION_SUCCESS_STATES = {"executed", "substantially-complete"}
                    -> EXECUTION_SUCCESS_STATES = {"executed", "substantially-complete", "partial"}
      FAILING OUTPUT UNDER THE MUTATION:
        $ python3 -m pytest tests/test_runner_shared.py::CrossHostSuccessBarEqualityTests -o addopts="" -q
        >       self.assertEqual(
                    oc_runipd.EXECUTION_SUCCESS_STATES, agy_runipd.EXECUTION_SUCCESS_STATES
                )
        E       AssertionError: Items in the second set but not the first:
        E       'partial'
        FAILED tests/test_runner_shared.py::CrossHostSuccessBarEqualityTests::
               test_EXECUTION_SUCCESS_STATES_is_EQUAL_on_both_hosts_even_though_duplicated
        1 failed, 3 passed in 0.36s
      AFTER REVERT:
        $ python3 -m pytest tests/test_runner_shared.py::CrossHostSuccessBarEqualityTests -o addopts="" -q
        ....                                                                     [100%]
        4 passed in 0.23s

      MUTATION 2, for E-05's execute-case test: revert the E-02 predicate to the unconditional read.
        runner_shared.success_states_for_action:
          return SUCCESS_STATES if action == "review" else EXECUTE_REPORTING_SUCCESS_STATES
       -> return SUCCESS_STATES  # MUTATION: the pre-zz5yxq unconditional read
      FAILING OUTPUT UNDER THE MUTATION, which reproduces the ORIGINAL DEFECT EXACTLY:
        $ python3 -m pytest "tests/test_rununify_run_queue_characterization.py::AnApprovalBlockedQueueIsNotASilentSuccess" \
              tests/test_oc_runipd.py::ContinuationHintTests -o addopts="" -q
        >               self.assertNotEqual(
                            rc,
                            0,
                            f"{label}: a queue of `reviewed`-but-unapproved EXECUTE items did NO WORK, so "
                            "exit 0 would report a silent success (backlog em0z50)",
                        )
        E               AssertionError: 0 == 0 : oc_runipd: a queue of `reviewed`-but-unapproved EXECUTE
                        items did NO WORK, so exit 0 would report a silent success (backlog em0z50)
        FAILED tests/test_oc_runipd.py::ContinuationHintTests::test_a_reviewed_but_unapproved_execute_item_offers_RESUME_not_inspect
        FAILED tests/test_rununify_run_queue_characterization.py::AnApprovalBlockedQueueIsNotASilentSuccess::test_a_review_run_that_reached_reviewed_and_an_execute_one_get_OPPOSITE_verdicts
        FAILED tests/test_rununify_run_queue_characterization.py::AnApprovalBlockedQueueIsNotASilentSuccess::test_a_reviewed_EXECUTE_item_is_not_counted_as_a_success
        3 failed, 7 passed in 0.60s
      The `0 == 0` is the measured incident itself, which is the strongest available evidence that the
      guard catches the thing it exists for. Note the mutation ALSO fails the `all_success` guard,
      confirming both surfaces are genuinely routed through the one predicate.
      AFTER REVERT:
        $ python3 -m pytest "tests/test_rununify_run_queue_characterization.py::AnApprovalBlockedQueueIsNotASilentSuccess" \
              tests/test_oc_runipd.py::ContinuationHintTests -o addopts="" -q
        ..........                                                               [100%]
        10 passed in 0.46s
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: the bare `python3 -m pytest` summary line pasted, showing the three named node ids PASSING and no new failure elsewhere; plus the diff of each of the three tests, showing the recorded reason for the contract change. State explicitly that no assertion was deleted to achieve this, and that `EXPECTED_KEYS` grew to include `needs_input` rather than the shape check being removed. If any of the three does NOT need changing because the implementation took a different route, say which and why rather than editing it anyway.
  - Observed evidence: |
      THE BARE SUITE SUMMARY LINE, pasted:
        $ python3 -m pytest
        8122 passed, 3 skipped, 2 xfailed in 295.50s (0:04:55)
      THE PRE-CHANGE BASELINE, measured in THIS worktree before any edit:
        $ python3 -m pytest
        8114 passed, 3 skipped, 2 xfailed in 278.46s (0:04:38)
      BOTH ARE FULLY GREEN, so comparing failing NODE IDS is trivial: the failing set was EMPTY
      before and is EMPTY after. The +8 is this plan's new tests. NOTE this baseline is BETTER than
      the one the plan's Step 0 records (it expected 2 pre-existing failures, and the prior attempt
      saw 31 phantom ones from `AW_EXECUTION_ROLE=worker` leaking into pytest); both have since been
      fixed upstream, which is why the 3 real failures the prior attempt could not distinguish were
      plainly visible this time.

      FOUR TESTS PINNED THE OLD CONTRACT, NOT THREE, and the deviation is reported rather than
      quietly absorbed. Each was updated as a deliberate contract change with the reason recorded IN
      THE TEST, and NO ASSERTION WAS DELETED to achieve a green suite.

      (1) `tests/test_rununify_initialize_run_characterization.py::
          TheFrozenQueueEntryShapeIsIdenticalOnBothHosts` - `EXPECTED_KEYS` grew from 12 to 13 by
          ADDING `needs_input`, exactly as this V-item requires, rather than the shape check being
          removed. The assertion is still an exact `assertEqual` against a frozen set, so the next
          unannounced key still fails. The test NAME moved with the count
          (`..._twelve_keys` -> `..._thirteen_keys`), since a test named for twelve asserting
          thirteen would be the real weakening. The class docstring now records why the addition is a
          deliberate compatibility change and why adding a key is the SAFE direction for a resume.
      (2) `tests/test_oc_runipd.py::ContinuationHintTests::test_single_session_success` - the FIXTURE
          changed `reviewed` -> `executed`, NOT the assertion. Its docstring records that `reviewed`
          was the pre-`zz5yxq` contract and that relaxing the `assertNotIn("resume")` instead would
          have deleted the only coverage of the inspect-vs-resume branch. A NEW test covers the
          `reviewed` case in both directions.
      (3) `tests/test_rununify_run_queue_characterization.py::TheExitCodeReflectsTheRealOutcome::
          test_the_exit_code_reads_SUCCESS_STATES_not_EXECUTION_SUCCESS_STATES` - DID NOT NEED
          CHANGING, and this V-item asks me to say which and why. E-07 predicted its
          `set(module.SUCCESS_STATES) == {"reviewed","approved","executed"}` assertion would have to
          move. It did not, because the implementation took a different route: `reviewed` was NEVER
          removed from `SUCCESS_STATES` (F-5 forbids it), and the reporting bar is a SEPARATE derived
          constant. The test is UNTOUCHED and passing. It also did real work: it is the test that
          CAUGHT the literal-E-02 implementation (see V-02's deviation note), so leaving it intact is
          the point.
      (4) `tests/test_rununify_run_queue.py::TheClosureClassificationIsPinned` - NOT NAMED BY E-07,
          found by running the suite. It pins the symbols `run_queue` closes over, and
          `SUCCESS_STATES` legitimately left that closure when the exit-code site began calling the
          shared projection. Removed from `EQUAL_CONSTANTS` with the reason recorded. Its census
          asserts a total of 41; the honest repair was to classify `_integrate_stranded_lanes`, a
          REAL PRE-EXISTING fork (measured: each host defines its own, NOT the same object) that the
          table had never listed, rather than to lower `CLOSURE_TOTAL`, which would have hidden a
          fork. Verified the omission pre-dated my change by re-measuring at the stashed baseline.
        $ python3 -m pytest tests/test_rununify_run_queue.py -o addopts="" -q
        32 passed in 2.23s
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the paths in `- Scope-Paths:`. Do NOT remove `reviewed` from `SUCCESS_STATES` (F-5). Do NOT change `determine_action` or `action_for`. Do NOT make a `reviewed` plan executable. Do NOT define a SECOND copy of the new predicate in `agy_runipd` (a single definition plus an identity pin is the requirement; note the earlier flat ban on siting anything in `oc_runipd` was CORRECTED at review, see F-10, because re-export from `oc_runipd` is this family's pinned convention). Do NOT edit `render_stream.py` (child 03 and pending plan `r2i1b1` own that surface). Do NOT edit `run_evidence._CLASSIFICATION_EXITS` or wire the drivers to `aggregate_run_exit` (OQ-02 records that as a follow-on outside this fence). Do NOT edit spec `25kzda` at all, since OQ-01 resolved to the shipped `needs_input` and no amendment is needed, and never its §4.2 finding-code table.
NOTE `tests/test_runner_item_dependencies.py` and `tests/test_runner_stop_level3.py`/`level4.py` are NOT in `- Scope-Paths:`. If E-04's identity pin belongs in the first (the likely case if E-02 sites the predicate beside `edge_satisfied`), or if the exit-code change requires touching a stop-level assertion, MAKE THE EDIT AND JUSTIFY IT with `--scope-reason`; they were deliberately left undeclared because the choice depends on E-02's siting decision, which is the executor's to make. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN, INCLUDING THE CORRECTED ONES. This is not boilerplate: review re-resolved every coordinate and found EVERY oc line number in the original E-01 wrong (`:327`->`:336`, `:3373`->`:3377`, `:4219`->`:4275`, `:6743`/`:6746`->`:6943`/`:6946`, `:7296`->`:7496`, `:7377`->`:7577`), plus `runner_shared.py:2727`/`:2735`->`:2969`/`:2977` and the agy exit code `:4509`->`:4515`. Find `SUCCESS_STATES`, `EXECUTION_SUCCESS_STATES`, `edge_satisfied`, `cascade_dependency_blocked`, `determine_action`, `action_for`, `render_continuation_hint`, and `deliberate_stop_exit_code` by name.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved zz5yxq --by-human --message ...`) before execution. The `- Readiness: go-pending-approval` field now present was written by `/plan-review` on 2026-09-08 as its attested output; do not hand-edit it. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. Do NOT close backlog `em0z50` here: its fixes (b) and (c) ship in children 02 and 03, and closing it after this plan would claim reporting behavior no code yet produces.
