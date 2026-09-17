# IPD: Give the review integration path the deferral ladder the execute path already has and stop promising a retry that never happens

- Date: 2026-09-17
- Kind: child
- Concern: A review turn whose integration is refused by a TRANSIENT condition is stranded permanently, while the identical refusal on an execute turn is retried automatically. The refusal message tells the operator "it is re-attempted once the base is clean" (`runner_shared.py:555`), and on the review path nothing ever re-attempts it: the review integration call site (`oc_runipd.py:7591-7625`) records the refusal, prints it, and moves on, never calling `decide_integration_deferral`, never setting `integration-deferred`, and never reaching `reattempt_deferred_integrations`. Measured 2026-09-17 in run `run-20260917T193010Z-1207513`: the review of plan `63425h` completed and cost $13.27 / 32m46s, then reported `integration-blocked` with git's own "main has uncommitted local changes" text plus a `fatal: stash failed`, and the review sat unmerged on `aw/lane/review-sweep-run-20260917T193010Z-1207513` until a human noticed and merged it by hand. An unmerged review is invisible to `aw att`, which is the same stranding that hid plans `4fodkt` and `63425h` earlier the same day.
- Scope: Route the review path's integration refusal through the SAME shared deferral ladder the execute path uses, so a transient refusal defers and is re-attempted rather than being terminal on first contact; and make the operator-facing report name the actual condition, its remedy, and the verb that recovers it. Does NOT change the ladder's rung logic, its budget, its policy flag, the execute path, or what counts as a transient refusal.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, tests/test_review_lane_isolation.py
- Item-Dependencies: none
- Blocks-Release: next
- Status: to-review
- Set: revladder
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: i4ak5n

## Workflow history

- 2026-09-17 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from a measured incident and filed at the maintainer's instruction after they observed the same failure "several times now". I CORRECTED MY OWN DIAGNOSIS TWICE WHILE INVESTIGATING, and both corrections matter because each wrong version would have produced a wrong plan. FIRST I claimed the ladder ignores the `integration-blocked` STATUS because `deferred_integration_items` (`:2464`) filters on `integration-deferred` only. That is true but not the defect: `INTEGRATION_REFUSAL_TRANSIENT` IS the string `'integration-blocked'`, and `classify_integration_refusal('integration-blocked')` returns True, so the refusal KIND is correctly recognized as transient. The status and the kind share a spelling, which is what misled me. SECOND I assumed the wiring was shared. It is not: `retry_deferred_integrations` is called from the EXECUTE dispatch loop only (`oc_runipd.py:8395` rung 1, `:8463` rungs 2 and 3), and the review path calls `integrate_review_lane_branch` (`:7591`) and then, on refusal, only records and prints (`:7614-7625`). Verified by scanning that call site for any deferral reference: none. So the ladder is sound and complete; the review path simply never enters it.

## Goal

Make a refused review integration recover by itself, the way a refused execute integration already
does, and make the message the operator reads true.

The ladder is not missing, and this plan must not rebuild it. `reattempt_deferred_integrations`
(`runner_shared.py:2714`) already implements three rungs, already re-attempts at the top of the dispatch
loop for free, already routes every re-attempt through the full merge-and-revalidate gate, and already
bounds itself with a budget and an operator policy flag. The review path is simply not wired to it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the asymmetry from the code before changing either path

- [ ] E-01 PROVE THE ASYMMETRY AT EXECUTION HEAD, and refuse to proceed on this plan's line numbers. Show that an `integration-blocked` refusal from an EXECUTE turn reaches `decide_integration_deferral` and can become `integration-deferred`, and that the SAME refusal from a REVIEW turn does not: scan the review integration call site for any reference to `decide_integration_deferral`, `INTEGRATION_DEFERRED_STATUS`, or `reattempt_deferred_integrations` and show there is none. Do this on BOTH hosts, because the fix must land on both and the two call sites are separate code.
  - Depends on: none
  - Expected outcome: a pasted per-host comparison naming the execute call site that enters the ladder and the review call site that does not, with the scan that proves the absence.
  - Execution state: pending

