# IPD: Give the review integration path the deferral ladder the execute path already has and stop promising a retry that never happens

- Date: 2026-09-17
- Kind: child
- Concern: A review turn whose integration is refused by a TRANSIENT condition is stranded permanently, while the identical refusal on an execute turn is retried automatically. The refusal message tells the operator "it is re-attempted once the base is clean" (`runner_shared.py:555`), and on the review path nothing ever re-attempts it: the review integration call site (`oc_runipd.py:7631`, the twin at `agy_runipd.py:4216`) records the refusal, prints it, and moves on. VERIFIED AT REVIEW by AST rather than by line range: the enclosing `execute_item` on BOTH hosts contains no reference to `decide_integration_deferral`, `INTEGRATION_DEFERRED_STATUS`, `reattempt_deferred_integrations`, or `deferred_integration_items`. (The authored range `:7591-7625` was stale; the call is at `:7631` and the refusal block at `:7654-7669`. Cite symbols, not line ranges.) Measured 2026-09-17 in run `run-20260917T193010Z-1207513`: the review of plan `63425h` completed and cost $13.27 / 32m46s, then reported `integration-blocked` with git's own "main has uncommitted local changes" text plus a `fatal: stash failed`, and the review sat unmerged on `aw/lane/review-sweep-run-20260917T193010Z-1207513` until a human noticed and merged it by hand. An unmerged review is invisible to `aw att`, which is the same stranding that hid plans `4fodkt` and `63425h` earlier the same day.
- Scope: Route the review path's integration refusal through the SAME shared deferral ladder the execute path uses, so a transient refusal defers and is re-attempted rather than being terminal on first contact; and make the operator-facing report name the actual condition, its remedy, and the verb that recovers it. Does NOT change the ladder's rung logic, its budget, its policy flag, the execute path, or what counts as a transient refusal.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, tests/test_review_lane_isolation.py
- Item-Dependencies: none
- Blocks-Release: next
- Status: approved
- Readiness: go-pending-approval
- Set: revladder
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: i4ak5n
- Approval: 2026-09-18, human ("approved"): Approved by maintainer: Option (a) chosen for sweep lane lifecycle; OQ-01 and OQ-02 resolved and PR-002 discharged

## Workflow history
- 2026-09-18 approved (aw set, --by-human): Approved by maintainer: Option (a) chosen for sweep lane lifecycle; OQ-01 and OQ-02 resolved and PR-002 discharged
- 2026-09-18 reviewed (antigravity pair with maintainer): /plan-review ROUND 2: APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL. OQ-02 RESOLVED: maintainer ruled for Option (a) (re-attempts never tear down the sweep lane; coordinator tears down at run end). OQ-01 RESOLVED (shared retry budget). PR-002 dispositioned FIXED. All blocking questions resolved; readiness promoted to go-pending-approval.
- 2026-09-18 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001..PR-007; readiness `no-go` on ONE blocking finding, plus a second BLOCKER fixed in place. Reviewed at HEAD `d3f418ff`; `aw ipd lint --phase author` conforming before revision; plan byte-identical to the lane input. THE DIAGNOSIS IS CORRECT AND I RE-PROVED IT BY AST RATHER THAN INHERITING IT: on BOTH hosts the enclosing `execute_item` containing the review integration call (`oc_runipd.py:7631`, `agy_runipd.py:4216`) references NONE of `decide_integration_deferral`, `INTEGRATION_DEFERRED_STATUS`, `reattempt_deferred_integrations`, `deferred_integration_items`. F2 verifies verbatim at `runner_shared.py:555` and is emitted from the SHARED merge path both actions reach (`:2295`), so review operators really do see the false promise; F5 verifies (`grep 'stash failed'` across `agent_workflows/` and `hooks/` returns nothing); F4's self-correction is exact. BUT THE PLAN'S CENTRAL PREMISE IS FALSE, and it is the premise that set its scope: "wires a caller in; it does not build a mechanism" and "does NOT change the ladder's rung logic" cannot both hold, because THE LADDER IS ACTION-BLIND IN THREE PLACES. (1) PR-001, BLOCKER, FIXED: the adapter binds `integrate=_integrate` -> this host's EXECUTE wrapper pinning `action_kind=INTEGRATION_ACTION_EXECUTE` (`oc_runipd.py:2440-2448`), and that constant is exactly what triggers `execute_merge_and_revalidate_gate` (`runner_shared.py:2204`), while the review path deliberately uses `integrate_review_lane_branch` which passes `INTEGRATION_ACTION_REVIEW` and takes NO `validation_runner` so a synthetic verdict is structurally impossible (`:2451-2470`); so E-03's status write alone makes the RETRY violate the `ajxr5d` OQ-01 rule the FIRST attempt honors. (2) same root: `finish_integrated=_finish` writes `item["status"] = "executed"` and calls `process_backlog_close`/`resolve_plan_path` (`:2524-2578`), none valid for a review. (3) PR-002, BLOCKER, OPEN: there is ONE sweep lane per run (`review_sweep_lane_id`, `runner_shared.py:1348-1354`) held at RUN level, and `lane_records_including_sweep` states "the lane belongs to no ITEM" (`:1529-1531`), while the ladder rebuilds a PER-ITEM handle from `preserved_*` and TEARS THE LANE DOWN on success (`oc_runipd.py:2543-2570`) - so two deferred reviews resolve to the same branch and the first success retires the lane the second needs, the exact hazard `teardown_review_sweep_lane` names for the per-item path (`lane_containment.py:3356-3357`). Measured that `deferred_integration_items` is action-blind and DOES select a review item. New E-04 (action-correct re-attempt) and E-05 (shared-lane rule) added, old E-05..E-07 renumbered E-06..E-08, `Highest E` 07 -> 08; V-04 now requires a validation runner that RAISES if called plus a post-success item dump, and V-05 requires TWO deferred reviews because one cannot expose the collision. ALSO: the plan named the wrong reuse target (`decide_integration_deferral` is PURE and no driver calls it; the shared write site is `record_integration_refusal`, `:2688`), told the operator to run `aw <host> run integrate <id6>` which IS NOT A COMMAND (the alias is `integrate` under the host group, `cli.py:3929`, and `rl67b0` is `executed` not approved so the verb is live), and every cited line number is stale by ~40 lines. SPEC QUESTION RESOLVED FROM EVIDENCE rather than left to the executor: `25kzda:163` scopes the ladder to the REFUSAL CONDITION and not to the action, and enumerates only what it must never apply to, so this is a delivery gap, no amendment is required, and no `.spec.md` is declared. OQ-02 raised `Blocking: yes` carrying PR-002.

