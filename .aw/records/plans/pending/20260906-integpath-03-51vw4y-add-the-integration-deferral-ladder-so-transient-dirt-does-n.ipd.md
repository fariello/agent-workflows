# IPD: Add the integration deferral ladder so transient dirt does not permanently strand a verified lane

- Date: 2026-09-06
- Kind: child
- Concern: A refused lane integration is TERMINAL ON FIRST ATTEMPT. `integrate_lane_branch` calls `dirty_tree_overlap` BEFORE the gate and returns `integration-blocked` on any overlap, leaving main untouched and the lane preserved. That refusal is CORRECT and must stay. The defect is what happens next: the caller writes `integration-blocked`, which sits in `TERMINAL_STATES` (`oc_runipd.py:301-319`, `agy_runipd.py:362-380`; re-verified at HEAD `ec475372` 2026-09-07), so the item is never re-attempted for the rest of the run. One transient condition, permanent loss.
  THE REFUSAL CAUSE IS TRANSIENT BY NATURE: another writer's uncommitted file in a shared checkout. MEASURED INCIDENT, run `run-20260905T050043Z-639569` (34 items, 7h40m, $183.95 total, of which $88.23 was spent on the four refused lanes; the $165.90 in backlog `5wdoze` is not in the run record, corrected at review 2026-09-07 from `aw runs`): four items finished their work, passed their gates, finalized on their lane branches, and then failed to integrate on dirty-path overlap (`76gsmv` 08:06:32, `eyh1fu` 08:51:26, `txc9l1` 10:48:33, `uyeko5` 11:47:04). Three more (`6ypimw`, `wpomxa`, `5slbpi`) then cascaded to `dependency-blocked` because their prerequisites never reached `executed`. Seven of 34 items lost to transient dirt. At the time, all four merged clean against main; the work was never in conflict, it was refused because of WHEN it was attempted. A lane refused at 08:06 would have integrated at 08:40 when the next item finished. Nothing waited.
  A NOTE ON WHAT ALREADY EXISTS, so the executor does not mistake it for the fix: both runners already write an `integration_deferred` REASON STRING into the attempt record and an `integration_deferral` onto the item (`oc_runipd.py:6493-6495`, `agy_runipd.py:3804-3806`). That is diagnostic text only; the status still goes terminal. There is no ladder, no re-attempt, and no non-terminal status.
- Scope: Add a NON-TERMINAL `integration-deferred` status and the maintainer-approved three-rung ladder on top of the shared integration module child 02 creates: rung 1 defer-and-re-attempt while other work exists, rung 2 a doubly-bounded poll when nothing else is dispatchable, rung 3 a timeout-bounded operator ask suppressed without a TTY, then and only then terminal `integration-blocked`. Every re-attempt routes through the existing merge-and-revalidate gate. A separate `--integration-retry-limit` budget, never the correction budget.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md, tests/test_runner_shared.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: executed:6sb3yu
- Status: reviewed
- Readiness: no-go
- Set: integpath
- Order: 3
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 51vw4y
- From-Backlog: 5wdoze
- Blocks-Release: next

## Workflow history
- 2026-09-07 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review: REVIEWED - OPEN QUESTIONS; PR-301..PR-306, five FIXED, PR-301 (BLOCKER) left OPEN and escalated to OQ-04 (Blocking: yes); Readiness no-go pending that answer

- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `5wdoze`, whose three-rung design the maintainer approved on 2026-09-05 and which this plan implements rather than redesigns. Re-verified at HEAD `a4279302` rather than trusted, since the item is from 2026-09-05 and both runners churned heavily: `integration-blocked` IS still in `TERMINAL_STATES` (`oc_runipd.py:301-319`), `integration-deferred` does NOT exist as a status anywhere, `dirty_tree_overlap` still runs only at integration time, and the dispatch loop's `runnable is None` condition (the trigger rung 2 needs) is still computed at `oc_runipd.py:7024`. ONE CORRECTION TO A POSSIBLE MISREADING recorded so the executor does not skip work believing it done: `grep integration_deferred` DOES return hits in both runners (`oc_runipd.py:6493-6495`, `agy_runipd.py:3804-3806`), but those write a diagnostic REASON STRING into the attempt/item record while the status still goes terminal; they are not a partial ladder. The item's cited evidence that the four lanes merged clean is now HISTORICAL: all four branches are deleted and all four plans sit in `executed/`, recovered by hand last session, so this plan reproduces the condition synthetically instead of pointing at live lanes. Item-Dependencies declares `executed:6sb3yu` because the ladder must be written ONCE in the shared module child 02 extracts; writing it before that extraction would mean writing it twice into two already-drifted copies.

## Goal

Stop losing verified work to another process's uncommitted file. A refusal becomes a deferral that is re-attempted, then a bounded evidence-based wait, then a bounded ask, and only then terminal.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: a non-terminal status, and its budget