- [ ] E-02 CONFIRM THE KIND IS ALREADY CLASSIFIED TRANSIENT, so the fix does not touch `classify_integration_refusal` and cannot widen what defers. Show `classify_integration_refusal(INTEGRATION_REFUSAL_TRANSIENT)` is True, that `INTEGRATION_REFUSAL_TRANSIENT` equals the string the git-refused-to-start arm returns (`runner_shared.py:2230-2233`), and that `merge-conflict` remains False. This is the measurement that keeps the fix to WIRING rather than to POLICY, and it is the one I got wrong first, so verify it rather than inheriting it.
  - Depends on: none
  - Expected outcome: pasted values showing the transient kind, the conflict kind, and the classifier's verdict for each, plus the arm that returns the transient kind quoted.
  - Execution state: pending

### Task group 2: wire the review path into the existing ladder, changing no rung logic

- [ ] E-03 ROUTE A REFUSED REVIEW INTEGRATION THROUGH `decide_integration_deferral`, exactly as the execute path does, and honor its verdict: a `deferred` decision writes `INTEGRATION_DEFERRED_STATUS` and leaves the lane preserved for re-attempt; a terminal decision keeps today's behavior unchanged. Reuse the shared decision function and the shared status constants; do NOT add a second decision site, a review-specific policy, or a review-specific budget. The four terminal reasons the shared function already enforces (non-transient kind, `--on-integration-blocked=block`, budget exhausted, budget zero) must apply to the review path with no exception carved out.
  - Depends on: E-01, E-02
  - Expected outcome: a refused review integration whose kind is transient records `integration-deferred` with the shared reason string; a `merge-conflict` refusal and a `block` policy each stay terminal, all three pasted.
  - Execution state: pending

- [ ] E-04 MAKE THE REVIEW ITEM REACHABLE BY THE LADDER, which is the half that actually performs the retry and the half a wiring change can silently miss. `deferred_integration_items` selects queue items whose `status` is `INTEGRATION_DEFERRED_STATUS`, and `reattempt_deferred_integrations` rebuilds each lane from the durable `preserved_*` fields rather than from memory. Verify a deferred REVIEW item is selected by that filter and that its lane is reconstructible from what the review path wrote; if the review path does not write the `preserved_*` fields the reconstruction needs, write them. A deferred item the ladder cannot see or cannot rebuild is worse than today's honest refusal, because the promise is then made twice.
  - Depends on: E-03
  - Expected outcome: pasted evidence that a deferred review item appears in `deferred_integration_items` and that `handle_for` rebuilds its lane, followed by a successful re-attempt once the blocking dirt is cleared.
  - Execution state: pending

- [ ] E-05 MIRROR THE WIRING ON THE ANTIGRAVITY HOST, in its own item because it is a separate call site and a fix landing on one host only is the drift this repository's `rununify` Set exists to remove. Prefer extending the SHARED function both hosts call over adding a second per-host branch; if the two call sites genuinely differ, state how and why in the execution note rather than forcing a false symmetry.
  - Depends on: E-03, E-04
  - Expected outcome: the same three cases from E-03 pasted for the Antigravity host, plus a statement of whether the wiring is shared or per-host and why.
  - Execution state: pending

### Task group 3: make the report tell the operator what to do

- [ ] E-06 REPORT THE DEFERRAL AND THE REMEDY, not just the refusal. The current message states the condition and then promises a re-attempt; once E-03 lands, that promise is true and the report should say which rung is pending and what clears it. Where a refusal is TERMINAL, the report must name the concrete recovery: the preserved lane branch, the verb that integrates it (`aw <host> run integrate <id6>`, per approved plan `rl67b0`), and the fact that a clean base is the precondition. ALSO NAME WHAT IS NOT OURS: the incident's `fatal: stash failed` line comes from `pre-commit`'s own stash handling, not from any runner code (verified: no runner module contains that string), so an operator hunting our code for it is wasting time. Say whose message it is.
  - Depends on: E-03
  - Expected outcome: pasted operator-facing output for a deferred review integration and for a terminal one, each naming the lane branch, the recovery verb, and the precondition; plus the `fatal: stash failed` attribution stated once where it will be read.
  - Execution state: pending