- 2026-09-18 reviewed (aw set): plan-review complete: REVIEWED - OPEN QUESTIONS; 7 findings, 5 FIXED, PR-002 left OPEN at BLOCKER and escalated as blocking OQ-02. The diagnosis is correct and was re-proved by AST on both hosts, but the plan's central premise (pure wiring, no rung-side work) is FALSE: the ladder is action-blind in three places. PR-001 BLOCKER FIXED: the re-attempt binds the EXECUTE wrapper (action_kind=execute), which is exactly what triggers the revalidation gate a review skips by NOT RUNNING, and its success path writes status=executed and closes a backlog item; new E-04 owns action-correctness. PR-002 BLOCKER OPEN: one sweep lane is shared by every review while the ladder is per-item and tears the lane down on success, so the first re-attempt retires the lane a second deferred review still needs; new E-05 carries whichever design OQ-02 authorizes. Also fixed: wrong reuse target (record_integration_refusal, not the pure decide_integration_deferral), a printed recovery verb that does not exist, and stale line numbers throughout. Spec question RESOLVED from evidence: 25kzda:163 scopes the ladder to the refusal CONDITION not the action, so no amendment is required; readiness no-go

- 2026-09-17 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from a measured incident and filed at the maintainer's instruction after they observed the same failure "several times now". I CORRECTED MY OWN DIAGNOSIS TWICE WHILE INVESTIGATING, and both corrections matter because each wrong version would have produced a wrong plan. FIRST I claimed the ladder ignores the `integration-blocked` STATUS because `deferred_integration_items` (`:2464`) filters on `integration-deferred` only. That is true but not the defect: `INTEGRATION_REFUSAL_TRANSIENT` IS the string `'integration-blocked'`, and `classify_integration_refusal('integration-blocked')` returns True, so the refusal KIND is correctly recognized as transient. The status and the kind share a spelling, which is what misled me. SECOND I assumed the wiring was shared. It is not: `retry_deferred_integrations` is called from the EXECUTE dispatch loop only (`oc_runipd.py:8395` rung 1, `:8463` rungs 2 and 3), and the review path calls `integrate_review_lane_branch` (`:7591`) and then, on refusal, only records and prints (`:7614-7625`). Verified by scanning that call site for any deferral reference: none. So the ladder is sound and complete; the review path simply never enters it.

## Goal

Make a refused review integration recover by itself, the way a refused execute integration already
does, and make the message the operator reads true.

The ladder is not missing, and this plan must not rebuild it. `reattempt_deferred_integrations`
(`runner_shared.py:2779`) already implements three rungs, already re-attempts at the top of the dispatch
loop for free, already routes every re-attempt through the full merge-and-revalidate gate, and already
bounds itself with a budget and an operator policy flag. The review path is simply not wired to it.

BUT "SIMPLY NOT WIRED" UNDERSTATES THE JOB, AND THE THREE MEASUREMENTS BELOW ARE WHY. Review found that
the ladder is ACTION-BLIND in three places, so setting a review item to `integration-deferred` (which is
literally what E-03 prescribes) hands it to machinery built for execute items. Each of these is a
CORRECTNESS problem, not a style one, and each must be closed by this plan rather than discovered by an
executor.

FIRST, THE RE-ATTEMPT WOULD RUN THE REVALIDATION GATE A REVIEW MUST NEVER RUN. The per-host adapter binds
`integrate=_integrate`, and `_integrate` calls `integrate_lane_branch(...)` through this host's wrapper,
which pins `action_kind=INTEGRATION_ACTION_EXECUTE` (`oc_runipd.py:2440-2448`). The review path
deliberately uses a DIFFERENT wrapper, `integrate_review_lane_branch`, which passes
`INTEGRATION_ACTION_REVIEW` and takes NO `validation_runner` at all, precisely so "a caller CANNOT supply a
synthetic validation result through this path even by mistake" (its docstring, `oc_runipd.py:2451-2470`).
Since `action_kind == INTEGRATION_ACTION_EXECUTE` is what triggers
`execute_merge_and_revalidate_gate` (`runner_shared.py:2204`), a deferred review re-attempted through the
existing adapter would revalidate a turn whose whole output is two record files. The `ajxr5d` OQ-01 ruling
that the skip must happen "by NOT RUNNING rather than by any fabricated verdict" would be violated by the
retry path while remaining true on the first attempt.

SECOND, THE SUCCESS PATH WOULD CORRUPT THE REVIEW ITEM. `finish_integrated=_finish` sets
`item["status"] = "executed"`, calls `process_backlog_close(...)`, and resolves a plan path
(`oc_runipd.py:2524-2578`). Measured by inspecting the adapter body: `_finish` references
`item["status"] = "executed"`, `process_backlog_close`, `teardown_lane_if_classified` and
`resolve_plan_path`. For a REVIEW item every one of those is wrong by construction: a review does not
execute the plan it reviewed, has no backlog carrier to close, and must not claim `executed`.

