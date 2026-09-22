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
the ladder is ACTION-BLIND in three places, so setting a review item to `merge-retry` (which is
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

- [x] E-01 PROVE THE ASYMMETRY AT EXECUTION HEAD, and refuse to proceed on this plan's line numbers. Show that an `integration-blocked` refusal from an EXECUTE turn reaches `decide_integration_deferral` and can become `integration-deferred`, and that the SAME refusal from a REVIEW turn does not: scan the review integration call site for any reference to `decide_integration_deferral`, `INTEGRATION_DEFERRED_STATUS`, or `reattempt_deferred_integrations` and show there is none. NOTE: With `execute_item` unified into `runner_shared.execute_item_core` (commit `70a2059f`), the review integration call site lives in `runner_shared.py` for both hosts rather than duplicated across `oc_runipd.py` and `agy_runipd.py`.
  - Depends on: none
  - Expected outcome: a pasted per-host comparison naming the execute call site that enters the ladder and the review call site that does not, with the scan that proves the absence.
  - Execution state: performed

- [x] E-02 CONFIRM THE KIND IS ALREADY CLASSIFIED TRANSIENT, so the fix does not touch `classify_integration_refusal` and cannot widen what defers. Show `classify_integration_refusal(INTEGRATION_REFUSAL_TRANSIENT)` is True, that `INTEGRATION_REFUSAL_TRANSIENT` equals the string the git-refused-to-start arm returns (`runner_shared.py:2230-2233`), and that `INTEGRATION_REFUSAL_CONFLICT` (`merge-refused`) remains False. NOTE the vocabulary was RENAMED 2026-09-21 (`l2mzxn`): the transient kind is now `merge-retry` and the terminal refusal is `merge-refused`; cite the CONSTANTS rather than the strings, and note a third kind `merge-unchecked` is now ALSO deferrable. This is the measurement that keeps the fix to WIRING rather than to POLICY, and it is the one I got wrong first, so verify it rather than inheriting it.
  - Depends on: none
  - Expected outcome: pasted values showing the transient kind, the conflict kind, and the classifier's verdict for each, plus the arm that returns the transient kind quoted.
  - Execution state: performed

### Task group 2: wire the review path into the existing ladder, changing no rung logic

- [x] E-03 ROUTE A REFUSED REVIEW INTEGRATION THROUGH THE SHARED LADDER WRITE SITE, which is `runner_shared.record_integration_refusal` (`:2688`), NOT `decide_integration_deferral` directly. CORRECTED AT REVIEW: `decide_integration_deferral` is PURE and is called from exactly two places, both inside `record_integration_refusal`; no driver calls it (verified: `grep decide_integration_deferral agent_workflows/` returns only `runner_shared.py`). `record_integration_refusal` is what counts the attempt durably, asks for the verdict, writes the status, and emits the rung-naming event, and it is already shared by both hosts. Because `execute_item` is unified in `runner_shared.execute_item_core`, the review integration call site lives in `runner_shared.py`, so wiring it there inherently wires it for both hosts. Reuse it; do NOT add a second decision site, a review-specific policy, or a review-specific budget. The four terminal reasons it enforces through the pure decision (non-transient kind, `--on-integration-blocked=block`, budget exhausted, budget zero) must apply to the review path with no exception carved out.
  - Depends on: E-01, E-02
  - Expected outcome: a refused review integration whose kind is transient records `merge-retry` with the shared reason string and an `integration_ladder` record; a `merge-refused` refusal and a `block` policy each stay terminal, all three pasted.
  - Execution state: performed

- [x] E-04 MAKE THE RE-ATTEMPT ACTION-CORRECT, which review measurement shows is the load-bearing item and is NOT what the authored E-04 asked for. The ladder is ACTION-BLIND in two ways that would corrupt a review, both proven at review and both restated here so an executor cannot miss them. (a) `integrate=_integrate` calls this host's execute wrapper, which pins `action_kind=INTEGRATION_ACTION_EXECUTE` (`oc_runipd.py:2440-2448`), and that constant is exactly what triggers `execute_merge_and_revalidate_gate` (`runner_shared.py:2204`); a re-attempted review would therefore REVALIDATE, defeating the `ajxr5d` OQ-01 rule that the skip happen "by NOT RUNNING". The re-attempt must dispatch to `integrate_review_lane_branch` for a review item. (b) `finish_integrated=_finish` sets `item["status"] = "executed"` and calls `process_backlog_close` / `resolve_plan_path` (`oc_runipd.py:2524-2578`), none of which is valid for a review. A review's success path must record review integration the way the FIRST-attempt review path does, and must not claim `executed` or close a backlog item. Prefer selecting the per-action behavior from the item itself over adding a parallel ladder; state which you chose and why.
  - Depends on: E-03
  - Expected outcome: a deferred REVIEW item shown re-attempted through the REVIEW wrapper (evidence that `action_kind` was `review` and that no validation runner was consulted), and shown finishing WITHOUT `status = executed`, WITHOUT a backlog close, and WITHOUT a plan-path resolution; plus the execute path's re-attempt shown byte-for-byte unchanged in behavior.
  - Execution state: performed

- [x] E-05 RESOLVE THE SHARED-LANE COLLISION BEFORE ANY RE-ATTEMPT CAN BE SAFE, per OQ-02's answer. There is ONE sweep lane per run (`review_sweep_lane_id`, `runner_shared.py:1348-1354`), recorded at RUN level, and `lane_records_including_sweep` states "the lane belongs to no ITEM" (`:1529-1531`), while the ladder rebuilds a PER-ITEM handle from `preserved_*` and TEARS THE LANE DOWN on success. So with two deferred reviews both resolve to the same branch and the first success retires the lane the second still needs, which is the hazard `teardown_review_sweep_lane` already names for the per-item path (`lane_containment.py:3356-3357`). Implement whatever OQ-02 authorizes, and whichever it is, the re-attempt MUST NOT tear down the sweep lane per item; retirement stays coordinator-owned and once-per-run.
  - Depends on: E-04
  - Expected outcome: TWO reviews deferred in one run, both re-attempted, both integrated, with the sweep lane shown surviving until coordinator retirement and neither review's work lost; plus the case where the first re-attempt succeeds and the second is still pending, shown not to have lost its lane.
  - Execution state: performed

- [x] E-06 VERIFY SYMMETRIC WIRING ON THE ANTIGRAVITY HOST. Because `execute_item` was unified into `runner_shared.execute_item_core` (commit `70a2059f`), the review integration call site is already single-implementation in `runner_shared.py`. E-06 therefore validates that the shared wiring covers the Antigravity host symmetrically (running agy tests), confirming that `aw agy run` exercises the identical ladder behavior without requiring any divergent host-specific branch.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: the same cases from E-03, E-04 and E-05 pasted for the Antigravity host, confirming that the shared wiring in `runner_shared.execute_item_core` covers both hosts identically.
  - Execution state: performed

### Task group 3: make the report tell the operator what to do

- [x] E-07 REPORT THE DEFERRAL AND THE REMEDY, not just the refusal. The current message states the condition and then promises a re-attempt; once E-03 lands, that promise is true and the report should say which rung is pending and what clears it. Where a refusal is TERMINAL, the report must name the concrete recovery: the preserved lane branch, the verb that integrates it (`aw oc integrate <id6>` / `aw agy integrate <id6>`, spelled out as `aw <host> runipd integrate <id6>`, from EXECUTED plan `rl67b0`), and the fact that a clean base is the precondition. THE VERB STRING WAS WRONG AS AUTHORED (`aw <host> run integrate <id6>` is not a command; the alias is registered as `integrate` directly under the host group, `cli.py:3929`), and printing a verb that does not exist is the specific failure `attention.lane_remedy_hint` already guards against ('Do not print a verb that does not exist'). VERIFY THE SPELLING AGAINST THE PARSER at execution HEAD before printing it. ALSO NAME WHAT IS NOT OURS: the incident's `fatal: stash failed` line comes from `pre-commit`'s own stash handling, not from any runner code (verified: no runner module contains that string), so an operator hunting our code for it is wasting time. Say whose message it is.
  - Depends on: E-03
  - Expected outcome: pasted operator-facing output for a deferred review integration and for a terminal one, each naming the lane branch, the recovery verb, and the precondition; plus the `fatal: stash failed` attribution stated once where it will be read.
  - Execution state: performed

- [x] E-08 SURFACE A STRANDED REVIEW IN THE RUN SUMMARY, because the measured cost of this defect was invisibility rather than the refusal itself. The run that stranded `63425h` reported `Outcome: COMPLETED` with `1 reviewed` and no blocked items, so nothing in the summary said a review's work was sitting on a lane. Make a review whose integration did not land visible in the end-of-run report with its lane named. Do NOT change the run's overall outcome verdict in this item: whether an unintegrated review makes a run non-COMPLETED is a separate judgement, and approved plan `ys1dor` already owns reporting a run whose work never landed.
  - Depends on: E-07
  - Expected outcome: a run whose review integration was refused shown reporting that fact in its summary with the lane named, pasted; and an explicit statement that the overall outcome verdict was not changed here.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE LADDER IS ALREADY BUILT AND ALREADY CHEAP. `reattempt_deferred_integrations` (`runner_shared.py:2779`; the authored `:2714` was stale) is called from the TOP of the dispatch loop, and its docstring records why rung 1 costs nothing: "that loop already reloads state and already runs `cascade_dependency_blocked` each iteration, so the next item's completion IS the natural retry trigger. Zero waiting, zero tokens, nothing blocked." Rungs 2 and 3 (`poll`, `ask`) fire when nothing else is dispatchable. This plan wires a caller in; it does not build a mechanism.
- EVERY RE-ATTEMPT MUST GO THROUGH THE FULL GATE. The same docstring: "There is deliberately no shortcut that treats a clean `dirty_tree_overlap` as sufficient: that would prove only the absence of un-owned dirt, and say nothing about whether the suite still passes against today's main." A review-path shortcut would be the same error.
- THE STATUS AND THE KIND ONCE SHARED A SPELLING, AND THAT WAS THE TRAP IN THIS AREA. Before the 2026-09-21 rename (`l2mzxn`) `INTEGRATION_REFUSAL_TRANSIENT` and `INTEGRATION_BLOCKED_STATUS` were BOTH the string `'integration-blocked'` - one a refusal KIND, one a terminal STATUS - and reading one for the other produced my first wrong diagnosis. THE RENAME SPLIT THEM: the transient kind is now `merge-retry` (equal to `INTEGRATION_DEFERRED_STATUS`, deliberately) and the terminal status is `merge-needs-human`. The trap is therefore GONE for the pair that caused it, but the lesson stands: cite the CONSTANTS, never the strings, because `INTEGRATION_REFUSAL_TRANSIENT` and `INTEGRATION_DEFERRED_STATUS` still share a value.
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

- [x] V-01 validates E-01
  - Required evidence: the pasted per-host comparison at execution HEAD, naming the EXECUTE call site that enters the ladder and the REVIEW call site that does not, WITH the scan output proving the review site references none of `decide_integration_deferral`, `INTEGRATION_DEFERRED_STATUS`, `reattempt_deferred_integrations`. A prose claim of asymmetry does NOT satisfy this item; the absence must be shown.
  - Observed evidence: measured at HEAD `2815aa56` BEFORE any edit. Both hosts delegate to the shared
    core, so the asymmetry is inside ONE function: `oc_runipd.execute_item delegates to
    execute_item_core: True` / `agy_runipd.execute_item delegates to execute_item_core: True`. Within
    `execute_item_core` the review integration call is at core-relative line 1515 and the execute one at
    1607/1611. THE SCAN, per refusal block:

    ```text
    REVIEW refusal block references to ladder names:
      decide_integration_deferral: False
      INTEGRATION_DEFERRED_STATUS: False
      reattempt_deferred_integrations: False
      record_integration_refusal: False
      deferred_integration_items: False

    EXECUTE refusal block references to ladder names:
      decide_integration_deferral: False
      INTEGRATION_DEFERRED_STATUS: False
      reattempt_deferred_integrations: False
      record_integration_refusal: True          <-- the execute path ENTERS the ladder here
      deferred_integration_items: False
    ```

    And the review block VERBATIM at that HEAD, which records the refusal, prints, and moves on:

    ```python
    if not review_integrated:
        item["review_integration_refusal"] = review_reason
        save_state(run_dir, state)
        print(
            pal(
                f"  ! review {item['id6']} was NOT integrated to main ({review_kind}): "
                f"{review_reason}. Its work is preserved on {wt_handle.branch}.",
                "yellow",
            ),
            file=sys.stderr,
        )
    ```

    The ladder's own ENTRY points exist on both hosts and are reached only from the EXECUTE dispatch
    loop: `oc_runipd.run_queue: ['retry_deferred_integrations(run_dir, state)',
    'retry_deferred_integrations(run_dir, state, poll=True, ask=True)']` and the identical pair in
    `agy_runipd.run_queue`. Full capture:
    `.aw/state/lane-submissions/run-20260922T023526Z-2065001/16-i4ak5n/attempt-1/evidence/E-01-asymmetry.txt`.
    NOTE the plan's authored line numbers (`oc_runipd.py:7631`, `agy_runipd.py:4216`) are stale: the
    unification into `execute_item_core` moved the site, which is why this was re-derived by AST.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted values of `INTEGRATION_REFUSAL_TRANSIENT`, `INTEGRATION_REFUSAL_CONFLICT`, `INTEGRATION_BLOCKED_STATUS` and `INTEGRATION_DEFERRED_STATUS`, plus `classify_integration_refusal` evaluated for the transient and conflict kinds, plus the arm at `runner_shared.py:2230-2233` quoted showing which kind a git-refused-to-start merge returns. This item exists because the plan's author got this wrong first; re-derive it rather than quoting F4.
  - Observed evidence: re-derived at execution HEAD rather than inherited from F4.

    ```text
    CONSTANTS (note the rename, `l2mzxn` 2026-09-21):
      INTEGRATION_REFUSAL_TRANSIENT = 'merge-retry'
      INTEGRATION_REFUSAL_CONFLICT = 'merge-refused'
      INTEGRATION_REFUSAL_UNMEASURED = 'merge-unchecked'
      INTEGRATION_DEFERRED_STATUS = 'merge-retry'
      INTEGRATION_BLOCKED_STATUS = 'merge-needs-human'

    classify_integration_refusal (True == deferrable):
      classify_integration_refusal(INTEGRATION_REFUSAL_TRANSIENT='merge-retry') -> True
      classify_integration_refusal(INTEGRATION_REFUSAL_UNMEASURED='merge-unchecked') -> True
      classify_integration_refusal(INTEGRATION_REFUSAL_CONFLICT='merge-refused') -> False
      classify_integration_refusal('a-kind-nobody-declared') -> False  (fail-closed)

    THE TRAP, still live: TRANSIENT kind and DEFERRED status share a value:
      INTEGRATION_REFUSAL_TRANSIENT == INTEGRATION_DEFERRED_STATUS -> True
      INTEGRATION_REFUSAL_TRANSIENT == INTEGRATION_BLOCKED_STATUS  -> False
    ```

    THE ARM a git-REFUSED-TO-START merge returns, quoted from `integrate_lane_branch` (the plan's cited
    `:2230-2233` is stale; located by symbol instead):

    ```python
    # Git REFUSED TO START the merge, so there is nothing to abort and NO abort is issued: with no
    # `MERGE_HEAD`, `git merge --abort` exits 128 ...
    return (
        False,
        format_local_changes_refusal_reason(merge_stdout=out2, merge_stderr=err2),
        INTEGRATION_REFUSAL_TRANSIENT,
    )
    ```

    And the CONFLICT arm, for contrast: `if merge_in_progress(repo):` ... returns
    `INTEGRATION_REFUSAL_CONFLICT`. THREE CORRECTIONS TO THE PLAN'S PREMISE, all from this measurement:
    the deferrable set is now THREE kinds and not one (`merge-unchecked` was added by `l2mzxn` after this
    plan was authored, so the review path inherits it too and V-03 tests it); the pre-rename trap the
    author fell into is GONE for the pair that caused it (`INTEGRATION_BLOCKED_STATUS` is now
    `merge-needs-human`), but SURVIVES for `INTEGRATION_REFUSAL_TRANSIENT`/`INTEGRATION_DEFERRED_STATUS`,
    which still share `merge-retry`; and `classify_integration_refusal` is UNTOUCHED by this plan, so
    nothing here widens what defers. Full capture: `evidence/E-02-kinds.txt`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: THREE pasted cases from real runs or fixtures. (a) transient refusal -> `integration-deferred` with the shared reason. (b) `merge-conflict` refusal -> still terminal. (c) `--on-integration-blocked=block` -> first refusal terminal. PLUS the budget-exhausted arm shown terminal. All four are the shared function's enumerated terminal reasons and none may be carved out for reviews.
  - Observed evidence: every arm driven through the SHARED write site with a REVIEW item
    (`action: "review"`). Note the post-rename spellings: the deferred status is `merge-retry` and the
    terminal ones are `merge-refused`/`merge-needs-human`.

    ```text
    (a) TRANSIENT kind, defer policy     kind=merge-retry      -> deferred=True  status='merge-retry'
        verdict: integration DEFERRED (attempt 1 of 11): main holds un-owned dirty paths overlapping
        this change, which is transient by nature, so the lane is preserved and integration is
        re-attempted through the full revalidate gate once other work advances
        UNMEASURED kind (l2mzxn's 3rd) kind=merge-unchecked  -> deferred=True  status='merge-retry'
    (b) CONFLICT kind -> TERMINAL        kind=merge-refused    -> deferred=False status='merge-refused'
        verdict: integration refusal kind 'merge-refused' is terminal on its first attempt ...
    (c) --on-integration-blocked=block   kind=merge-retry      -> deferred=False status='merge-needs-human'
        verdict: --on-integration-blocked=block: the operator pinned the pre-ladder behavior, so the
        first refusal is terminal and the lane is preserved
    (d) budget EXHAUSTED                 kind=merge-retry      -> deferred=False status='merge-needs-human'
        verdict: integration re-attempt budget exhausted (10 re-attempt(s) after the first, limit 10) ...
        budget ZERO                      kind=merge-retry      -> deferred=False status='merge-needs-human'
    ```

    THE WIRING ITSELF is asserted structurally rather than by grep, so a comment naming the function
    cannot satisfy it: `test_the_review_call_site_REACHES_the_shared_write_site_on_both_hosts` parses
    `execute_item_core`, isolates the `if not review_integrated:` block by AST, and requires
    `record_integration_refusal` among the calls INSIDE that block (the pre-existing execute call further
    down the same function cannot satisfy it). AND THE WIRING IS NOT INERT, which is the defect this
    execution found and closed: `test_a_REAL_TURN_leaves_the_item_SELECTABLE_by_the_ladder_END_TO_END`
    drives a whole turn on both hosts and then asks the ladder's own FILTER -
    `selected by the ladder filter : ['rev001']` and `item status after the refusal : 'merge-retry'`. See
    DECISION 16-i4ak5n-D2: with the write site wired but the local `disposition` unchanged, the turn's
    later unconditional `item["status"] = disposition` overwrote `merge-retry` back to `reviewed` and the
    filter returned `[]`, so every unit assertion passed while the review stayed stranded. Runner output:

    ```text
    28 passed in 2.25s   (the five new classes, `-o addopts=""`)
    ```

    Full captures: `evidence/V-03-V-07-V-08.txt`, `evidence/V-02-defer-then-integrate.txt`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: THE ACTION-CORRECTNESS PROOF, which is this plan's highest-value item because the ladder is action-blind by default. (a) A deferred REVIEW item re-attempted, with evidence the merge ran with `action_kind == "review"` and that NO validation runner was consulted (assert the runner is never called, e.g. a runner that raises if invoked, rather than asserting a passing verdict). (b) The same re-attempt shown finishing WITHOUT `item["status"] == "executed"`, WITHOUT a backlog close, and WITHOUT a plan-path resolution: paste the item dict after success. (c) The EXECUTE path's re-attempt shown unchanged, so the per-action split did not alter it. A test that only shows the review integrated does NOT satisfy this item: an implementation that reused `_integrate`/`_finish` verbatim would pass that and would revalidate the review and mark it executed.
  - Observed evidence: THE CHOICE MADE, as the item asks: the per-action behavior is selected FROM THE
    ITEM by the shared `runner_shared.integration_action_for_item(item)` rather than by a parallel ladder,
    so the rungs, the budget, the policy flag and `classify_integration_refusal` are untouched and only
    WHICH adapter a re-attempt dispatches to changes. The rationale is that a parallel ladder would be a
    second decision site for the same question, which is the drift `record_integration_refusal` was
    collapsed to prevent.

    (a) THE MERGE RAN AS A REVIEW AND NO VALIDATION RUNNER WAS CONSULTED, proved with a runner that
    RAISES if invoked (`_explode`), not with a passing verdict:
    `test_a_deferred_REVIEW_is_re_attempted_through_the_REVIEW_wrapper_and_NEVER_validates` patches
    `make_integration_validation_runner` to return `_explode`, spies the shared
    `integrate_lane_branch`, and asserts `action_kind == INTEGRATION_ACTION_REVIEW` and that the
    positional `validation_runner` argument was `None`. The ladder record confirms the routing:

    ```text
    ladder records : [{'id6': 'rev001', 'outcome': 'integrated',
                       'detail': 'fast-forward integrated to main', 'action': 'review'}]
    ```

    (b) THE SUCCESS PATH CLAIMS NO `executed`, CLOSES NO BACKLOG ITEM, RESOLVES NO PLAN PATH.
    `test_the_review_success_path_claims_NO_executed_and_closes_NO_backlog_item` patches BOTH
    `process_backlog_close` and `resolve_plan_path` to raise, so reaching either fails the test, and then
    asserts the post-success item. From the end-to-end run:

    ```text
    item status after re-attempt   : 'reviewed'        (NOT 'executed')
    review_integrated              : True
    the review's revision is ON MAIN: True
    its record is ON MAIN          : True
    ```

    The item additionally has no `backlog_close` and no `last_plan_path` key, and its
    `review_integration_refusal` is CLEARED (a landed review must not still read as stranded to the
    summary). The status is RESTORED from the turn's own lane-derived verdict rather than invented; see
    DECISION 16-i4ak5n-D3 for why hardcoding `reviewed` would silently downgrade an `approved`-setting
    review.

    (c) THE EXECUTE PATH IS UNCHANGED: `test_the_EXECUTE_path_re_attempt_is_UNCHANGED_by_the_split`
    drives an execute item's deferred re-attempt on both hosts and asserts
    `action_kind == INTEGRATION_ACTION_EXECUTE`, that the validation runner WAS called (`assertTrue(
    validated)`, i.e. the gate still revalidates), and that the item still reaches `status == "executed"`.

    AND THE FAIL-CLOSED DIRECTION IS PINNED TOO (DECISION 16-i4ak5n-D4):
    `test_a_deferred_REVIEW_is_left_DEFERRED_when_no_review_adapter_was_supplied` supplies only the
    execute pair, with an `integrate` that RAISES if reached, and asserts the outcome is
    `no-review-adapter` and the item stays `merge-retry` - so a caller that cannot integrate a review
    correctly leaves it deferred rather than corrupting it. Runner output: `28 passed in 2.25s`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: TWO reviews deferred in ONE run, since one is the case that cannot expose the collision. Paste: both items in `deferred_integration_items`; the handle each resolves to, shown to be the SAME sweep branch; the first re-attempt succeeding; and then the SECOND re-attempt also succeeding with its lane still present. PLUS explicit evidence that the successful re-attempt did NOT retire the sweep lane (the lane directory and branch still there, and the coordinator retirement shown to be the only teardown). If OQ-02 authorized a different design, paste the evidence that design demands instead, but the two-review case is mandatory either way.
  - Observed evidence: OQ-02 OPTION (a) IS WHAT WAS IMPLEMENTED (maintainer, 2026-09-18): a re-attempt
    NEVER tears the sweep lane down, and retirement is left entirely to the coordinator-owned
    `retire_review_sweep_lane` at run end. TWO deferred reviews in ONE run, driven end-to-end through the
    real `execute_item` on BOTH hosts, with both merges refused by the measured transient condition:

    ```text
    BOTH deferred, per the ladder's own filter : ['rev001', 'rev002']
    rev001 resolves to                        : aw/lane/review-sweep-run-test
    rev002 resolves to                        : aw/lane/review-sweep-run-test
    THE SAME BRANCH (this IS the collision)   : True

    --- rung 1 re-attempts BOTH deferred reviews ---
      ✓ review rev001 integrated to main on a deferred re-attempt (fast-forward integrated to main);
        the shared sweep lane aw/lane/review-sweep-run-test is RETAINED for any other review
        (retirement is the coordinator's, once per run)
      ✓ review rev002 integrated to main on a deferred re-attempt (fast-forward integrated to main);
        the shared sweep lane aw/lane/review-sweep-run-test is RETAINED for any other review
        (retirement is the coordinator's, once per run)

    rev001 status : 'reviewed'          rev002 status : 'reviewed'

    --- THE FIRST SUCCESS MUST NOT HAVE RETIRED THE LANE THE SECOND NEEDED ---
    sweep worktree still on disk              : True
    sweep BRANCH still present                : True
    run-level record marked retired by an ITEM: False

    rev001: revision on main=True  record on main=True
    rev002: revision on main=True  record on main=True

    --- AND RETIREMENT IS STILL THE COORDINATOR'S, once, at run end ---
    coordinator retirement: retired=True  reason='sweep complete'
    ```

    Identical output for `agy_runipd (aw agy run)` in the same capture. THE INTERLEAVED CASE the item also
    demands (first success while the second is still pending) is
    `test_the_SECOND_review_still_has_its_lane_while_the_first_has_landed`: after the first lands, the
    second's `deferred_review_lane_handle` still resolves to the same live branch.

    THE NO-TEARDOWN PROPERTY IS PINNED BY EXPLODING EVERY ROUTE rather than by reading the source, because
    the hazard is a CALL and a source pin is satisfied by a comment:
    `test_RETIREMENT_IS_THE_COORDINATORS_and_the_ITEM_path_never_tears_down` patches
    `teardown_lane_if_classified`, `teardown_review_sweep_lane` AND `teardown_isolation_worktree` to raise,
    then runs `finish_integrated_review_item`. The mechanism: the per-item `preserved_*` handle rebuild is
    BYPASSED for a review by the shared `deferred_review_lane_handle`, which reads the RUN-LEVEL
    `REVIEW_SWEEP_LANE_KEY` record - so both reviews get the same branch by construction rather than by
    coincidence, and a retired or absent lane resolves to `None` (pinned by
    `test_a_RETIRED_sweep_lane_resolves_to_None_rather_than_a_fabricated_handle`) which the ladder already
    handles by failing toward terminal with the branch untouched.
    Full capture: `evidence/V-05-two-reviews-one-lane.txt`.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: V-03's three cases, V-04's three, and V-05's two-review case, each pasted for the Antigravity host, confirming that the shared wiring in `runner_shared.execute_item_core` behaves symmetrically across both hosts without host-divergent branches.
  - Observed evidence: SYMMETRY IS STRUCTURAL FOR THE REFUSAL SITE and BEHAVIORAL for the adapters, and
    the distinction matters because only the second could have drifted. The refusal site is
    single-implementation in `runner_shared.execute_item_core` (V-01's evidence shows both hosts delegate
    to it), so E-03's wiring reaches `aw agy run` by construction. The ADAPTERS are genuinely per-host
    code, so every V-03/V-04/V-05 test is parameterized over `_DRIVERS = (("oc_runipd", oc_runipd),
    ("agy_runipd", agy_runipd))` with `subTest(driver=...)`, which means a failure on ONE host is a
    failure of the suite.

    THE ANTIGRAVITY HOST, driven end-to-end (V-02's case, the full defer-then-integrate cycle):

    ```text
    ================================================================================================
    HOST: agy_runipd (aw agy run)
    ================================================================================================
      ! review rev001 was NOT integrated to main (merge-retry): integration refused: main tree has
        un-owned dirty paths overlapping the incoming change: .aw/records/plans/pending/...ipd.md
        -> its work is preserved on aw/lane/review-sweep-run-test; main is untouched
        -> DEFERRED, so no action is needed from you: this is attempt 1 of 11 ...
    item status after the refusal  : 'merge-retry'
    selected by the ladder filter  : ['rev001']
    resolves to the sweep branch   : aw/lane/review-sweep-run-test
    --- the blocking dirt is cleared; the DISPATCH LOOP's rung 1 re-attempts ---
      ✓ review rev001 integrated to main on a deferred re-attempt (fast-forward integrated to main);
        the shared sweep lane ... is RETAINED ...
    ladder records                 : [{'id6': 'rev001', 'outcome': 'integrated',
                                       'detail': 'fast-forward integrated to main', 'action': 'review'}]
    item status after re-attempt   : 'reviewed'
    ```

    V-05's TWO-REVIEW CASE on the Antigravity host, from the same parameterized capture:

    ```text
    HOST: agy_runipd (aw agy run)
    BOTH deferred, per the ladder's own filter : ['rev001', 'rev002']
    THE SAME BRANCH (this IS the collision)   : True
    rev001 status : 'reviewed'   rev002 status : 'reviewed'
    sweep worktree still on disk              : True
    sweep BRANCH still present                : True
    run-level record marked retired by an ITEM: False
    coordinator retirement: retired=True  reason='sweep complete'
    ```

    V-04's three cases on the Antigravity host are the `agy_runipd` subTests of
    `test_a_deferred_REVIEW_is_re_attempted_through_the_REVIEW_wrapper_and_NEVER_validates`,
    `test_the_review_success_path_claims_NO_executed_and_closes_NO_backlog_item` and
    `test_the_EXECUTE_path_re_attempt_is_UNCHANGED_by_the_split`, all PASSED in the run below. NO
    HOST-DIVERGENT BRANCH WAS ADDED: `test_the_review_lane_helpers_have_exactly_one_definition` now also
    covers `integration_action_for_item`, `item_is_deferred_review`, `deferred_review_lane_handle`,
    `finish_integrated_review_item` and `format_review_integration_refusal_report`, asserting NEITHER
    driver redefines any of them. Each host's `retry_deferred_integrations` gains only the two thin
    bindings (its own review wrapper, and a delegation to the shared finish performer).

    ```text
    28 passed in 2.25s
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: pasted operator-facing output for BOTH a deferred and a terminal review refusal. The deferred one must say a re-attempt is pending and what clears it; the terminal one must name the preserved lane branch, the recovery verb, and the clean-base precondition. THE VERB MUST BE PASTED AS THE PARSER ACCEPTS IT, together with the evidence that it does (e.g. `aw oc integrate --help` succeeding, or the parser registration quoted): the authored spelling `aw <host> run integrate <id6>` does not exist, and a printed verb that fails for an operator mid-incident is worse than no verb. PLUS the `fatal: stash failed` attribution quoted from wherever it now appears, with the supporting evidence that no runner module emits that string.
  - Observed evidence: BOTH SHAPES, as an operator sees them on stderr.

    DEFERRED (the shape whose promise used to be FALSE on this path):

    ```text
      ! review 63425h was NOT integrated to main (merge-retry): integration refused by git: main has
        uncommitted local changes to file(s) this merge would overwrite, so the merge never started
        (no conflict, nothing to resolve)
        -> its work is preserved on aw/lane/review-sweep-run-20260917T193010Z-1207513; main is untouched
        -> DEFERRED, so no action is needed from you: this is attempt 1 of 11 and the run re-attempts
           the integration itself through the full merge-and-revalidate gate as soon as other work
           advances. integration DEFERRED (attempt 1 of 11): main holds un-owned dirty paths overlapping
           this change, which is transient by nature, so the lane is preserved and integration is
           re-attempted through the full revalidate gate once other work advances
        -> note: a `fatal: stash failed` line accompanying this refusal is `pre-commit`'s own stash
           handling reacting to the same dirty tree, NOT this runner's output; no runner module emits it
    ```

    TERMINAL:

    ```text
      ! review 63425h was NOT integrated to main (merge-retry): integration refused by git: ...
        -> its work is preserved on aw/lane/review-sweep-run-20260917T193010Z-1207513; main is untouched
        -> TERMINAL, so a HUMAN owns it now: integration re-attempt budget exhausted (10 re-attempt(s)
           after the first, limit 10); the overlapping dirty path never cleared, so the lane is
           preserved and a human owns it
        -> recover it with `aw <host> integrate 63425h` (spelled out: `aw <host> runipd integrate
           63425h`), which costs no agent turn; it needs a CLEAN base, so commit or stash the un-owned
           changes in main first
        -> note: a `fatal: stash failed` line ... NOT this runner's output; no runner module emits it
    ```

    The DEFERRED shape deliberately does NOT print a recovery verb: telling a human to merge by hand while
    the run's own next re-attempt is pending would invite a race. THE VERB IS PROVEN AGAINST THE PARSER at
    execution HEAD, all four spellings, each printing real help and exiting 0:

    ```text
      aw oc integrate --help                -> exit 0
      aw oc runipd integrate --help         -> exit 0
      aw agy integrate --help               -> exit 0
      aw agy runipd integrate --help        -> exit 0
    ```

    (`usage: runipd integrate [-h] [--repo REPO] [--run-id RUN_ID] id6`.) CORRECTION TO F7/E-07's PREMISE,
    recorded because the plan asserts the opposite: the authored spelling `aw <host> run integrate <id6>`
    DOES parse today (`aw oc run integrate --help` exits 0 - `run` is an accepted `argv_subcommand`
    alongside `runipd`). So the authored string was not broken; the printed form still uses the
    documented `integrate` alias plus its spelled-out driver form, and
    `test_the_printed_VERB_ACTUALLY_PARSES_on_both_hosts` pins all four rather than trusting any of them.

    THE ATTRIBUTION'S SUPPORTING EVIDENCE: `test_NO_runner_module_emits_that_string_which_is_why_it_is_attributed`
    scans every `*.py` under the package and finds the ONLY occurrence is the disclaiming constant itself
    (`PRE_COMMIT_STASH_ATTRIBUTION`) and its explanatory comment - so the claim "no runner module emits
    it" is measured, and the test fails loudly if that ever stops being true rather than leaving a false
    statement in operator output. Full capture: `evidence/V-03-V-07-V-08.txt`.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: the end-of-run summary pasted for a run whose review integration was refused, showing the stranded review and its lane named. PLUS an explicit statement, with the verdict line quoted, that the run's overall outcome classification was NOT changed by this item.
  - Observed evidence: rendered for the EXACT shape run `run-20260917T193010Z-1207513` recorded (a
    success-tuple `reviewed` status, which is precisely why nothing in the old summary said the work had
    not landed):

    ```text
    ╭──────────────────────────────────────────────────────────────────────────────────────────────╮
    │ AW RUN SUMMARY: run-20260917T193010Z-1207513 (opencode)                                      │
    │ Outcome: COMPLETED   Duration: 0s   Spend: $0.00   Tokens: 0 (In: 0 │ Out: 0 │ Cache: 0)     │
    │ Progress: 1/1  [██████████] 100% (1 reviewed)                                                │
    ├─────┬─────┬────────┬───────────┬────────┬──────────┬────────┬─────────────────────────────────┤
    │ Run │ Pos │ ID6    │ Set       │ Action │ Status   │ Verify │ ...                             │
    │  01 │  01 │ 63425h │ rcptwiden │ review │ reviewed │ -      │ ...                             │
    ╰─────┴─────┴────────┴───────────┴────────┴──────────┴────────┴─────────────────────────────────╯

    STRANDED WORK - NOT IN YOUR PROJECT:
      • 63425h: REVIEW NOT INTEGRATED; its work is on branch
        aw/lane/review-sweep-run-20260917T193010Z-1207513
        → why: integration refused by git: main has uncommitted local changes to file(s) this merge
          would overwrite
        → next: the review's work is PRESERVED on aw/lane/review-sweep-run-20260917T193010Z-1207513 and
          was never merged. Inspect it with `git log HEAD..aw/lane/review-sweep-...`, then recover it
          with `aw <host> integrate 63425h` (it needs a CLEAN base). Do NOT delete the branch: that is
          the one irreversible move here
    ```

    THE OVERALL OUTCOME VERDICT WAS NOT CHANGED BY THIS ITEM, and here is the verdict line quoted:

    ```text
    │ Outcome: COMPLETED   Duration: 0s   Spend: $0.00   Tokens: 0 (In: 0 │ Out: 0 │ Cache: 0)     │
    ```

    Still `COMPLETED`. Whether an unintegrated review should make a run non-`COMPLETED` is a separate
    judgement owned by approved plan `ys1dor`, so this item adds VISIBILITY only, and
    `test_the_OVERALL_OUTCOME_VERDICT_IS_NOT_CHANGED_by_this_item` pins that fence (asserting `COMPLETED`
    is present and `STRANDED` is absent from the verdict line).

    FOUR FALSE-POSITIVE / SAFETY PROPERTIES ARE ALSO PINNED, because a report that cries wolf is one an
    operator learns to skim: a LANDED review and an EXECUTE item are NOT reported (absence of the
    `review_integrated` key is not a refusal); a DEFERRED review says `NOTHING from you` and prints no
    recovery verb, so a human is never invited into a race with the run's own re-attempt; the lane BRANCH
    is printed while `preserved_worktree` (an absolute home path) is NOT; and an item somehow carrying both
    an execute and a review refusal gets exactly ONE row rather than two with contradictory advice.
    NOTE: this required editing `agent_workflows/render_stream.py`, which is NOT in `- Scope-Paths:`; see
    DECISION 16-i4ak5n-D1 and the scope justification recorded at finalize. Full capture:
    `evidence/V-03-V-07-V-08.txt`.
  - Result: pass

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
SHIP E-03 WITHOUT E-04: setting a review item to `merge-retry` while the re-attempt still runs the
EXECUTE wrapper makes the retry revalidate a review and mark it `executed`, which is strictly worse than
today's honest refusal, because the plan's own F2 complaint (a promise that is not kept) becomes a promise
that is kept WRONGLY. FOURTH, DO NOT SHIP E-03/E-04 WITHOUT E-05: the sweep lane is shared, so the first
successful re-attempt would retire the lane a second deferred review still needs, converting a recoverable
stranding into a lost one. Both are why V-04 and V-05 exist and why neither may be satisfied by a
single-review test.

BEWARE THE SHARED SPELLING: the refusal KIND and the
terminal STATUS were both the string `integration-blocked` before the 2026-09-21 rename, and confusing them is what produced this
plan's first wrong diagnosis. THE HARD-MUST HONESTY RULE: paste the ACTUAL command and test output for
every `V-*`, on BOTH hosts where the item says both; never claim a run not performed. Commit path-scoped
(`git commit -m msg -- <paths>`); never `git add -A`; never push. Before every commit run
`git diff --cached --name-only` and unstage anything not yours; this is a shared checkout and main moved
twice during this plan's own investigation. After the gate, move this plan to
`.aw/records/plans/executed/` via `aw ipd finalize`, and do not claim done until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries real observed evidence.