- [ ] E-07 SURFACE A STRANDED REVIEW IN THE RUN SUMMARY, because the measured cost of this defect was invisibility rather than the refusal itself. The run that stranded `63425h` reported `Outcome: COMPLETED` with `1 reviewed` and no blocked items, so nothing in the summary said a review's work was sitting on a lane. Make a review whose integration did not land visible in the end-of-run report with its lane named. Do NOT change the run's overall outcome verdict in this item: whether an unintegrated review makes a run non-COMPLETED is a separate judgement, and approved plan `ys1dor` already owns reporting a run whose work never landed.
  - Depends on: E-06
  - Expected outcome: a run whose review integration was refused shown reporting that fact in its summary with the lane named, pasted; and an explicit statement that the overall outcome verdict was not changed here.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE LADDER IS ALREADY BUILT AND ALREADY CHEAP. `reattempt_deferred_integrations` (`runner_shared.py:2714`) is called from the TOP of the dispatch loop, and its docstring records why rung 1 costs nothing: "that loop already reloads state and already runs `cascade_dependency_blocked` each iteration, so the next item's completion IS the natural retry trigger. Zero waiting, zero tokens, nothing blocked." Rungs 2 and 3 (`poll`, `ask`) fire when nothing else is dispatchable. This plan wires a caller in; it does not build a mechanism.