THIRD, AND MOST STRUCTURALLY: THE REVIEW LANE IS SHARED BY EVERY REVIEW IN THE RUN, WHILE THE LADDER
ASSUMES ONE LANE PER ITEM. There is exactly one sweep lane per run
(`review_sweep_lane_id(run_id)`, `runner_shared.py:1348-1354`), recorded at RUN level under
`REVIEW_SWEEP_LANE_KEY`, and `lane_records_including_sweep` states in terms that settle the question that
"the lane belongs to no ITEM" (`:1529-1531`). The ladder, by contrast, rebuilds a per-item handle from
`item["preserved_branch"]`/`preserved_lane_id`/`preserved_base` and tears the lane down on success. So two
deferred reviews would resolve to the SAME branch, the first successful re-attempt would retire the lane
the second still needs, and `teardown_review_sweep_lane`'s own docstring already names this hazard for the
per-item path: "putting it on the per-item path would destroy the lane the NEXT review needs"
(`lane_containment.py:3356-3357`). E-04 as authored asks only whether the lane is RECONSTRUCTIBLE; that is
the easy half and it is not the dangerous one.

WHAT SURVIVES ALL THREE: the diagnosis (F1, F2), the decision to reuse `decide_integration_deferral`
rather than invent a policy, and the refusal to touch `classify_integration_refusal`. What does NOT
survive is the premise that this is a pure wiring change with no rung-side work. See OQ-02, blocking.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the asymmetry from the code before changing either path

- [ ] E-01 PROVE THE ASYMMETRY AT EXECUTION HEAD, and refuse to proceed on this plan's line numbers. Show that an `integration-blocked` refusal from an EXECUTE turn reaches `decide_integration_deferral` and can become `integration-deferred`, and that the SAME refusal from a REVIEW turn does not: scan the review integration call site for any reference to `decide_integration_deferral`, `INTEGRATION_DEFERRED_STATUS`, or `reattempt_deferred_integrations` and show there is none. NOTE: With `execute_item` unified into `runner_shared.execute_item_core` (commit `70a2059f`), the review integration call site lives in `runner_shared.py` for both hosts rather than duplicated across `oc_runipd.py` and `agy_runipd.py`.
  - Depends on: none
  - Expected outcome: a pasted per-host comparison naming the execute call site that enters the ladder and the review call site that does not, with the scan that proves the absence.
  - Execution state: pending

- [ ] E-02 CONFIRM THE KIND IS ALREADY CLASSIFIED TRANSIENT, so the fix does not touch `classify_integration_refusal` and cannot widen what defers. Show `classify_integration_refusal(INTEGRATION_REFUSAL_TRANSIENT)` is True, that `INTEGRATION_REFUSAL_TRANSIENT` equals the string the git-refused-to-start arm returns (`runner_shared.py:2230-2233`), and that `merge-conflict` remains False. This is the measurement that keeps the fix to WIRING rather than to POLICY, and it is the one I got wrong first, so verify it rather than inheriting it.
  - Depends on: none
  - Expected outcome: pasted values showing the transient kind, the conflict kind, and the classifier's verdict for each, plus the arm that returns the transient kind quoted.
  - Execution state: pending

### Task group 2: wire the review path into the existing ladder, changing no rung logic

- [ ] E-03 ROUTE A REFUSED REVIEW INTEGRATION THROUGH THE SHARED LADDER WRITE SITE, which is `runner_shared.record_integration_refusal` (`:2688`), NOT `decide_integration_deferral` directly. CORRECTED AT REVIEW: `decide_integration_deferral` is PURE and is called from exactly two places, both inside `record_integration_refusal`; no driver calls it (verified: `grep decide_integration_deferral agent_workflows/` returns only `runner_shared.py`). `record_integration_refusal` is what counts the attempt durably, asks for the verdict, writes the status, and emits the rung-naming event, and it is already shared by both hosts. Because `execute_item` is unified in `runner_shared.execute_item_core`, the review integration call site lives in `runner_shared.py`, so wiring it there inherently wires it for both hosts. Reuse it; do NOT add a second decision site, a review-specific policy, or a review-specific budget. The four terminal reasons it enforces through the pure decision (non-transient kind, `--on-integration-blocked=block`, budget exhausted, budget zero) must apply to the review path with no exception carved out.
  - Depends on: E-01, E-02
  - Expected outcome: a refused review integration whose kind is transient records `integration-deferred` with the shared reason string and an `integration_ladder` record; a `merge-conflict` refusal and a `block` policy each stay terminal, all three pasted.
  - Execution state: pending

- [ ] E-04 MAKE THE RE-ATTEMPT ACTION-CORRECT, which review measurement shows is the load-bearing item and is NOT what the authored E-04 asked for. The ladder is ACTION-BLIND in two ways that would corrupt a review, both proven at review and both restated here so an executor cannot miss them. (a) `integrate=_integrate` calls this host's execute wrapper, which pins `action_kind=INTEGRATION_ACTION_EXECUTE` (`oc_runipd.py:2440-2448`), and that constant is exactly what triggers `execute_merge_and_revalidate_gate` (`runner_shared.py:2204`); a re-attempted review would therefore REVALIDATE, defeating the `ajxr5d` OQ-01 rule that the skip happen "by NOT RUNNING". The re-attempt must dispatch to `integrate_review_lane_branch` for a review item. (b) `finish_integrated=_finish` sets `item["status"] = "executed"` and calls `process_backlog_close` / `resolve_plan_path` (`oc_runipd.py:2524-2578`), none of which is valid for a review. A review's success path must record review integration the way the FIRST-attempt review path does, and must not claim `executed` or close a backlog item. Prefer selecting the per-action behavior from the item itself over adding a parallel ladder; state which you chose and why.
  - Depends on: E-03
  - Expected outcome: a deferred REVIEW item shown re-attempted through the REVIEW wrapper (evidence that `action_kind` was `review` and that no validation runner was consulted), and shown finishing WITHOUT `status = executed`, WITHOUT a backlog close, and WITHOUT a plan-path resolution; plus the execute path's re-attempt shown byte-for-byte unchanged in behavior.
  - Execution state: pending