- [ ] E-01 Add `integration-deferred` as a NON-TERMINAL status and keep it out of `TERMINAL_STATES` in BOTH runners (`oc_runipd.py:301-319`, `agy_runipd.py:362-380`). This is the single change that makes re-attempt possible: today's `integration-blocked` is terminal, which is why nothing retried.
  AUDIT EVERY TERMINAL_STATES CONSUMER before adding the status, because a new status that some readers treat as unknown is worse than no new status. THE COMPLETE CONSUMER SET WAS RE-MEASURED AT REVIEW 2026-09-07 (the plan's earlier `oc:3451` / `agy:3052` / `agy:4246` anchors were stale); RE-LOCATE BY SYMBOL, not by these numbers:
  * `oc_runipd.py:3454` and `:7120`, `agy_runipd.py:4394`: pass `terminal_states=TERMINAL_STATES` into the SHARED orchestrator-dispatch decision (`runner_shared.decide_orchestrator_dispatch`, which at `:2807`/`:2809` splits terminal-and-not-success from terminal-and-success). A deferred child must read as NEITHER, so it keeps the orchestrator waiting (RECONSIDER) rather than terminating the Set. Confirm that is what happens.
  * `oc_runipd.py:4162` in `cascade_dependency_blocked` (agy re-exports the same function at `:336` and calls it at `:4308`, so this is ONE implementation, not two): it kills a dependent when its prerequisite's status is `in TERMINAL_STATES and not in required`. Keeping `integration-deferred` OUT of the set is therefore exactly what stops the cascade from killing dependents, which is the seven-of-34 cascade this plan exists to prevent. Assert it.
  * **`oc_runipd.py:5844` AND `agy_runipd.py:3185` ARE THE TRAP, and the plan previously mis-cited them as a mere set-difference nuance.** In `reconcile_disposition` the branch reads `if disposition in TERMINAL_STATES - {"dependency-blocked", "not-attempted"}: return disposition`. Because `integration-deferred` is deliberately NOT in `TERMINAL_STATES`, that branch is SKIPPED and control falls through to `return ("partial" if exit_code == 0 else "failed-safely")`. So a deferred item's own disposition would be SILENTLY REWRITTEN to `partial`, which IS terminal, destroying the deferral and reproducing today's permanent loss behind a green suite. This consumer MUST be taught to pass `integration-deferred` through explicitly. It is the single highest-risk edit in this E-item; do not treat it as bookkeeping.
  * NOT THIS ONE: `run_state.TERMINAL_STATES` (`run_state.py:65`) is an UNRELATED run-lifecycle vocabulary (`complete`/`cancelled`) consumed by `run_cli.py:877`, `run_engine.py:218`/`:278`, and `run_recovery.py:461`. Do not touch it and do not confuse the two while grepping.
  Enumerate what you actually find, state what each does with a deferred item, and make each choice deliberate. If the set has grown since this review, say so.
  IT MUST NOT SATISFY A DEPENDENCY. A dependent item requires its prerequisite to reach `executed`; a deferred prerequisite has NOT integrated, so `dependency_status` must treat it as unsatisfied exactly as it treats a queued item. Getting this wrong would dispatch a dependent against a base that lacks its prerequisite's commits, which is worse than the bug being fixed.
  - Depends on: none
  - Expected outcome: `integration-deferred` exists in both runners, is absent from both `TERMINAL_STATES`, does not satisfy a dependency edge, and every `TERMINAL_STATES` consumer has a recorded, deliberate behavior for it.
  - Execution state: pending

- [ ] E-02 Add a SEPARATE `--integration-retry-limit` (default 10) plus its config default, and do NOT reuse `DEFAULT_RETRY_LIMIT`. Two different quantities are being counted and conflating them is a category error the backlog item names explicitly.
  `run_recovery.DEFAULT_RETRY_LIMIT` is 2 (`run_recovery.py:67`) and counts PAID CORRECTION TURNS; its own rationale is that "a retry cannot turn failure into success by mere repetition", so a third attempt "mostly buys another paid turn". An integration re-attempt costs one `git status` and one `git merge-tree`: milliseconds, zero tokens, and repetition genuinely CAN succeed, because the blocker is another process's transient dirt.
  DO NOT CLAMP IT TO SPEC 2.1's 0..10 RANGE, which bounds the CORRECTION budget specifically. And note there is nothing to reuse even if reuse were wanted: `plan_retry`/`retry_budget_remaining` have zero production callers (backlog `trjfyy`), so this is a new counter either way.
  READ THIS BEFORE REGISTERING THE FLAG, because the obvious implementation FAILS A SHIPPED TEST and the plan's original instruction ("register through `runner_shared.RUN_POLICY_FLAGS`") cannot be followed as written. `tests/test_run_flag_surface.py` drives its assertions from spec `25kzda` 2.1 AS A FILE, IN BOTH DIRECTIONS: `test_every_flag_the_spec_declares_is_accounted_for` catches a spec flag the code lacks, and `test_no_owned_flag_is_absent_from_the_spec` catches a REGISTERED flag the spec does NOT declare (`tests/test_run_flag_surface.py:150-158`). Spec 2.1 declares NEITHER `--integration-retry-limit` NOR `--on-integration-blocked` (verified: grep returns nothing), so registering either in `RUN_POLICY_FLAGS` makes that test FAIL, while this plan's `Spec / documentation sync` section simultaneously forbids editing the spec. That is a contradiction the executor cannot resolve alone, so it is raised as OQ-04 (`Blocking: yes`) rather than left to be discovered mid-implementation.
  DO NOT "FIX" IT BY EDITING THE SPEC, and do NOT add the flags to `DECLARED_BUT_NOT_OWNED_HERE` (that list is for flags the SPEC declares and this surface deliberately does not own, which is the opposite case). Do NOT weaken or skip the test. Await OQ-04's answer; if the answer is to register the flags on host parsers OUTSIDE the spec-governed table, then implement them that way and still declare them ONCE in a shared place so the two hosts cannot diverge, which is the property `RUN_POLICY_FLAGS` exists to protect.
  - Depends on: E-01
  - Expected outcome: a distinct integration-retry budget on both hosts, default 10, frozen at queue build, provably independent of `DEFAULT_RETRY_LIMIT` (changing one does not move the other), registered by whichever route OQ-04 authorizes, with `tests/test_run_flag_surface.py` still passing unmodified.
  - Execution state: pending

### Task group 2: the three rungs

- [ ] E-03 RUNG 1, DEFER AND RE-ATTEMPT while other work exists. On a dirty-overlap refusal, mark the item `integration-deferred` rather than `integration-blocked`, and re-attempt integration at the top of the existing dispatch loop (the dispatch loop; find it by the `runnable is None` condition near `oc_runipd.py:7064` / `agy_runipd.py:4340`, NOT by a line number), which already reloads state and already runs `cascade_dependency_blocked` each iteration. Zero waiting, zero tokens, nothing blocked: the next item's completion is the natural retry trigger.
  RE-VERIFICATION IS MANDATORY ON EVERY ATTEMPT. A lane verified against yesterday's main is not verified against today's. Every re-attempt must route through `orchestrate_isolation.execute_merge_and_revalidate_gate`, which already encodes "per-lane green never implies integrated green". Do NOT shortcut to a bare `git merge` because `merge-tree` came back clean: that proves absence of TEXTUAL conflict and says nothing about whether the suite still passes.
  DECREMENT THE BUDGET PER ATTEMPT and go terminal when it is exhausted, so a permanently dirty path cannot spin the loop forever.
  - Depends on: E-02
  - Expected outcome: a refused integration is deferred, re-attempted on a later loop iteration, and integrates when the dirt clears; every attempt runs the full revalidate gate; the budget bounds the attempts.
  - Execution state: pending

- [ ] E-04 RUNG 2, a BOUNDED POLL when nothing else is dispatchable. THE TRIGGER IS NOT "is this the last item" but "is there any item I could dispatch instead", which the loop ALREADY computes as `runnable is None` (`oc_runipd.py:7064`, `agy_runipd.py:4340`). That one condition covers both the last-item case and the case where five items remain and ALL are deferred, which a last-item test would miss.
  TWO INDEPENDENT BOUNDS, BOTH REQUIRED:
  (i) max poll count (default 10);
  (ii) max staleness of activity in main. Stop polling when the NEWER of main's HEAD commit time and its most recent dirty-file mtime exceeds a threshold (default about 1h). Poll count alone is the WRONG SOLE BOUND: 10 polls at 30s is 5 minutes whether main is alive or has been idle since yesterday. If nothing has moved in main for an hour, nobody is about to commit and polling is superstition. Bound (ii) is what makes the wait EVIDENCE-BASED rather than arbitrary.
  REPORT BOTH HONESTLY. "polled 10x over 5m; main last active 3m ago" and "gave up immediately, main idle 4h" are very different facts, and the second tells the operator the dirt is abandoned and needs a human. Emit that distinction as a durable event, not only to stdout.
  - Depends on: E-03
  - Expected outcome: when `runnable is None` and deferred items exist, the runner polls instead of ending the run; it stops on EITHER bound; the report names which bound fired and main's last-activity age.
  - Execution state: pending

- [ ] E-05 RUNG 3, ASK, with a hard anti-deadlock constraint. Prompt the operator after rungs 1 and 2 fail. THE ASK MUST NOT BE ABLE TO HANG THE RUN FOREVER, or this rebuilds the unbounded-wait deadlock that `qyaime` closed, whose own honest limit was that the ask is "bounded and recorded, not architecturally prevented". So the prompt needs its OWN timeout, and on timeout it falls to terminal `integration-blocked` with the lane preserved. It must never sit there.
  SUPPRESS THE ASK AUTOMATICALLY WHEN THERE IS NO TTY. An unattended overnight run must never stop on a question nobody will see. Reuse `runner_shared.is_interactive_run` (`:1790`), which already tests BOTH a real TTY and the absence of `--unattended`, and whose docstring records why both halves are load-bearing: `--unattended` is the operator declaring there is nobody to answer, and it must win over a TTY that happens to exist. Do NOT write a second TTY test.
  ADD THE OVERRIDE: `--on-integration-blocked=defer|poll|ask|block` plus a config default, so an operator can pin the behavior. `block` reproduces today's semantics exactly, which is what makes the change safe to adopt.
  - Depends on: E-04
  - Expected outcome: the ask fires only in a genuinely interactive run, times out to terminal `integration-blocked` with the lane preserved, and never blocks indefinitely; the override selects any rung including today's `block`.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-06 Test the LADDER'S TRANSITIONS deterministically, without depending on a real concurrent writer. Drive the shared ladder directly: a refusal with other work pending yields `integration-deferred` and a re-attempt; a refusal with `runnable is None` enters the poll; an exhausted budget yields terminal `integration-blocked`; a cleared dirty path yields `integrated`.
  ASSERT THE BUDGET IS INDEPENDENT: set `--integration-retry-limit` and `DEFAULT_RETRY_LIMIT` to different values and show each governs only its own path. This is the specific confusion the backlog item warns against, so it needs a test rather than a comment.
  ASSERT BOTH RUNG-2 BOUNDS SEPARATELY: one case where the poll count is exhausted while main is still active, and one where main is stale so the poll stops EARLY regardless of count. A test that only exercises the count would pass with bound (ii) unimplemented, which is the bound that carries the design's whole argument.
  ASSERT THE ASK CANNOT HANG: simulate no answer and show the timeout falls to terminal with the lane preserved; assert the ask is SKIPPED entirely when `is_interactive_run` is false.
  ASSERT THE DEPENDENCY RULE from E-01: a dependent item must NOT be dispatched while its prerequisite is `integration-deferred`.
  - Depends on: E-05
  - Expected outcome: every rung transition, both bounds, the budget independence, the ask timeout, the no-TTY suppression, and the dependency rule are each pinned by a test.
  - Execution state: pending

- [ ] E-07 Prove the MEASURED INCIDENT would now be survived, end to end, on BOTH hosts. Reconstruct its shape synthetically in a throwaway repository, since the original lanes are gone: a lane that finalizes and then finds an overlapping dirty path in main, where the dirt is REMOVED between attempt one and attempt two. Show attempt one defers and attempt two integrates, with no agent turn spent and the full revalidate gate run on the successful attempt.
  DO BOTH HOSTS EXPLICITLY. The runner suites are asymmetric (the agy side has far fewer tests, and several of the largest diverged symbols have zero agy coverage), so a green suite can hide an agy-side regression. If you cannot demonstrate the ladder on the agy host, say so plainly rather than inferring from the oc result.
  Run the suite BARE (`python3 -m pytest`) and state before/after counts. VALIDATE IN THE REAL CHECKOUT: `tests/test_run_viewer.py` reads the gitignored `.aw/records/runs/` and fails in a bare worktree while passing in the real checkout, so green elsewhere proves nothing.
  - Depends on: E-06
  - Expected outcome: the incident's shape is survived on both hosts, deferring then integrating with no paid turn; bare suite green with counts stated.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE REFUSAL ITSELF IS CORRECT AND MUST SURVIVE. `integrate_lane_branch` refuses BEFORE running the gate so it never integrates over a contaminated base, leaving main untouched and the lane preserved. This plan changes only the DISPOSITION after a refusal, never the refusal condition.
- THE DISPATCH LOOP ALREADY DOES THE WORK RUNG 1 NEEDS: it reloads state each iteration and already calls `cascade_dependency_blocked`, so a re-attempt at the top of the loop is a small addition rather than a new mechanism.
- `runnable is None` IS ALREADY COMPUTED (`oc_runipd.py:7064`, `agy_runipd.py:4340`) and is exactly rung 2's trigger. Do not invent a last-item test.
- THE TWO BUDGETS ARE DIFFERENT QUANTITIES. `DEFAULT_RETRY_LIMIT = 2` (`run_recovery.py:67`) counts paid correction turns on the stated ground that repetition cannot turn failure into success; an integration re-attempt is milliseconds and zero tokens, and repetition genuinely can succeed. `runner_shared.RETRY_BUDGET_OWNER` names `run_recovery.DEFAULT_RETRY_LIMIT` as the single owner of that value, so do not fork it.
- `is_interactive_run` (`runner_shared.py:1790`, verified exact) ALREADY encodes the correct prompt predicate (real TTY on stdin and stderr, AND no `--unattended`, the latter winning over a TTY that happens to exist). Reuse it.
- POLICY FLAGS ARE DECLARED ONCE AND FROZEN AT QUEUE BUILD via `runner_shared.RUN_POLICY_FLAGS` and `freeze_run_policy_flags`, so a resume cannot silently change what a flag meant mid-run. The new budget belongs in that table.
- INFORMING AN AGENT IS NECESSARY AND NOT SUFFICIENT. `k1nity` measured byte-identical duplicate work on 3+ resumed runs despite an explicit prompt notice, so the ladder's correctness must live in the deterministic code path, never in prose the agent is expected to honor.
- Run the suite BARE: `python3 -m pytest`. Validate `test_run_viewer.py` in the REAL checkout.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | `integration-blocked` is TERMINAL, so a refused integration is never re-attempted for the rest of the run. RE-VERIFIED at HEAD `ec475372` 2026-09-07, with the anchors corrected (the plan's `agy_runipd.py:355` was stale). | `oc_runipd.py:301-319`, `agy_runipd.py:362-380`; `'integration-blocked' in oc.TERMINAL_STATES` is True |
| F-2 | `integration-deferred` does NOT exist as a status in either runner. | measured grep 2026-09-06 |
| F-3 | **A PARTIAL-LOOKING ARTIFACT EXISTS AND IS NOT THE LADDER.** Both runners write an `integration_deferred` reason string into the attempt record and `integration_deferral` onto the item, then set the status to a TERMINAL value anyway. An executor grepping for the name could wrongly conclude the work is done. | `oc_runipd.py:6493-6495`, `agy_runipd.py:3804-3806` (anchors corrected at review; the plan's `:6473`/`:3671` were stale) |
| F-4 | THE MEASURED INCIDENT: run `run-20260905T050043Z-639569`, 34 items, 7h40m. COST CORRECTED AT REVIEW: the run total was **$183.95** and the four refused lanes cost **$88.23** (the three cascaded items spent nothing, never having run); $165.90 appears nowhere in the durable record. Four items refused on dirty overlap (`76gsmv` 08:06:32, `eyh1fu` 08:51:26, `txc9l1` 10:48:33, `uyeko5` 11:47:04); three more cascaded to `dependency-blocked`. Seven of 34 lost to transient dirt. | `aw runs run-20260905T050043Z-639569` (34 steps, `$183.95`); per-item costs summed from its table; `events.jsonl` for the four refusals and three cascades |
| F-5 | **THE INCIDENT'S LANE EVIDENCE IS NOW HISTORICAL**, so E-07 must reconstruct the shape synthetically: all four branches are deleted and all four plans are in `.aw/records/plans/executed/`, recovered by hand last session. | `git rev-parse --verify` fails for all four; `ls .aw/records/plans/executed/` |
| F-6 | The two budgets must stay separate, and the reason is recorded in the code: `DEFAULT_RETRY_LIMIT = 2` exists because "a retry cannot turn failure into success by mere repetition", which is FALSE for an integration re-attempt whose blocker is another process's transient dirt. | `run_recovery.py:67`, `:56-64`; `runner_shared.py:1616-1618` |
| F-7 | There is nothing to reuse even if reuse were wanted: `plan_retry`/`retry_budget_remaining` have zero production callers, so the integration counter is new either way. | backlog `trjfyy` |
| F-8 | `runnable is None` is already the loop's own condition and covers both the last-item case and the all-deferred case that a last-item test would miss. | `oc_runipd.py:7064`, `agy_runipd.py:4340` (anchors corrected at review; `:7024` was stale) |
| F-9 | The prompt predicate already exists and already handles the `--unattended`-beats-TTY case, so rung 3 must reuse it rather than write a second TTY test. | `runner_shared.py:1790-1800` |
| F-10 | `TERMINAL_STATES` is consumed via SET DIFFERENCE (`TERMINAL_STATES - {"dependency-blocked", "not-attempted"}`), so a NON-member is excluded from that expression too; every consumer needs an audited decision. ANCHORS CORRECTED at review (the plan's `oc:3451`/`agy:3052`/`agy:4246` were stale). | `oc_runipd.py:5844`, `agy_runipd.py:3185` (the set-difference sites); `oc_runipd.py:3454`, `:7120`, `agy_runipd.py:4394` (shared dispatch); `oc_runipd.py:4162` (cascade) |
| F-11 | **THE SET-DIFFERENCE SITE IS A SILENT-DOWNGRADE TRAP, not a nuance.** In `reconcile_disposition`, a disposition NOT in `TERMINAL_STATES - {...}` falls through to `return ("partial" if exit_code == 0 else "failed-safely")`. Since `integration-deferred` is deliberately NOT in `TERMINAL_STATES`, a deferred item would be RELABELLED `partial`, which IS terminal, silently destroying the deferral and reproducing today's permanent loss while every ladder unit test still passed. This consumer must pass the status through explicitly. | `oc_runipd.py:5840-5846`, `agy_runipd.py:3181-3187`; verified by set-membership probe 2026-09-07 |
| F-12 | **THE CASCADE IS ONE SHARED IMPLEMENTATION, not two.** `cascade_dependency_blocked` is defined at `oc_runipd.py:4109` and RE-EXPORTED by agy (`agy_runipd.py:336`, called at `:4308`), so E-01's dependency rule needs fixing in one place and asserting on both hosts. Keeping `integration-deferred` out of `TERMINAL_STATES` is precisely what prevents the cascade from killing dependents, which is the seven-of-34 loss this plan targets. | `oc_runipd.py:4109`, `:4162`; `agy_runipd.py:336`, `:4308` |
| F-13 | **THE NEW FLAGS COLLIDE WITH A SPEC-BOUND CONTRACT TEST.** `tests/test_run_flag_surface.py` reads spec `25kzda` 2.1 AS A FILE and asserts in BOTH directions; `test_no_owned_flag_is_absent_from_the_spec` FAILS on a flag registered in `RUN_POLICY_FLAGS` that the spec does not declare. Spec 2.1 declares neither `--integration-retry-limit` nor `--on-integration-blocked`, and the spec is `Status: approved` while this plan disclaims spec-edit authority. Raised as blocking OQ-04. | `tests/test_run_flag_surface.py:150-158`; grep of the spec returns no match for either flag |
| F-14 | A SECOND, UNRELATED `TERMINAL_STATES` EXISTS and must not be confused with the runner's: `run_state.TERMINAL_STATES` is the run-lifecycle vocabulary (`complete`/`cancelled`), consumed by `run_cli.py:877`, `run_engine.py:218`/`:278`, `run_recovery.py:461`. A grep-driven audit that does not separate them would edit the wrong set. | `run_state.py:65`, `:67` |

## Proposed changes (ordered, validatable)

1. Add the non-terminal `integration-deferred` status, audit every `TERMINAL_STATES` consumer, and keep it from satisfying a dependency (E-01).
2. Add a separate `--integration-retry-limit` (default 10) through the shared policy-flag table, provably independent of the correction budget (E-02).
3. Rung 1: defer and re-attempt at the top of the existing dispatch loop, always through the revalidate gate (E-03).
4. Rung 2: poll when `runnable is None`, bounded BOTH by count and by main's activity staleness, reporting which bound fired (E-04).
5. Rung 3: a timeout-bounded ask, suppressed without a TTY, plus the `--on-integration-blocked` override whose `block` value reproduces today (E-05).
6. Pin every transition, both bounds, budget independence, the ask timeout, and the dependency rule (E-06).
7. Prove the measured incident's shape is survived on BOTH hosts (E-07).

## Deferred / out of scope (with reason)

- CONTENT-BASED NARROWING of the false-positive rate (skipping the refusal when main's dirty version of a path is byte-identical to what the merge would produce). Considered and DELIBERATELY DECLINED by the maintainer on 2026-09-05 as low-value relative to the ladder.
- PATH-PATTERN ALLOWLISTS, "docs are safe", "review records are harmless". EXPLICITLY REJECTED, not merely deferred: they reason about who probably wrote a file rather than whether it can conflict, which is the fail-open inference `d07nz2` prohibits. Narrow on content, never on category.
- THE STARTUP DIRTY-BASE GATE. That is backlog `p8ni63`, which handles dirt present BEFORE a run while this child handles dirt appearing DURING one. It is deliberately NOT in this Set's children because it is a separate refusal surface with its own consent flag; it stays open for its own plan.
- THE `integrate` VERB AND THE RESUME PATH. Child 04 (`rl67b0`) owns both, and it depends on this child so the ladder exists for it to call.
- RECONCILING `h1ksy6`, which fixes the same function but WIDENS its input set, making refusal MORE reachable. It is diagnostic-only and does not address "then what". These two must be reconciled rather than stacked blindly; that reconciliation needs `h1ksy6` to have a plan first, so it is named here and left out.
- LETTING THE RUNNER TELL ITS OWN DIRT FROM A CO-WORKER'S. That is `a8eufb` via commit trailers, and it is insufficient here by construction: trailers mark COMMITS, while the incident's dirt was 130+ UNCOMMITTED working-tree files from a stray `aw install`, carrying no trailer at all.
- RESOLVING THE DIRT. This repository's policy for un-owned dirty state is to leave it strictly alone (`AGENTS.md` shared-checkout rules). The ladder waits, asks, and reports; it never stashes, resets, or cleans.

## Scope check

- Over-scope: none. One shared module, both runners, and the three corresponding test modules.
- Scope-Paths justification: `runner_shared.py` receives the ladder and the new flag declaration (E-02..E-05) because child 02 puts the integration logic there; `oc_runipd.py` and `agy_runipd.py` each need their `TERMINAL_STATES` change and their dispatch-loop call site (E-01, E-03, E-04); the three test modules hold the assertions.
- BOTH DRIVER MODULES ARE THE HIGHEST-CONTENTION FILES IN THE REPOSITORY. Expect drift, re-locate by symbol, expect to rebase and re-run the full suite after any merge.
- Under-scope, stated rather than left as `none`: this child does not add the startup gate, does not add the `integrate` verb, does not narrow the refusal by content or category, does not reconcile `h1ksy6`, and does not resolve dirt. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, with the `N passed` summary line pasted and counts stated. MEASURE YOUR OWN BEFORE-BASELINE and judge on the DELTA: the suite is NOT green at HEAD. Measured at review 2026-09-07 (HEAD `ec475372`): `1 failed, 5613 passed, 3 skipped, 2 xfailed`, the failure being the pre-existing `tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows`. Do NOT report it as yours. The authoring-time note of `5536 passed` at HEAD `3d239cfa` is stale and superseded.
- Targeted: `tests/test_runner_shared.py`, `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`, AND `tests/test_run_flag_surface.py` (which the two new flags collide with; see OQ-04 and F-13). Run that last one explicitly and paste its result: a green run there is the evidence that OQ-04 was honored rather than worked around.
- A SYNTHETIC INCIDENT REPLAY on BOTH hosts: dirt present at attempt one, removed before attempt two, showing defer then integrate with no agent turn.
- VALIDATE IN THE REAL CHECKOUT for `tests/test_run_viewer.py` (reads the gitignored `.aw/records/runs/`).
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

THIS PLAN AMENDS SPEC `25kzda` 2.1, BY MAINTAINER RULING (OQ-04, 2026-09-07), AND THAT AMENDMENT IS PART OF THE DELIVERABLE. The spec file is declared in `- Scope-Paths:` so the runner announces the edit before the run starts and the finalize scope gate reconciles it afterwards. Supersedes this section's earlier claim that "this plan has no spec-edit authority", which was the wrong frame: specs are living contracts meant to evolve, and the obligation is to make an amendment VISIBLE, not to avoid it (`AGENTS.md:82`).

WHY 2.1 GAINS TWO FLAGS, stated here because a spec edit changes the contract every other plan is reviewed against. `--integration-retry-limit` bounds integration RE-ATTEMPTS, and `--on-integration-blocked` selects the disposition ladder rung. Both are run-policy flags frozen at queue build like every other member of `RUN_POLICY_FLAGS`, and both must be declared in 2.1 because `tests/test_run_flag_surface.py:150-158` reads the spec file in BOTH directions: a registered flag the spec does not declare fails the suite. Declaring them in the shared spec-governed table is also what keeps the two hosts from diverging, the failure `--full-auto` already demonstrated.

`--integration-retry-limit` IS NOT THE CORRECTION BUDGET and must not be described as, or clamped to, spec 2.1's 0..10 range, which bounds PAID CORRECTION TURNS specifically (F-6). Amend the spec to declare the two flags as their own quantity; do NOT widen or reuse the retry-budget clause.

DO NOT EDIT THE SPEC'S FINDING-CODE TABLE. It is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` under a byte-equality test, so editing a cell IS a code change and is outside this plan's amendment. The authorized edit is 2.1's flag declarations only.

`--help` text for the two new flags must state plainly what each does, including that `--on-integration-blocked=block` reproduces the previous behavior, since that is what makes the change adoptable. Write no em or en dashes in user-facing prose.

## Open questions

### OQ-01: Should rung 2's staleness threshold be wall-clock time or a count of loop iterations?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: WALL-CLOCK, measured against the NEWER of main's HEAD commit time and its most recent dirty-file mtime, per the maintainer-approved design. The bound's whole purpose is to distinguish "someone is actively working in main and will commit shortly" from "this dirt was abandoned yesterday", and that is a statement about elapsed real time, not about how many times this loop happened to spin. An iteration count would also couple the wait to queue size, so a run with one deferred item and nothing else to do would give up faster than an identical run with more items, which is backwards.

### OQ-02: On budget exhaustion at rung 1, should the run go straight to terminal or fall through to rung 2?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: FALL THROUGH TO RUNG 2 IF IT IS APPLICABLE, then to rung 3, then terminal. The rungs answer different questions: rung 1 asks "can I retry cheaply while doing other useful work", rung 2 asks "should I wait now that there is nothing else to do", and exhausting the first does not answer the second. Going straight to terminal on rung-1 exhaustion would make the ladder collapse to today's behavior in exactly the case it was built for, a run whose remaining items are all deferred. The bounds on rung 2 (count AND staleness) are what keep the fall-through from becoming an unbounded wait.

### OQ-03: Should a deferred item block the run from ending, or should the run end and leave it deferred?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: THE RUN MUST NOT END LEAVING AN ITEM IN A NON-TERMINAL STATE, because `integration-deferred` is by definition not a disposition and a run that ends on one has fabricated neither success nor failure, leaving the operator with no signal and the next resume with an ambiguous item. So after rungs 2 and 3 are exhausted the item MUST be resolved to terminal `integration-blocked` with the lane preserved, which is today's outcome and is honest. Child 04's `integrate` verb and automatic resume path are then the recovery route, which is why that child depends on this one.

### OQ-04: Where do the two new flags get registered, given that the shared table is spec-governed and this plan has no spec-edit authority?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-301
- Resolution or deferral rationale: RESOLVED 2026-09-07 BY MAINTAINER RULING: OPTION (a). Amend spec `25kzda` 2.1 to declare both `--integration-retry-limit` and `--on-integration-blocked`, then register them in `runner_shared.RUN_POLICY_FLAGS` as E-02 intends. The shared spec-governed table is the correct home precisely because it is what stops the two hosts diverging, which is the failure `--full-auto` already demonstrated (default `False` on one host, `True` on the other); moving the flags outside it to dodge a contract test would trade a visible blocker for the exact class of drift the table exists to prevent.
  THE PREMISE THIS PLAN DISCLAIMED IS ITSELF WRONG, AND THE MAINTAINER CORRECTED IT: A PLAN MAY AMEND A SPEC. Specs are living contracts meant to EVOLVE as we learn, not immutable history, so "this plan has no spec-edit authority" was never the right frame; the obligation is not to avoid amending a spec but to make the amendment IMPOSSIBLE TO MISS. Concretely, for this plan: list `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` in `- Scope-Paths:` (that declaration is what the runner announces before the run starts and what the finalize scope gate reconciles afterwards), and state in `Spec / documentation sync` WHY 2.1 gains two flags, since a spec edit changes the contract every other plan is reviewed against. This ruling is now doctrine at `AGENTS.md:82` and the visibility mechanism it depends on is tracked by backlog `dk16dx` (`Blocks-Release: next`), which records the measured gaps: agy imports `spec_impacts_for_queue` but never calls it, neither host announces at run END, and the start announcement swallows its own failure silently.
  THE THREE PROHIBITIONS BELOW STAND UNCHANGED. Amending 2.1 as a declared, announced, maintainer-approved change is authorized; editing the spec unilaterally and quietly is not, nor is misusing `DECLARED_BUT_NOT_OWNED_HERE` (which means the reverse: the spec declares it and this surface does not own it), nor is modifying, skipping, or xfailing `tests/test_run_flag_surface.py`. That test passing UNMODIFIED, with both flags declared in the spec and registered in the table, is the evidence this route was taken correctly; V-02 already demands it.
  ORIGINAL ESCALATION RATIONALE, retained for the record: raised at review from a measured contradiction, and not agent-resolvable because every available route either edits an approved spec or weakens a shipped contract test, and choosing among those is a maintainer call about a public flag surface.
  THE CONTRADICTION, precisely. E-02 says to register `--integration-retry-limit` in `runner_shared.RUN_POLICY_FLAGS`, and E-05 adds `--on-integration-blocked`. That table is bound to spec `25kzda` 2.1 BY A TEST THAT READS THE SPEC FILE IN BOTH DIRECTIONS: `test_no_owned_flag_is_absent_from_the_spec` fails on a registered flag the spec does not declare (`tests/test_run_flag_surface.py:150-158`). Spec 2.1 declares NEITHER flag (verified by grep at HEAD `ec475372`), and the spec is `Status: approved`. Meanwhile this plan's own `Spec / documentation sync` section says it "has no spec-edit authority". So following E-02 as written breaks the suite, and fixing the break requires an act the plan forbids.
  THE OPTIONS, each with its real cost: (a) AMEND SPEC 2.1 to declare both flags, in a separate spec change the maintainer approves, then register them in the shared table as E-02 intends. This is the cleanest end state (one declaration, both hosts, frozen at queue build) and it is exactly what the test is designed to force; its cost is that it makes this child depend on a spec amendment. (b) REGISTER THEM OUTSIDE the spec-governed table, on each host's parser via one shared helper, leaving `RUN_POLICY_FLAGS` untouched; the suite stays green and no spec changes, but the flags then sit outside the surface built to stop the two hosts diverging, which is the failure `--full-auto` already demonstrated (default `False` on one host, `True` on the other). (c) DROP THE FLAGS and hard-code the budget and the disposition policy; smallest change, but it removes the `--on-integration-blocked=block` escape hatch that the plan itself calls "what makes the change safe to adopt". This review recommends (a), with (b) acceptable if the maintainer wants the ladder to land before any spec motion; (c) is not recommended because it deletes the adoption path.
  DO NOT resolve this by editing the spec unilaterally, by adding the flags to `DECLARED_BUT_NOT_OWNED_HERE` (that list means the reverse: the spec declares it and this surface does not own it), or by modifying/skipping the test. Any of those would trade a visible blocker for an invisible one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste both runners' `TERMINAL_STATES` showing `integration-deferred` ABSENT and `integration-blocked` still present. ENUMERATE every `TERMINAL_STATES` consumer you found (at minimum the six E-01 names: `oc_runipd.py:3454`, `:4162`, `:5844`, `:7120`, `agy_runipd.py:3185`, `:4394`) and state for each what a deferred item does there. Confirm you did NOT touch the unrelated `run_state.TERMINAL_STATES` (F-14).
    THE LOAD-BEARING PASTE IS THE SILENT-DOWNGRADE TRAP (F-11): show `reconcile_disposition` returning `integration-deferred` UNCHANGED for a deferred item, on BOTH hosts. Pasting only the `TERMINAL_STATES` definitions is a FAILED validation, because the pre-fix code path silently relabels a deferred item `partial` (which IS terminal) and every ladder unit test would still pass. Prove the fall-through no longer fires: run it with `exit_code == 0` and show the result is `integration-deferred`, not `partial`.
    Paste a probe showing a dependent item is NOT dispatched while its prerequisite is `integration-deferred`, and note that `cascade_dependency_blocked` is ONE shared implementation re-exported by agy (F-12), so assert the behavior on both hosts rather than fixing it twice.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `--integration-retry-limit` in both hosts' `--help` with its default. Paste PROOF OF INDEPENDENCE: set it and `DEFAULT_RETRY_LIMIT` to different values and show each governs only its own path (an integration re-attempt count that does not move when the correction budget changes, and vice versa). Paste the frozen value from a real `state.json` `options` block, showing it is frozen at queue build like every other policy flag.
    STATE WHICH OQ-04 ROUTE YOU IMPLEMENTED and paste `python3 -m pytest tests/test_run_flag_surface.py` PASSING, unmodified. If you registered the flags in `RUN_POLICY_FLAGS`, that test passing is evidence spec 2.1 was amended as option (a) authorizes; if you registered them elsewhere, say so and show the single shared declaration that keeps the two hosts from diverging. A modified, skipped, or xfailed `test_run_flag_surface.py` is a FAILED validation, as is adding either flag to `DECLARED_BUT_NOT_OWNED_HERE`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a run where attempt one refuses on dirty overlap and yields `integration-deferred` (not `integration-blocked`), then a later loop iteration integrates after the dirt clears. Paste evidence the REVALIDATE GATE ran on the successful attempt, not a bare `git merge`: name the gate function and show it was invoked. Paste the budget decrementing per attempt and going terminal when exhausted.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the trigger condition showing it is `runnable is None` and NOT a last-item test, plus a case with several remaining items ALL deferred to show that case is covered. Paste TWO separate bound demonstrations: (i) poll count exhausted while main is still active; (ii) main STALE so polling stops early regardless of remaining count. Paste the report line for each, showing it names which bound fired and main's last-activity age. A paste covering only the count is a FAILED validation, since bound (ii) carries the design's argument.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the ask firing in an interactive run, and paste it being SKIPPED with `is_interactive_run` false (both the no-TTY case and the `--unattended` case, since that flag must beat a real TTY). Paste the TIMEOUT path: no answer, prompt times out, item goes terminal `integration-blocked`, lane branch still present (`git branch --list` pasted). State explicitly that no code path can wait on the prompt indefinitely, and name the `qyaime` deadlock this bound exists to avoid rebuilding. Paste `--on-integration-blocked=block` reproducing today's behavior exactly.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the ACTUAL output of the ladder transition tests: defer-then-integrate, budget exhaustion to terminal, both rung-2 bounds separately, the ask timeout, the no-TTY suppression, and the dependency rule. For the budget-independence test, quote the assertion. Confirm no test depends on a real concurrent writer or on wall-clock sleeping long enough to be flaky; state how time and dirt were controlled.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the synthetic incident replay for BOTH hosts: attempt one defers, dirt is removed, attempt two integrates, no agent turn spent. Show the merge commit on main for each host. Paste the BARE `python3 -m pytest` summary line with before/after counts. State that `test_run_viewer.py` was validated in the REAL checkout and why. If the agy host could not be demonstrated, SAY SO PLAINLY rather than inferring from the oc result; an inferred agy result is a FAILED validation.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). OQ-01 through OQ-03 are resolved; OQ-04 is OPEN and `Blocking: yes`, so this plan is NOT approvable until the maintainer answers it. That is deliberate: OQ-04 records a measured contradiction between E-02/E-05's flag registration and the spec-bound contract test `tests/test_run_flag_surface.py`, and every route out of it either amends an approved spec or moves the flags off the shared surface. `aw set approved` refuses over an unresolved blocking question (`plan_readiness.has_unresolved_blocking_question`), which is the correct fail-closed behavior here: an executor who started this plan without that answer would hit a failing test with no authorized fix.

DEPENDENCY: this child declares `- Item-Dependencies: executed:6sb3yu` and MUST NOT run before child 02. This edge is GENUINE, unlike the two the review of children 02 and 03's siblings had to correct: the ladder belongs in the SHARED integration module, and written before the extraction it would be written twice into two copies measured as drifted (0.651 similarity, re-verified 2026-09-07), which is the outcome three of the four source backlog items explicitly ask to avoid. Note also that child 02 may move a THIRD symbol (`build_lane_outcome`) under its authorized narrow exception, so re-read the shared module's actual contents rather than assuming only two functions arrived. The runner re-checks dependencies at dispatch, so a queued-together Set is safe.

Scope fence: touch ONLY the six paths in `Scope-Paths`. Do NOT change the refusal CONDITION (`dirty_tree_overlap`'s logic or when it is consulted); this plan changes only the disposition afterwards. Do NOT reuse or modify `DEFAULT_RETRY_LIMIT`. Do NOT clamp the new budget to spec 2.1's 0..10 correction range. Do NOT narrow the refusal by content or by path category. Do NOT stash, reset, clean, or commit anything to resolve dirt. Do NOT add the startup gate or the `integrate` verb. Do NOT edit `agent_workflows/hooks/executed_transition_gate.py`. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT and both driver modules are the highest-contention files in it: run `aw runs` before starting, and if a driver file is being changed under you and the two sets of changes cannot be safely combined, STOP and report rather than overwriting.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. Find `TERMINAL_STATES`, the dispatch loop's `runnable is None`, `is_interactive_run`, `RUN_POLICY_FLAGS`, and the shared integration function by name.

TWO ITEMS CARRY THE MOST RISK, and they fail in opposite directions. V-04 bound (ii) is the one most likely to be skipped, because a poll-count bound alone LOOKS like a complete implementation and every count-based test would pass without it; without it the wait is arbitrary rather than evidence-based, which is the design's entire argument. V-05's timeout is the one most likely to reintroduce a deadlock: an ask with no timeout rebuilds exactly what `qyaime` closed, and an unattended overnight run that stops on an unseen question is strictly worse than today's terminal refusal. If either cannot be shown green, STOP and report.

DO NOT LET THE PARTIAL ARTIFACT FOOL YOU. `integration_deferred` already appears in both runners as a diagnostic reason string while the status still goes terminal (F-3). Grepping the name and concluding the ladder exists would leave this plan's entire substance unbuilt behind a green suite.

On completion, close backlog `5wdoze`, which this plan carries as `- From-Backlog:` and whose `- Blocks-Release: next` gate it inherits. Child 02 shares that provenance but delivers only the seam, so `5wdoze` closes HERE, not there.