- EVERY RE-ATTEMPT MUST GO THROUGH THE FULL GATE. The same docstring: "There is deliberately no shortcut that treats a clean `dirty_tree_overlap` as sufficient: that would prove only the absence of un-owned dirt, and say nothing about whether the suite still passes against today's main." A review-path shortcut would be the same error.
- THE STATUS AND THE KIND SHARE A SPELLING, AND THAT IS THE TRAP IN THIS AREA. `INTEGRATION_REFUSAL_TRANSIENT == 'integration-blocked'` (a refusal KIND) and `INTEGRATION_BLOCKED_STATUS == 'integration-blocked'` (a terminal STATUS) are the same string used for two different things. Reading one for the other is what produced my first wrong diagnosis; an executor should keep them apart deliberately.
- THE TERMINAL ARMS ARE DELIBERATE AND ENUMERATED. `decide_integration_deferral` (`:2400`) documents four reasons a refusal stays terminal, including the operator's `--on-integration-blocked=block` pin and an exhausted budget so "a permanently dirty path cannot spin the loop forever". The review path must inherit all four rather than acquiring a softer rule.
- ONE SHARED REVIEW LANE IS AN ACCEPTED DESIGN COST. The review call site's own comment records the OQ-02 decision: "a stranded review, never a lost edit." This plan does not revisit that; it makes the stranding recoverable and visible instead of permanent and silent.
- `git merge --abort` IS CORRECTLY NOT ISSUED for this arm. `runner_shared.py:2222-2226`: with no `MERGE_HEAD`, abort exits 128, and "Main is already exactly as it was found... because git checks this precondition BEFORE touching the working tree". Nothing here should add an abort.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `oc_runipd.py:7591-7625` | **THE REVIEW PATH NEVER ENTERS THE DEFERRAL LADDER.** On refusal it sets `review_integration_refusal`, saves state, prints, and continues. A scan of that call site finds no reference to `decide_integration_deferral`, `INTEGRATION_DEFERRED_STATUS`, or `reattempt_deferred_integrations`. The execute path enters the ladder at `:8395` (rung 1) and `:8463` (rungs 2 and 3). | the call site read at HEAD; the scan returning nothing |
| F2 | HIGH | `runner_shared.py:555` | **THE MESSAGE PROMISES SOMETHING THE REVIEW PATH DOES NOT DO.** `format_local_changes_refusal_reason` ends "it is re-attempted once the base is clean". True on the execute path, false on the review path. A message that states a false remedy is worse than one that states none, because the operator waits instead of acting. | the string; F1's absence of any re-attempt |
| F3 | HIGH | run `run-20260917T193010Z-1207513` | **MEASURED COST: a completed $13.27 / 32m46s review turn stranded, and the summary said `COMPLETED` with no blocked items.** The work sat on `aw/lane/review-sweep-run-20260917T193010Z-1207513` until a human noticed. An unmerged review is invisible to `aw att`, the same failure mode that hid plans `4fodkt` and `63425h` hours earlier. | the run summary table and the refusal line |
| F4 | MEDIUM | my own first diagnosis | **THE KIND IS ALREADY CLASSIFIED TRANSIENT; THE STATUS FILTER IS NOT THE BUG.** I first claimed `deferred_integration_items` filtering on `integration-deferred` was the defect. `classify_integration_refusal('integration-blocked')` returns True, so the kind is recognized. Recorded because the wrong fix (widening the status filter) would have changed the execute path's behavior for no reason while leaving the review path stranded. | `INTEGRATION_REFUSAL_TRANSIENT == 'integration-blocked'`; the classifier's return |
| F5 | MEDIUM | `pre-commit`, not this repository | **`fatal: stash failed` IS NOT OURS AND SHOULD BE ATTRIBUTED.** No runner module contains that string; it is `pre-commit`'s stash handling reacting to the same dirty tree. Leaving it unattributed in our output sends an operator into our code for a message we did not emit. | `grep 'stash failed'` across `agent_workflows/` and `hooks/` returning nothing |
| F6 | LOW | the retry's precondition | THE BLOCKING CONDITION IS A DIRTY MAIN, WHICH A CONCURRENT SESSION CAUSES ROUTINELY. This checkout is explicitly shared (`AGENTS.md`), and main gained commits from another session twice during this very investigation. So the transient arm is not a rare case; it is the expected case in normal use, which is what makes an unwired retry expensive rather than theoretical. | main moving from `3b2f1fdd` to `665ae62b` mid-investigation |
| F7 | LOW | approved plan `rl67b0` | ADJACENT AND COMPLEMENTARY, NOT OVERLAPPING. `rl67b0` adds an `integrate` verb and makes RESUME merge finished lanes, i.e. recovery AFTER a run ends. This plan is IN-RUN deferral. They compose: fewer strandings to recover, and a verb to recover the rest. E-06 should name that verb rather than inventing a recovery path. | `rl67b0`'s goal and E-01/E-03 |

## Proposed changes (ordered, validatable)

1. Prove the per-host asymmetry between the execute and review integration call sites (E-01) and confirm the refusal kind is already classified transient (E-02).
2. Route a refused review integration through the shared `decide_integration_deferral` and honor all four terminal arms (E-03).
3. Make a deferred review item selectable by `deferred_integration_items` and its lane reconstructible from durable state (E-04).
4. Mirror the wiring on the Antigravity host, preferring the shared function (E-05).
5. Report the deferral, the terminal recovery verb, and the `pre-commit` attribution (E-06).
6. Surface a stranded review in the run summary with its lane named (E-07).

## Deferred / out of scope (with reason)