- [ ] E-05 RESOLVE THE SHARED-LANE COLLISION BEFORE ANY RE-ATTEMPT CAN BE SAFE, per OQ-02's answer. There is ONE sweep lane per run (`review_sweep_lane_id`, `runner_shared.py:1348-1354`), recorded at RUN level, and `lane_records_including_sweep` states "the lane belongs to no ITEM" (`:1529-1531`), while the ladder rebuilds a PER-ITEM handle from `preserved_*` and TEARS THE LANE DOWN on success. So with two deferred reviews both resolve to the same branch and the first success retires the lane the second still needs, which is the hazard `teardown_review_sweep_lane` already names for the per-item path (`lane_containment.py:3356-3357`). Implement whatever OQ-02 authorizes, and whichever it is, the re-attempt MUST NOT tear down the sweep lane per item; retirement stays coordinator-owned and once-per-run.
  - Depends on: E-04
  - Expected outcome: TWO reviews deferred in one run, both re-attempted, both integrated, with the sweep lane shown surviving until coordinator retirement and neither review's work lost; plus the case where the first re-attempt succeeds and the second is still pending, shown not to have lost its lane.
  - Execution state: pending

- [ ] E-06 VERIFY SYMMETRIC WIRING ON THE ANTIGRAVITY HOST. Because `execute_item` was unified into `runner_shared.execute_item_core` (commit `70a2059f`), the review integration call site is already single-implementation in `runner_shared.py`. E-06 therefore validates that the shared wiring covers the Antigravity host symmetrically (running agy tests), confirming that `aw agy run` exercises the identical ladder behavior without requiring any divergent host-specific branch.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: the same cases from E-03, E-04 and E-05 pasted for the Antigravity host, confirming that the shared wiring in `runner_shared.execute_item_core` covers both hosts identically.
  - Execution state: pending

### Task group 3: make the report tell the operator what to do

- [ ] E-07 REPORT THE DEFERRAL AND THE REMEDY, not just the refusal. The current message states the condition and then promises a re-attempt; once E-03 lands, that promise is true and the report should say which rung is pending and what clears it. Where a refusal is TERMINAL, the report must name the concrete recovery: the preserved lane branch, the verb that integrates it (`aw oc integrate <id6>` / `aw agy integrate <id6>`, spelled out as `aw <host> runipd integrate <id6>`, from EXECUTED plan `rl67b0`), and the fact that a clean base is the precondition. THE VERB STRING WAS WRONG AS AUTHORED (`aw <host> run integrate <id6>` is not a command; the alias is registered as `integrate` directly under the host group, `cli.py:3929`), and printing a verb that does not exist is the specific failure `attention.lane_remedy_hint` already guards against ('Do not print a verb that does not exist'). VERIFY THE SPELLING AGAINST THE PARSER at execution HEAD before printing it. ALSO NAME WHAT IS NOT OURS: the incident's `fatal: stash failed` line comes from `pre-commit`'s own stash handling, not from any runner code (verified: no runner module contains that string), so an operator hunting our code for it is wasting time. Say whose message it is.
  - Depends on: E-03
  - Expected outcome: pasted operator-facing output for a deferred review integration and for a terminal one, each naming the lane branch, the recovery verb, and the precondition; plus the `fatal: stash failed` attribution stated once where it will be read.
  - Execution state: pending

- [ ] E-08 SURFACE A STRANDED REVIEW IN THE RUN SUMMARY, because the measured cost of this defect was invisibility rather than the refusal itself. The run that stranded `63425h` reported `Outcome: COMPLETED` with `1 reviewed` and no blocked items, so nothing in the summary said a review's work was sitting on a lane. Make a review whose integration did not land visible in the end-of-run report with its lane named. Do NOT change the run's overall outcome verdict in this item: whether an unintegrated review makes a run non-COMPLETED is a separate judgement, and approved plan `ys1dor` already owns reporting a run whose work never landed.
  - Depends on: E-07
  - Expected outcome: a run whose review integration was refused shown reporting that fact in its summary with the lane named, pasted; and an explicit statement that the overall outcome verdict was not changed here.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE LADDER IS ALREADY BUILT AND ALREADY CHEAP. `reattempt_deferred_integrations` (`runner_shared.py:2779`; the authored `:2714` was stale) is called from the TOP of the dispatch loop, and its docstring records why rung 1 costs nothing: "that loop already reloads state and already runs `cascade_dependency_blocked` each iteration, so the next item's completion IS the natural retry trigger. Zero waiting, zero tokens, nothing blocked." Rungs 2 and 3 (`poll`, `ask`) fire when nothing else is dispatchable. This plan wires a caller in; it does not build a mechanism.
- EVERY RE-ATTEMPT MUST GO THROUGH THE FULL GATE. The same docstring: "There is deliberately no shortcut that treats a clean `dirty_tree_overlap` as sufficient: that would prove only the absence of un-owned dirt, and say nothing about whether the suite still passes against today's main." A review-path shortcut would be the same error.
- THE STATUS AND THE KIND SHARE A SPELLING, AND THAT IS THE TRAP IN THIS AREA. `INTEGRATION_REFUSAL_TRANSIENT == 'integration-blocked'` (a refusal KIND) and `INTEGRATION_BLOCKED_STATUS == 'integration-blocked'` (a terminal STATUS) are the same string used for two different things. Reading one for the other is what produced my first wrong diagnosis; an executor should keep them apart deliberately.
- THE TERMINAL ARMS ARE DELIBERATE AND ENUMERATED. `decide_integration_deferral` (`:2459`; the authored `:2400` was stale) documents four reasons a refusal stays terminal, including the operator's `--on-integration-blocked=block` pin and an exhausted budget so "a permanently dirty path cannot spin the loop forever". The review path must inherit all four rather than acquiring a softer rule.
- ONE SHARED REVIEW LANE IS AN ACCEPTED DESIGN COST. The review call site's own comment records the
  `ajxr5d` OQ-02 decision: "a stranded review, never a lost edit." This plan does not revisit that; it makes
  the stranding recoverable and visible instead of permanent and silent. BUT THAT SHARING IS NOT INERT HERE,
  which the authored plan did not notice: one lane per RUN (`review_sweep_lane_id`,
  `runner_shared.py:1348-1354`) held at run level, and `lane_records_including_sweep` states "the lane
  belongs to no ITEM" (`:1529-1531`), while the ladder is per-item and tears the lane down on success. That
  collision is E-05 and OQ-02 (F10).
- THE LADDER'S ADAPTER IS ACTION-SPECIFIC, AND THAT IS THE PART THIS PLAN MUST CHANGE. `retry_deferred_integrations`
  binds `integrate` to this host's EXECUTE wrapper (`action_kind=INTEGRATION_ACTION_EXECUTE`) and
  `finish_integrated` to a success path that writes `status = executed` and closes a backlog item. The
  review path deliberately uses a different wrapper that takes no validation runner at all. So "reuse the
  shared ladder" is right about the RUNGS and wrong about the ADAPTER (F8, F9).
- `record_integration_refusal` IS THE SHARED WRITE SITE, not `decide_integration_deferral`. The latter is
  pure and is only called from inside the former; both hosts call the former (`oc_runipd.py:7796`,
  `agy_runipd.py:4349`). Wire to the write site so the durable attempt count and the rung-naming event come
  for free (F11).
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
| F7 | LOW | ~~approved~~ **EXECUTED** plan `rl67b0` | ADJACENT AND COMPLEMENTARY, NOT OVERLAPPING. `rl67b0` adds an `integrate` verb and makes RESUME merge finished lanes, i.e. recovery AFTER a run ends. This plan is IN-RUN deferral. They compose: fewer strandings to recover, and a verb to recover the rest. E-07 should name that verb rather than inventing a recovery path. CORRECTED AT REVIEW: `rl67b0` is `Status: executed`, not approved, so the verb EXISTS today and E-07 must print the real spelling. It is registered as `integrate` directly under the host group (`cli.py:3929`), i.e. `aw oc integrate <id6>`, spelled out `aw oc runipd integrate <id6>`; the authored `aw <host> run integrate <id6>` is not a command. | `rl67b0`'s front matter; `cli.py:3929`, `:11544` |
| F8 | HIGH | `oc_runipd.py:2440-2448` vs `:2451-2470`; `runner_shared.py:2204` | **THE LADDER'S RE-ATTEMPT WOULD REVALIDATE A REVIEW.** The adapter binds `integrate=_integrate`, which calls this host's execute wrapper pinning `action_kind=INTEGRATION_ACTION_EXECUTE`, and that constant is exactly what triggers `execute_merge_and_revalidate_gate`. The review path deliberately uses `integrate_review_lane_branch`, which passes `INTEGRATION_ACTION_REVIEW` and takes NO `validation_runner` so a synthetic verdict is structurally impossible. So E-03's status write alone would make the RETRY violate the `ajxr5d` OQ-01 rule that the skip happen "by NOT RUNNING". | the two wrappers' bodies; the `if action_kind == INTEGRATION_ACTION_EXECUTE` branch |
| F9 | HIGH | `oc_runipd.py:2524-2578` | **THE LADDER'S SUCCESS PATH WOULD CORRUPT A REVIEW ITEM.** `_finish` sets `item["status"] = "executed"`, calls `process_backlog_close`, resolves a plan path, and deletes the `preserved_*` keys. Measured by inspecting the adapter body, which references all four. For a review none is valid: it executes no plan and carries no backlog item. | the `_finish` body |
| F10 | HIGH | `runner_shared.py:1348-1354`, `:1529-1531`; `lane_containment.py:3356-3357` | **ONE SWEEP LANE IS SHARED BY EVERY REVIEW, WHILE THE LADDER IS PER-ITEM AND TEARS THE LANE DOWN.** `lane_records_including_sweep` states "the lane belongs to no ITEM". Two deferred reviews resolve to the same branch and the first success retires the lane the second needs, the exact hazard `teardown_review_sweep_lane` names for the per-item path. This is why E-04's authored "is the lane reconstructible?" was the easy half. | the sweep-lane id helper; the run-level record; the teardown docstring |
| F11 | MEDIUM | `runner_shared.py:2688` vs `:2459` | **THE PLAN NAMES THE WRONG FUNCTION TO REUSE.** `decide_integration_deferral` is PURE and is called from only two places, both inside `record_integration_refusal`; no driver calls it. The shared WRITE site both hosts already use is `record_integration_refusal`, which counts the attempt durably, gets the verdict, writes the status, and emits the rung-naming event. Wiring to the pure function would reimplement the counting and the event. | `grep decide_integration_deferral agent_workflows/` returning `runner_shared.py` only; `oc_runipd.py:7796` and `agy_runipd.py:4349` calling the write site |
| F12 | LOW | `runner_shared.py:12380` (previously `oc_runipd.py:7631`; `agy_runipd.py:4216`) | `execute_item` was unified into `runner_shared.execute_item_core` (commit `70a2059f`), so the review integration call site lives in `runner_shared.py` for both hosts rather than duplicated in the individual runner modules. F1's substance was re-verified by AST. | the AST scan of the enclosing `execute_item_core` |