- THE LADDER'S RUNG LOGIC, BUDGET, AND POLICY FLAG. Already built, already tested, already bounded. This plan adds a caller; changing the mechanism while wiring a new caller into it would make one change to two things at once.
- WHAT COUNTS AS A TRANSIENT REFUSAL. `classify_integration_refusal` is the single definition both hosts share and E-02 only VERIFIES it. Widening it is a policy change with its own risk (an unknown kind acquiring a retry loop nobody reasoned about, which its docstring names as the fail-closed concern).
- THE RUN'S OVERALL OUTCOME VERDICT. Whether an unintegrated review makes a run non-`COMPLETED` is a separate judgement and approved plan `ys1dor` already owns reporting a run whose work never landed. E-07 adds visibility without changing the verdict.
- POST-RUN RECOVERY. Approved plan `rl67b0` owns the `integrate` verb and resume-side merging. E-06 NAMES that verb rather than duplicating it.
- THE ONE-SHARED-REVIEW-LANE DESIGN. Settled by OQ-02 with the cost stated in the code ("a stranded review, never a lost edit"). Not reopened.
- FIXING `pre-commit`'s STASH BEHAVIOR. Not our code. E-06 attributes it; nothing here changes it.
- WIDENING THE PRE-MERGE DIRTY CHECK. Approved plan `fujm0y` owns that (it makes rename-detection-hidden paths classify correctly). Independent of this wiring and correct either way, since git remains the authority on its own preconditions.

## Scope check

- Over-scope: none. Every item is the review path's entry into an existing mechanism, plus the report that describes it.
- Under-scope: none for the reported defect. Post-run recovery, the outcome verdict, and the dirty-check width are each owned by a named approved plan and deferred above.

## Required tests / validation

1. `python3 -m pytest` bare, pasted summary line, compared against the pre-execution baseline (also pasted). The gate is no NEW failures.
2. A REVIEW turn whose integration is refused by the transient condition: shown deferring, then integrating on a later loop iteration once the blocking dirt is cleared. Pasted, on both hosts.
3. THE TERMINAL ARMS PRESERVED (mandatory, not optional): a `merge-conflict` refusal on the review path stays terminal; `--on-integration-blocked=block` makes the first refusal terminal; an exhausted budget stops re-attempting. Each pasted, because a wiring change that quietly softened one would be a worse defect than the one being fixed.
4. THE LADDER ACTUALLY SEES IT: a deferred review item shown returned by `deferred_integration_items` and its lane rebuilt by `handle_for`, not merely shown to have the right status.
5. The operator-facing output for both a deferred and a terminal review refusal, each naming the lane branch and the recovery verb.
6. `aw ipd lint --phase pre-transition` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

SPEC `20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` governs the run's deferral and
reporting behavior and is deliberately NOT declared in `- Scope-Paths:`, because this plan's reading is
that wiring an existing caller into an existing ladder implements the spec rather than amending it: the
transient arm and its budget are already specified, and the review path's omission is a gap in delivery.
THAT READING IS THE EXECUTOR'S TO TEST. If the spec says the deferral ladder applies to EXECUTE turns
specifically, or enumerates the statuses a review turn may reach, then this plan changes the contract:
declare that spec file in `Scope-Paths` first, per the spec-amendment rule, and record the reason here.

Note plan `63425h` (rcptwiden-01) already declares an edit to that same spec file. If both land, the
executor must not clobber the other's amendment; check the spec's current text rather than assuming this
plan's baseline.

## Open questions