## Proposed changes (ordered, validatable)

1. Prove the per-host asymmetry between the execute and review integration call sites (E-01) and confirm the refusal kind is already classified transient (E-02).
2. Route a refused review integration through the shared WRITE site `record_integration_refusal`, honoring all four terminal arms (E-03).
3. Make the re-attempt ACTION-CORRECT: dispatch a review to `integrate_review_lane_branch` so it is not revalidated, and give it a success path that does not claim `executed` or close a backlog item (E-04).
4. Resolve the shared-sweep-lane collision per OQ-02, and never tear the sweep lane down per item (E-05).
5. Mirror all three on the Antigravity host, preferring the shared function (E-06).
6. Report the deferral, the terminal recovery verb (verified against the parser), and the `pre-commit` attribution (E-07).
7. Surface a stranded review in the run summary with its lane named (E-08).

REVIEW NOTE ON ORDERING: items 3 and 4 did not exist in the authored plan and are not polish. Without
item 3 the retry revalidates a review and marks it `executed`; without item 4 a second deferred review
loses its lane to the first one's success. Item 2 alone therefore MUST NOT ship on its own.

## Deferred / out of scope (with reason)

- THE LADDER'S RUNG LOGIC, BUDGET, AND POLICY FLAG. Already built, already tested, already bounded. This
  plan adds a caller; changing the mechanism while wiring a new caller into it would make one change to two
  things at once. NARROWED AT REVIEW, because as written this bullet is now partly false and would have
  been read as authority to skip E-04: the RUNG LOGIC (the three rungs, their triggers, the budget, the
  policy flag, `classify_integration_refusal`) is untouched, but the per-host ADAPTER that binds
  `integrate` and `finish_integrated` MUST change, because both are execute-specific (F8, F9). Editing the
  adapter is not editing the ladder; conflating the two is what made this plan look like pure wiring.
- POST-RUN RECOVERY OF A REVIEW THAT NEVER LANDED. `rl67b0` (now `executed`) owns `aw <host> integrate
  <id6>`, whose contract is a lane that "already finished, verified and finalized"; whether it accepts a
  REVIEW lane is not established here and is not this plan's to change. E-07 NAMES the verb; if it turns
  out not to accept a review lane, that is a finding to report, not a fix to smuggle in.
- WHAT COUNTS AS A TRANSIENT REFUSAL. `classify_integration_refusal` is the single definition both hosts share and E-02 only VERIFIES it. Widening it is a policy change with its own risk (an unknown kind acquiring a retry loop nobody reasoned about, which its docstring names as the fail-closed concern).
- THE RUN'S OVERALL OUTCOME VERDICT. Whether an unintegrated review makes a run non-`COMPLETED` is a separate judgement and approved plan `ys1dor` already owns reporting a run whose work never landed. E-07 adds visibility without changing the verdict.
- POST-RUN RECOVERY. Approved plan `rl67b0` owns the `integrate` verb and resume-side merging. E-06 NAMES that verb rather than duplicating it.
- THE ONE-SHARED-REVIEW-LANE DESIGN. Settled by OQ-02 with the cost stated in the code ("a stranded review, never a lost edit"). Not reopened.
- FIXING `pre-commit`'s STASH BEHAVIOR. Not our code. E-06 attributes it; nothing here changes it.
- WIDENING THE PRE-MERGE DIRTY CHECK. Approved plan `fujm0y` owns that (it makes rename-detection-hidden paths classify correctly). Independent of this wiring and correct either way, since git remains the authority on its own preconditions.

## Scope check

- Over-scope: none. Every item is the review path's entry into an existing mechanism, plus the report that describes it.
- UNDER-SCOPE AS AUTHORED, and this is the review's main structural finding rather than a quibble. The plan
  described itself as pure wiring ("this plan wires a caller in; it does not build a mechanism") and its
  Scope says it does not change "the ladder's rung logic". Measured, that is not achievable: the ladder is
  ACTION-BLIND, so entering it as a review requires per-action behavior in the re-attempt (F8, F9) and a
  rule for the SHARED sweep lane (F10). Two new E-items (E-04, E-05) now carry that work, and the
  self-description above is corrected in the Goal. An executor who took the authored scope literally would
  have shipped item 2 alone and produced a retry that revalidates reviews, marks them `executed`, and
  destroys a second review's lane.
- Under-scope, still: post-run recovery, the outcome verdict, and the dirty-check width are each owned by a
  named plan and deferred below.

## Required tests / validation

1. `python3 -m pytest` bare, pasted summary line, compared against the pre-execution baseline (also pasted). The gate is no NEW failures. RUN IT BARE: `pyproject.toml` `addopts` already supplies the quiet/parallel/fast-subset flags, and a second `-q` suppresses the summary line this item requires. A managed worker lane also fails a set of lifecycle tests BY DESIGN (backlog `770fkp`, measured at 31 in this session), so take the baseline in the SAME tree and gate on no NEW failures rather than an absolute count.
2. A REVIEW turn whose integration is refused by the transient condition: shown deferring, then integrating on a later loop iteration once the blocking dirt is cleared. Pasted, on both hosts.
3. THE TERMINAL ARMS PRESERVED (mandatory, not optional): a `merge-conflict` refusal on the review path stays terminal; `--on-integration-blocked=block` makes the first refusal terminal; an exhausted budget stops re-attempting. Each pasted, because a wiring change that quietly softened one would be a worse defect than the one being fixed.
4. THE LADDER ACTUALLY SEES IT: a deferred review item shown returned by `deferred_integration_items` and its lane rebuilt by `handle_for`, not merely shown to have the right status. (Review already measured that the FILTER is action-blind and does select a review item, so this is the cheap half; items 4a and 4b below are the ones that can fail.)
4a. THE RE-ATTEMPT IS ACTION-CORRECT: the review's re-attempt shown running with `action_kind == "review"` and NEVER consulting a validation runner (prove it with a runner that raises if called, not with a passing verdict), and its success shown NOT setting `status = executed`, NOT closing a backlog item, and NOT resolving a plan path. Without this, entering the ladder makes the retry violate the `ajxr5d` OQ-01 rule the first attempt honors.
4b. TWO DEFERRED REVIEWS IN ONE RUN both recover, with the shared sweep lane shown surviving the first success. One deferred review cannot expose the collision, so a single-review test does not satisfy this.
5. The operator-facing output for both a deferred and a terminal review refusal, each naming the lane branch and the recovery verb, with the verb PROVEN to parse (`aw oc integrate --help` or the parser registration quoted). The authored spelling does not exist.
6. THE EXECUTE PATH UNCHANGED: its first-attempt refusal, its deferral, and its re-attempt success each shown behaving exactly as before, since E-04 edits the shared adapter both actions reach.
7. `aw ipd lint --phase pre-transition` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

SPEC `20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` (`25kzda`, `Status: approved`) governs
the run's deferral behavior and is deliberately NOT declared in `- Scope-Paths:`: wiring an existing caller
into an existing ladder IMPLEMENTS the spec rather than amending it.

THE EXECUTOR NO LONGER HAS TO TEST THAT READING; REVIEW TESTED IT AND IT HOLDS. The spec's ladder
requirement is at `:163` and it is scoped to the REFUSAL CONDITION, not to the action that produced it:
"`--on-integration-blocked` selects the disposition ladder applied when an integration is REFUSED because
the main tree holds un-owned dirty paths overlapping the incoming change ... The ladder applies ONLY to
that transient dirty-overlap refusal." It enumerates what the ladder must NEVER apply to (a genuine merge
conflict, a stale base, a non-passing combined revalidation, a scope violation) and says nothing that
restricts it to execute turns, and it does not enumerate the statuses a review turn may reach. So a review
turn refused by exactly that condition is inside the requirement, and today's behavior is a delivery gap.
No amendment is declared and no `.spec.md` appears in `Scope-Paths`.