### OQ-01: Should a review integration deferral share the execute path's budget, or have its own?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking; E-03 uses the SHARED budget by default, which needs no new flag and no new state. FOR SHARED: one `--integration-retry-limit` is one thing for an operator to reason about, the ladder's existing bound already prevents an infinite loop, and a review re-attempt costs a merge and a revalidation exactly like an execute one. FOR SEPARATE: a review turn produces two small record files while an execute turn produces product code, so an operator might want to retry a review far more patiently than an execute item, and one shared count means a busy execute queue can exhaust the budget a review would have used. Recorded because it is an operator-facing policy call, and because adding a second flag later is cheap while removing one is not.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted per-host comparison at execution HEAD, naming the EXECUTE call site that enters the ladder and the REVIEW call site that does not, WITH the scan output proving the review site references none of `decide_integration_deferral`, `INTEGRATION_DEFERRED_STATUS`, `reattempt_deferred_integrations`. A prose claim of asymmetry does NOT satisfy this item; the absence must be shown.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted values of `INTEGRATION_REFUSAL_TRANSIENT`, `INTEGRATION_REFUSAL_CONFLICT`, `INTEGRATION_BLOCKED_STATUS` and `INTEGRATION_DEFERRED_STATUS`, plus `classify_integration_refusal` evaluated for the transient and conflict kinds, plus the arm at `runner_shared.py:2230-2233` quoted showing which kind a git-refused-to-start merge returns. This item exists because the plan's author got this wrong first; re-derive it rather than quoting F4.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: THREE pasted cases from real runs or fixtures. (a) transient refusal -> `integration-deferred` with the shared reason. (b) `merge-conflict` refusal -> still terminal. (c) `--on-integration-blocked=block` -> first refusal terminal. PLUS the budget-exhausted arm shown terminal. All four are the shared function's enumerated terminal reasons and none may be carved out for reviews.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: a deferred REVIEW item shown returned by `deferred_integration_items` (paste the call and its result), its lane shown rebuilt by `handle_for` (paste the handle), and then a successful re-attempt after the blocking dirt is cleared, with main's HEAD before and after. Status-is-correct evidence alone does NOT satisfy this item: the failure mode is a deferred item the ladder cannot see.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: V-03's three cases pasted for the Antigravity host, PLUS an explicit statement of whether the wiring is shared between hosts or duplicated, and if duplicated, why the call sites could not share. If the two hosts' behavior differs in any pasted case, that difference is a finding, not a footnote.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted operator-facing output for BOTH a deferred and a terminal review refusal. The deferred one must say a re-attempt is pending and what clears it; the terminal one must name the preserved lane branch, the `aw <host> run integrate <id6>` verb, and the clean-base precondition. PLUS the `fatal: stash failed` attribution quoted from wherever it now appears, with the supporting evidence that no runner module emits that string.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the end-of-run summary pasted for a run whose review integration was refused, showing the stranded review and its lane named. PLUS an explicit statement, with the verdict line quoted, that the run's overall outcome classification was NOT changed by this item.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (7 E-items in 3 task groups, under the 18-leaf / 5-group thresholds).

EXECUTION CONTRACT. `OQ-01` is non-blocking and the maintainer's; execute with the SHARED budget and do
not invent a second flag. SCOPE FENCE: this plan declares both runner modules, `runner_shared.py`, and
`tests/test_review_lane_isolation.py`; an out-of-scope edit must be made only if genuinely required and
then JUSTIFIED to `aw ipd finalize` with a `--scope-reason` per path, and a declared path left unmodified
needs a `--scope-ack`. THE TWO THINGS THIS PLAN MUST NOT DO, both stated because each is a shortcut to a
passing test. FIRST, do not soften any of the four terminal arms for the review path: an operator who
passed `--on-integration-blocked=block` or exhausted the budget must still get a terminal refusal, and
V-03 tests all four for that reason. SECOND, do not add a review-specific shortcut that treats a clean
`dirty_tree_overlap` as sufficient to integrate; the ladder's own docstring records why every re-attempt
must go through the full merge-and-revalidate gate. BEWARE THE SHARED SPELLING: the refusal KIND and the
terminal STATUS are both the string `integration-blocked`, and confusing them is what produced this
plan's first wrong diagnosis. THE HARD-MUST HONESTY RULE: paste the ACTUAL command and test output for
every `V-*`, on BOTH hosts where the item says both; never claim a run not performed. Commit path-scoped
(`git commit -m msg -- <paths>`); never `git add -A`; never push. Before every commit run
`git diff --cached --name-only` and unstage anything not yours; this is a shared checkout and main moved
twice during this plan's own investigation. After the gate, move this plan to
`.aw/records/plans/executed/` via `aw ipd finalize`, and do not claim done until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries real observed evidence.