ONE SPEC CONSTRAINT DOES BIND E-04, and it is the reason F8 is a HIGH rather than a note: the same sentence
forbids any rung from reclassifying a failure as a deferral and from integrating over a contaminated base.
A re-attempt that ran the EXECUTE path's revalidation gate for a review would be doing something the spec
never contemplated for a turn with nothing to validate, and the `ajxr5d` OQ-01 ruling (skip "by NOT
RUNNING", never by a fabricated verdict) is the controlling authority. E-04 must satisfy both.

Note plan `63425h` (rcptwiden-01) declared an edit to that same spec file and is now `Status: executed`, so
its amendment is already in the tree; read the spec's CURRENT text rather than this plan's baseline.

## Open questions

### OQ-01: Should a review integration deferral share the execute path's budget, or have its own?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-18: Use the shared budget
  (`--integration-retry-limit`). This keeps a single, uniform retry bound across the run without adding flags or
  state.

### OQ-02: One sweep lane is shared by every review in the run, but the ladder is per-item and tears the lane down on success. How should a deferred review's lane be handled?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Finding: PR-002 (dispositioned FIXED)
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-18: Option (a) is chosen. A review
  re-attempt NEVER tears down the sweep lane during re-attempt execution; retirement is left entirely to the
  existing coordinator-owned `teardown_review_sweep_lane` at the end of the run. This preserves the `ajxr5d` OQ-02
  decision (one sweep lane per run, avoiding session-sharing hazard `lanesess xd9sll`), eliminates the hazard
  where the first successful review re-attempt tears down the lane needed by subsequent reviews, and satisfies
  E-05 and V-05. PR-002 is dispositioned FIXED.

  ROUND 1 CONTEXT (KEPT FOR HISTORY): NOT DECIDED BY THE REVIEWER, because every option trades off against
  the `ajxr5d` OQ-02 ruling that this repository already made ("one lane for the whole sweep", accepted
  cost "a stranded review, never a lost edit"), and reopening that is the maintainer's.
  MEASURED AT REVIEW: there is exactly ONE sweep lane per run (`review_sweep_lane_id(run_id)`,
  `runner_shared.py:1348-1354`), held at RUN level under `REVIEW_SWEEP_LANE_KEY`, and
  `lane_records_including_sweep` states "the lane belongs to no ITEM" (`:1529-1531`). The ladder, in
  contrast, rebuilds a PER-ITEM handle from `item["preserved_branch"]` / `preserved_lane_id` /
  `preserved_base` and, on success, calls `teardown_lane_if_classified` and then DELETES those
  `preserved_*` keys (`oc_runipd.py:2543-2570`). So with two deferred reviews: both resolve to the same
  branch, and the first successful re-attempt retires the lane the second still needs. That is precisely
  the hazard `teardown_review_sweep_lane` names for the per-item path ("putting it on the per-item path
  would destroy the lane the NEXT review needs", `lane_containment.py:3356-3357`).
  OPTIONS: (a) make the re-attempt NEVER tear down a sweep lane, leaving retirement to the existing
  coordinator-owned `teardown_review_sweep_lane`, which is the smallest change and preserves the current
  design, but means a deferred review's lane lives to end of run; (b) defer only ONE review at a time,
  refusing to defer a second while one is pending, which keeps the per-item model honest but silently
  strands the second review exactly as today; (c) give each review its own lane, which removes the
  collision entirely but reverses `ajxr5d` OQ-02 and re-opens the session-sharing hazard incident
  `lanesess xd9sll` recorded; or (d) merge each deferred review's work by branch rather than by lane
  handle, decoupling the retry from lane lifetime.
  The reviewer's read is that (a) is the smallest correct answer and (d) the most robust, and that (c)
  should not be chosen inside this plan; but the choice belongs to the maintainer because (a) changes
  when a lane is reclaimed and (c) reverses a recorded decision.

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
  - Required evidence: THE ACTION-CORRECTNESS PROOF, which is this plan's highest-value item because the ladder is action-blind by default. (a) A deferred REVIEW item re-attempted, with evidence the merge ran with `action_kind == "review"` and that NO validation runner was consulted (assert the runner is never called, e.g. a runner that raises if invoked, rather than asserting a passing verdict). (b) The same re-attempt shown finishing WITHOUT `item["status"] == "executed"`, WITHOUT a backlog close, and WITHOUT a plan-path resolution: paste the item dict after success. (c) The EXECUTE path's re-attempt shown unchanged, so the per-action split did not alter it. A test that only shows the review integrated does NOT satisfy this item: an implementation that reused `_integrate`/`_finish` verbatim would pass that and would revalidate the review and mark it executed.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: TWO reviews deferred in ONE run, since one is the case that cannot expose the collision. Paste: both items in `deferred_integration_items`; the handle each resolves to, shown to be the SAME sweep branch; the first re-attempt succeeding; and then the SECOND re-attempt also succeeding with its lane still present. PLUS explicit evidence that the successful re-attempt did NOT retire the sweep lane (the lane directory and branch still there, and the coordinator retirement shown to be the only teardown). If OQ-02 authorized a different design, paste the evidence that design demands instead, but the two-review case is mandatory either way.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: V-03's three cases, V-04's three, and V-05's two-review case, each pasted for the Antigravity host, confirming that the shared wiring in `runner_shared.execute_item_core` behaves symmetrically across both hosts without host-divergent branches.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: pasted operator-facing output for BOTH a deferred and a terminal review refusal. The deferred one must say a re-attempt is pending and what clears it; the terminal one must name the preserved lane branch, the recovery verb, and the clean-base precondition. THE VERB MUST BE PASTED AS THE PARSER ACCEPTS IT, together with the evidence that it does (e.g. `aw oc integrate --help` succeeding, or the parser registration quoted): the authored spelling `aw <host> run integrate <id6>` does not exist, and a printed verb that fails for an operator mid-incident is worse than no verb. PLUS the `fatal: stash failed` attribution quoted from wherever it now appears, with the supporting evidence that no runner module emits that string.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: the end-of-run summary pasted for a run whose review integration was refused, showing the stranded review and its lane named. PLUS an explicit statement, with the verdict line quoted, that the run's overall outcome classification was NOT changed by this item.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (8 E-items in 3 task groups, under the 18-leaf / 5-group thresholds).
  REVIEW NOTE ON DENSITY, since a passing count lint does not clear right-sizing: E-04 and E-05 each name
  ONE concern (action-correctness of the re-attempt; the shared-lane rule) but each touches the shared
  adapter AND its per-host twin, so if an executor finds either cannot be done in one focused pass, split
  it per host rather than widening the item.

EXECUTION CONTRACT. `OQ-02` IS BLOCKING and must be answered before E-05 (and therefore before any
re-attempt can safely land); `OQ-01` is non-blocking and the maintainer's, so execute with the SHARED
budget and do not invent a second flag. SCOPE FENCE: this plan declares both runner modules,
`runner_shared.py`, and `tests/test_review_lane_isolation.py`; an out-of-scope edit must be made only if
genuinely required and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason` per path, and a declared
path left unmodified needs a `--scope-ack`.

THE FOUR THINGS THIS PLAN MUST NOT DO, each a shortcut to a passing test. FIRST, do not soften any of the
four terminal arms for the review path: an operator who passed `--on-integration-blocked=block` or exhausted
the budget must still get a terminal refusal, and V-03 tests all four for that reason. SECOND, do not add a
review-specific shortcut that treats a clean `dirty_tree_overlap` as sufficient to integrate; the ladder's
own docstring records why every re-attempt must go through the full merge-and-revalidate gate. THIRD, DO NOT
SHIP E-03 WITHOUT E-04: setting a review item to `integration-deferred` while the re-attempt still runs the
EXECUTE wrapper makes the retry revalidate a review and mark it `executed`, which is strictly worse than
today's honest refusal, because the plan's own F2 complaint (a promise that is not kept) becomes a promise
that is kept WRONGLY. FOURTH, DO NOT SHIP E-03/E-04 WITHOUT E-05: the sweep lane is shared, so the first
successful re-attempt would retire the lane a second deferred review still needs, converting a recoverable
stranding into a lost one. Both are why V-04 and V-05 exist and why neither may be satisfied by a
single-review test.

BEWARE THE SHARED SPELLING: the refusal KIND and the
terminal STATUS are both the string `integration-blocked`, and confusing them is what produced this
plan's first wrong diagnosis. THE HARD-MUST HONESTY RULE: paste the ACTUAL command and test output for
every `V-*`, on BOTH hosts where the item says both; never claim a run not performed. Commit path-scoped
(`git commit -m msg -- <paths>`); never `git add -A`; never push. Before every commit run
`git diff --cached --name-only` and unstage anything not yours; this is a shared checkout and main moved
twice during this plan's own investigation. After the gate, move this plan to
`.aw/records/plans/executed/` via `aw ipd finalize`, and do not claim done until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries real observed evidence.
