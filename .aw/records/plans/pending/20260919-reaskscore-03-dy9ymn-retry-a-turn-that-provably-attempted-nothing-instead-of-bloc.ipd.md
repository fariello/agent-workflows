# IPD: Retry a turn that provably attempted nothing instead of blocking its Set with a terminal partial

- Date: 2026-09-19
- Kind: child
- Concern: A TURN THAT PERFORMED NO WORK AT ALL IS RECORDED AS A TERMINAL `partial`, WHICH IS INDISTINGUISHABLE FROM A TURN THAT GENUINELY TRIED AND FELL SHORT, AND ONE SUCH ITEM TAKES ITS WHOLE SET DOWN. `partial` is in `TERMINAL_STATES` (`oc_runipd.py:470-488`) and outside `EXECUTION_SUCCESS_STATES` (`:492`), so `cascade_dependency_blocked` (`:4416-4489`) correctly marks every dependent `dependency-blocked` and `decide_orchestrator_dispatch` correctly refuses the parent. Measured 2026-09-18 in `run-20260918T045802Z-2547360`: `zqs0px` ended `partial` after 36 seconds having written no outcome, performed no E-item, left `starting_head == ending_head` and a clean tree with zero lane commits, and took `qmgn12`, `di08i9` and `rgaasb` down with it for a `BLOCKED` run with 1 of 5 executed. The same shape recurred on 2026-09-18 twice more. THE CASCADE IS CORRECT; THE TRIGGER IS NOT. Nothing in the codebase distinguishes "attempted nothing" from "attempted and fell short": a search for zero-work detection finds none, and `files_changed` appears once, as a key in a prompt literal (`runner_shared.py:10573`), read by nobody.
- Scope: Add a NARROW, evidence-based "provably attempted nothing" predicate over facts the attempt already records, and on that verdict re-queue the item for one more attempt inside the existing retry budget instead of recording a terminal `partial`. Consume `ty7w6o`'s host-truncation signal as corroborating evidence. EXCLUDES loosening any dependency, success-bar, or orchestrator-retirement predicate: the cascade is right. EXCLUDES retrying any item that produced ANY evidence of work. EXCLUDES the rescoring fix (`skn8uk`) and the truncation signal itself (`ty7w6o`). EXCLUDES telling the agent its remaining turn budget, which is `x7wfyx`'s other half and is a prompt change with its own review surface.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_turn_bounds.py
- Item-Dependencies: executed:ty7w6o
- Status: approved
- Priority: medium
- Readiness: go-pending-approval
- Set: reaskscore
- Order: 3
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- From-Backlog: x7wfyx
- Blocks-Release: next
- Work-Kind: bug
- Id: dy9ymn
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-23 approved (aw set): Backfilled Priority by inheritance from source backlog item x7wfyx (planprio Order 02, plan 8u6770, E-03); no lifecycle transition occurred.
- 2026-09-19 approved (aw set): status set to approved

- 2026-09-19 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 all FIXED, none deferred, none open; Readiness `go-pending-approval`. Reviewed at HEAD `cf9c0d70`; the plan was byte-identical to the sealed lane input and the tree was clean, so no pre-review snapshot. `aw ipd lint --phase author` reported `clean` before the revisions and `--phase review-finalize` reports `clean` after them. Watermark 05 -> 06 (one item added). THE DESIGN IS RIGHT: an evidence-based predicate, a refusal to loosen the cascade, and a bounded retry are the correct shape, and I verified the requeue shapes, `requeue_interrupted`'s indeterminate refusal, the `holds_work`-after-merge warning, `ending_head`/`ending_status` being recorded unconditionally before the disposition, and the `graduated` transition on `x7wfyx` (which does write history and does preserve `Blocks-Release`). FOUR SUBSTANTIVE CORRECTIONS, each measured. (1) THE CITED REQUEUE SEAM CANNOT FIRE: `oc_runipd.py:6455-6468` is at function-relative 56-69 of `run_queue`, BEFORE `while True:` at 131, so it is a resume-time run-once block; a zero-work turn happens at the `execute_item` call at 298. A check placed there would never observe an in-run turn. Split out as new E-06 with the correct window (anywhere between `execute_item`'s return and the next iteration's cascade at 147, which is generous rather than tight) plus V-06 and a negative control. (2) TWO OF E-01'S FOUR CONDITIONS ARE VACUOUS FOR THE MEASURED SHAPE: `ending_head` and `ending_status` are `git_head(repo)`/`git_status(repo)` on the MAIN checkout while the lane is `work_dir`, so on an isolated turn both hold even for a lane that committed real work; E-01 now reads the lane's own `commits_ahead`/`dirty` via the shipped `describe_lane`/`inspect_lane`, and V-02 now requires each negative control be built in the mode where it can actually fail. (3) THE BUDGET HAS NO SPEND COUNTER: the frozen limit IS readable from `state["options"]["retry_budget"]`, but nothing reads it and `plan_retry`/`retry_budget_remaining` have zero callers outside their module (both need a `RunEngine` over a `ledger.jsonl` no driver run writes), so E-04's three budget behaviors had nothing to read; E-04 now counts on the item mirroring the shipped `integration_attempts` pattern, V-04 demands the counter's value be pasted and a case above one retry, and OQ-04 records the relationship to `xipfy1`. (4) A SELF-CARRIER WOULD HAVE REFUSED THIS PLAN'S OWN FINALIZE: OQ-02 carried `- Carrier: dy9ymn`, which goes terminal exactly when the plan finalizes (measured: 1 obligation flips to failing at `error` severity at the `pre-transition` checkpoint the gate itself requires); now `Carrier-Declined`, re-measured at 0. ALSO: the `graduated` transition MOVES an undeclared path, so the Scope check now states it and OQ-05 names the two supported routes; E-02's refusals are recorded as defence-in-depth rather than the live guard; and all five `runner_shared.py` citations are drifted and re-anchored by symbol. Full record: `.aw/records/reviews/20260919-reaskscore-03-dy9ymn-retry-a-turn-that-provably-attempted-nothing-instead-of-bloc.review.md`.
- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored as the driver-side half of backlog `x7wfyx` (its item B), which was split off `q1z9gn` when only the prompt half landed. Declares `executed:ty7w6o` because the host-truncation signal is the corroborating evidence this predicate consumes. Inherits `Blocks-Release: next` from `x7wfyx`.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Require EVIDENCE THAT SOMETHING WAS ATTEMPTED before a single item is allowed to block its whole Set.
A turn that provably did nothing should cost one retry, not four items.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the predicate

- [x] E-01 ADD A PURE, HOST-NEUTRAL PREDICATE `turn_attempted_nothing(...)` TO `runner_shared.py`, RETURNING A REASONED VERDICT (not a bare bool) OVER FACTS THE ATTEMPT ALREADY RECORDS. It must require ALL of these to hold, so that any single sign of work refuses the verdict: no outcome file was written for the attempt; `starting_head == ending_head`; the lane branch holds NO commits beyond its base (or, for a shared-tree turn, no commit was made); and the working tree is CLEAN (`attempt["ending_status"]` empty). It MUST be CONJUNCTIVE and FAIL CLOSED: if any input is missing or unreadable, the verdict is "cannot prove nothing was attempted", which means NO retry and today's behavior. The verdict must carry the reason and the facts it read, because this predicate authorizes spending a full turn's tokens and a human must be able to audit why. DO NOT reuse `worktree_lease.holds_work` as the commit test: `runner_shared` records that it stays True FOREVER after a `--no-ff` merge (the comment measuring `BEFORE MERGE`/`AFTER MERGE` both reporting `holds_work=True`), so it cannot answer "did THIS attempt commit anything". That warning is correct; only its line offset has drifted, so anchor it by that comment.
  TWO OF THE FOUR CONDITIONS ARE VACUOUS FOR THE MEASURED SHAPE, AND THE PREDICATE MUST NOT REST ON THEM. Measured at review: `attempt["ending_head"]` and `attempt["ending_status"]` are both written as `git_head(repo)` / `git_status(repo)`, where `repo` is the MAIN CHECKOUT, while the lane is `work_dir`. The measured failure is an ISOLATED lane turn, and a lane agent never moves the main checkout's HEAD and never dirties its tree, so on an isolated turn `starting_head == ending_head` and an empty `ending_status` are TRUE BY CONSTRUCTION - true even for a lane that committed substantial real work. They are genuine signals only for a `--no-isolate-worktree` turn, where the agent works in `repo` directly.
  SO THE LOAD-BEARING CONDITIONS FOR THE MEASURED CASE ARE (1) NO OUTCOME FILE AND (3) NO LANE COMMIT, and condition (3) must be read from LANE FACTS rather than from the attempt's main-checkout fields. Use the shipped lane inspector: `runner_shared.describe_lane` returns `commits_ahead` and `dirty` from `worktree_lease.inspect_lane(repo, lane_id, base_commit=base)`, which is the only source that answers "did THIS lane commit anything" and which also gives the lane's own dirty state - the correct substitute for condition (4) on an isolated turn. Keep conditions (2) and (4) as written for the shared-tree case, but DOCUMENT AT THE PREDICATE which conditions carry weight in which mode, because a reader who believes all four are always load-bearing will over-trust the verdict on an isolated turn.
  - Depends on: none
  - Expected outcome: `runner_shared.turn_attempted_nothing` exists, is pure, returns a reasoned verdict, refuses on any missing input, reads the lane's own `commits_ahead`/`dirty` for an isolated turn rather than the main checkout's head and status, and documents which conditions are meaningful in which mode.
  - Execution state: performed

- [x] E-02 REQUIRE THE PREDICATE TO REFUSE ON EVERY NON-ATTEMPT STATUS AND EVERY DELIBERATE OUTCOME, so a retry can never override an intent. It MUST refuse for: a deliberately stopped or forced item (`runner_stop.is_indeterminate` and the stopped/forced dispositions), which spec `c4gd2h` R19 already forbids re-running and which `requeue_interrupted` already refuses (`oc_runipd.py:6290-6296`); a `merge-retry` item (renamed from `integration-deferred` on 2026-09-21; prefer the constant `runner_shared.INTEGRATION_DEFERRED_STATUS`), which is non-terminal and owned by the integration ladder; a `dependency-blocked` or `not-attempted` item, which never ran; and a `review` action, whose scoring reads the plan's `- Status:` and whose zero-work case is a different question. Reuse the EXISTING refusal predicates rather than restating their conditions, so the two routes cannot disagree - the same reasoning `oc_runipd.py:6436-6441` gives for gating `--retry-incomplete` on the same predicate as `requeue_interrupted`.
  MOST OF THESE REFUSALS ARE DEFENCE IN DEPTH, NOT LIVE PATHS, and saying so keeps an implementer's attention on the condition that actually protects the change. Measured at review: the zero-work branch is entered only for an item whose disposition is the terminal `partial`, and each protected class carries a DIFFERENT status at that point - a stopped item `interrupted`, a forced one `unknown_outcome`, a deferred one `merge-retry`, an unrun one `dependency-blocked` or `not-attempted` - so the branch is not reached for any of them. A `review` action likewise cannot present as `partial`: its scorer returns `reviewed`, `approved` or `failed-safely`. KEEP EVERY REFUSAL ANYWAY (a later change to the disposition vocabulary, or a caller that invokes the predicate from a different seam, would make them live, and fail-closed redundancy is cheap here), but do not treat them as the safety property: the EVIDENCE CONJUNCTION in E-01 is what prevents a retry over real work.
  - Depends on: E-01
  - Expected outcome: each refused class is covered by a test that fails if the refusal is removed, and the code records which refusals are currently unreachable so a later reader does not mistake them for the live guard.
  - Execution state: performed

- [x] E-03 TREAT `ty7w6o`'s HOST-TRUNCATION RECORD AS CORROBORATION, AND DECIDE AND DOCUMENT ITS EXACT ROLE. The natural reading is that `attempt["host_truncation"]` STRENGTHENS the verdict (the host itself admits it killed the work), and the design decision to make is whether it is REQUIRED or merely SUPPORTING. Requiring it would confine the retry to the one measured cause and refuse a future zero-work turn with another cause; treating it as supporting makes the predicate cause-agnostic. Choose ONE, implement it, and RECORD THE CHOICE WITH ITS REASON where a later reader will find it, because a reader who assumes the other reading will mis-predict when a retry fires. Whichever is chosen, a truncation record MUST NOT by itself authorize a retry: the four evidence conditions in E-01 still all have to hold, since a host may truncate a turn that had already done real work.
  - Depends on: E-01
  - Expected outcome: the role of the truncation signal is implemented and documented at the predicate, with a test for both a truncated and a non-truncated zero-work turn.
  - Execution state: performed

### Task group 2: act on it, bounded

- [x] E-04 RE-QUEUE THE ITEM FOR ONE MORE ATTEMPT INSTEAD OF RECORDING THE TERMINAL `partial`, BOUNDED BY THE EXISTING RETRY BUDGET AND BY NO NEW KNOB. Spec `25kzda` 5.5 governs this: the budget is `--retry-budget` (0..10, default 2), it "counts correction attempts after the initial attempt", it "cannot be raised on resume", and `0` MUST mean no retry at all. A zero-work turn is a legitimate charge against this budget: spec 5.5 lists "host spawn failure" and "host nonzero exit that did not create an ambiguous side effect" as retryable, and a turn that provably created NO side effect is the cleanest possible member of that class. When the budget is exhausted the terminal `partial` stands, which is the honest outcome.
  THE LIMIT IS READABLE BUT NO SPEND COUNTER EXISTS, AND THIS IS THE ONE THING THAT MAKES E-04 MORE WORK THAN IT LOOKS. Measured at review, precisely: `freeze_run_policy_flags` resolves `--retry-budget` through `resolve_retry_budget` and the effective integer lands in `state["options"]["retry_budget"]` at queue build, so READING the limit is a one-liner, exactly as `integration_retry_limit` is read (`int(options.get("integration_retry_limit", DEFAULT_INTEGRATION_RETRY_LIMIT))` in `runner_shared`). What does NOT exist is any per-item accounting of budget already spent: `grep` finds NO read of the frozen `retry_budget` anywhere in `agent_workflows/`, and `run_recovery.plan_retry` / `retry_budget_remaining` have zero callers outside their own module because both require a `RunEngine` over a hash-chained `ledger.jsonl` that no driver run writes. So "one retry within budget", "budget exhausted" and "`--retry-budget 0`" - all three demanded by this item and by `V-04` - have nothing to read today.
  COUNT IT ON THE ITEM, MIRRORING THE SHIPPED PRECEDENT, and do NOT reach for `plan_retry`. `runner_shared` already solves this exact problem for the sibling budget: it reads the frozen limit from options, computes `attempts_used = int(item.get("integration_attempts", 0)) + 1`, writes that back onto the item, and passes both to a pure decision function. Copy that shape with a distinct per-item key (e.g. `item["zero_work_retries"]`), which keeps the counter durable in `state.json` across a resume, needs no ledger, and introduces NO SECOND KNOB - the frozen `--retry-budget` remains the only limit, so the category error `runner_shared` warns of (conflating it with `--integration-retry-limit`) is not committed. Note that `xipfy1` (`approved`, release-blocking) owns wiring the budget generally through `plan_retry`; this item deliberately does NOT do that work, and `OQ-04` records the relationship so the two do not collide.
  THE MECHANISM must reuse the existing requeue shape (`item["status"] = "queued"` with `item["recovery_next"] = True`, remembering `item["requeue_from_status"]`) rather than inventing a second dispatch path. BUT SEE THE SEAM WARNING IN E-06 BELOW: the site this plan originally cited for that shape is the wrong PLACE to put the new call, even though it is the right SHAPE to copy.
  - Depends on: E-02, E-03
  - Expected outcome: a provably-zero-work item is re-dispatched once within budget and reaches a real terminal state; with `--retry-budget 0` it is `partial` immediately; with the budget exhausted it is `partial`; the count lives on the item mirroring `integration_attempts`, and no new flag is added.
  - Execution state: performed

- [x] E-06 PUT THE REQUEUE WHERE IT CAN ACTUALLY FIRE: AFTER `execute_item` RETURNS, INSIDE THE DISPATCH LOOP. This is a separate item because the plan originally named a seam that CANNOT work, and an executor who copied the shape into the cited location would ship a retry that never runs. MEASURED at review by locating `run_queue`'s own structure: the `--retry-incomplete` block the plan cites (`oc_runipd.py:6455-6468`) sits at function-relative lines 56 to 69, which is BEFORE `while True:` at function-relative 131 - it is a resume-time, run-once block that inspects statuses left by a PREVIOUS invocation. A zero-work turn happens DURING the run, at the `execute_item(...)` call at function-relative 298, so a check placed in the pre-loop block would never observe it.
  THE CORRECT WINDOW IS GENEROUS, WHICH IS WORTH KNOWING BECAUSE THE PLAN PRESENTS IT AS TIGHT: `cascade_dependency_blocked` runs at the TOP of the loop (function-relative 147), so it first observes this turn's `partial` on the NEXT iteration. Anything between `execute_item`'s return and that next iteration is early enough. Place the verdict-and-requeue immediately after the `execute_item` call's own error handling, before the loop continues, on BOTH hosts (`agy_runipd`'s `run_queue` mirrors this structure). The plan's ordering CLAIM is correct and its stated reason is correct; only the cited location was wrong.
  - Depends on: E-04
  - Expected outcome: the requeue is reached from inside the dispatch loop after `execute_item` returns on both hosts, and a test demonstrates it fires for a turn that happened during the run (not only for a resumed one).
  - Execution state: performed

- [x] E-05 MAKE THE RETRY AUDITABLE AND LOUD, because it spends money. Append a `zero-work-retry` event naming `id6`, `attempt`, the verdict's reason, the facts it read, the budget remaining, and whether a host truncation corroborated it; print one short line at the time; and record the decision on the item so `aw runs` can report it afterwards. Emit NOTHING when the predicate refuses, so the event's presence means "a turn was re-dispatched because it provably did nothing" and never "the check ran". A refused verdict on an item that ends `partial` SHOULD still be visible in the run report as the reason it was not retried, since "we looked and could not prove it" is exactly what a human needs to see to judge whether the predicate is too strict.
  - Depends on: E-04
  - Expected outcome: `events.jsonl` carries `zero-work-retry` for each retry and none for a refusal; the run report names both the retry and the refusal reason.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- THE REQUEUE MECHANISM ALREADY EXISTS AND HAS A SHAPE TO COPY. `--retry-incomplete` flips `item["status"] = "queued"` with `item["recovery_next"] = True` and remembers `item["requeue_from_status"]` (`oc_runipd.py:6455-6468`); `requeue_interrupted` (`:6290`) is the recovery-mode twin. Note that `_reset_item_for_retry`, named in backlog `x7wfyx`'s fix sketch, DOES NOT EXIST in the package - the sketch is wrong on that detail and an implementer must not go looking for it.
- THE DISPATCH LOOP RE-READS STATE EVERY ITERATION, so a requeued item is naturally picked up: `run_queue`'s `while True` (`oc_runipd.py:6530`) reloads state, cascades, retries deferred integrations, and re-selects from `queued`. This is the same "the loop is the retry trigger" property `integpath-03` relied on (`:6548-6557`).
- ORDERING AGAINST THE CASCADE IS LOAD-BEARING. `cascade_dependency_blocked` runs at the TOP of the loop (`:6546`) and marks dependents of any non-success terminal item. So the requeue must happen BEFORE the cascade observes the `partial`, or the siblings are already blocked and the retry rescues nothing. `integration-deferred`'s placement records exactly this lesson: it is ordered after the cascade because it is NOT terminal, which is what "converts the measured seven-of-34 cascade loss into no loss at all" (`:6553-6557`).
- THE RETRY BUDGET IS ALREADY RESOLVED AND FROZEN ONCE, AND IS READ BY NOBODY. `runner_shared.resolve_retry_budget` delegates the 0..10 bound to `run_recovery.validate_retry_budget` (`run_recovery.py:136`, accurate) and `freeze_run_policy_flags` puts the effective integer into `state["options"]["retry_budget"]`. Read it; do not re-resolve it and do not add a knob. MEASURED AT REVIEW, and this is the gap E-04 must close: NOTHING in `agent_workflows/` reads that frozen value back, and `run_recovery.plan_retry` / `retry_budget_remaining` have ZERO callers outside their own module (both need a `RunEngine` over a `ledger.jsonl` no driver run writes). The LIMIT is readable; the SPEND COUNTER does not exist. The shipped precedent to copy is the sibling budget's: read the frozen limit from options, keep `attempts_used` on the ITEM (`integration_attempts`), and pass both to a pure decision function.
- EVERY `runner_shared.py` LINE CITATION IN THIS PLAN HAS DRIFTED; the `oc_runipd.py`, `agy_runipd.py`, `run_recovery.py` and `tests/` citations are all accurate. Measured at review across the plan's distinct citations: the five `runner_shared.py` offsets (`:10573`, `:1141`, `:5564`, `:12483`, `:2544`) now land on unrelated lines, because that file grew after this plan was authored. None is out of range, so none announces itself. RE-DERIVE EACH BY SYMBOL; the substance of every claim was re-verified at review and holds.
- A RETRY CANNOT TURN FAILURE INTO SUCCESS BY REPETITION. `run_recovery.plan_retry`'s guarantee 3 (`run_recovery.py:285-287`) states it, and guarantee 5 invalidates evidence bound to the retried step. That is the principle bounding this change: the predicate must be narrow enough that a deterministically-failing item cannot loop.
- THE THREE COPIES PROBLEM. `reconcile_disposition` lives per host (`oc_runipd.py:6027`, `agy_runipd.py:2903`) plus a shared fallback, and `execute_item_core` binds the host copy by `getattr` (`runner_shared.py:12483`). Cross-host equality of `TERMINAL_STATES` and `EXECUTION_SUCCESS_STATES` is test-pinned (`tests/test_rununify_run_queue.py:165`). Put the RULE in `runner_shared.py` once; the two drivers are declared here only for the requeue seam.

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | A zero-work turn is currently terminal and takes its Set with it. | `run-20260918T045802Z-2547360`: `02 zqs0px partial 36s`, then `qmgn12`/`di08i9`/`rgaasb` all `dependency-blocked`; run `BLOCKED`, 1 of 5 executed. |
| F-2 | The zero-work evidence is already recorded on the attempt, so no new capture is needed. | Same run: `starting_head == ending_head == 7c233993`, `git status` clean, lane holds 0 commits, `outcomes/` holds no file for the item. |
| F-3 | No zero-work detection exists anywhere in product code today. | Searches for `zero-work`, `did_work`, `no-op turn`, `empty turn` across `agent_workflows/` return nothing; `files_changed` appears once (`runner_shared.py:10573`) as a prompt-literal key that nothing reads back. |
| F-4 | The cascade is correct and must not be loosened. | `partial` is terminal (`oc_runipd.py:470-488`) and outside `EXECUTION_SUCCESS_STATES` (`:492`); `cascade_dependency_blocked` (`:4416-4489`) is doing exactly its job. Loosening it would dispatch a dependent against a base lacking the commits it depends on. |
| F-5 | The retry budget already exists, is already bounded 0..10, and is already frozen per run. | `runner_shared.resolve_retry_budget:5564` -> `run_recovery.validate_retry_budget:136`; frozen at `:6043-6044`; spec `25kzda` 5.5. |
| F-6 | `x7wfyx`'s fix sketch names a symbol that does not exist, so the sketch cannot be followed literally. | `_reset_item_for_retry` has no definition in `agent_workflows/`. The real shapes are `requeue_interrupted` (`oc_runipd.py:6290`) and the `--retry-incomplete` block (`:6436-6468`). |
| F-7 | The measured cause is a HOST truncation, not an agent choice, which is why a prompt fix cannot close this. | `ty7w6o` F-1/F-2: the agent issued a plain foreground `run_command` and the host backgrounded then terminated it, reporting `SUCCESS`. |
| F-8 | An interrupted item is ALREADY refused a silent re-run, and that refusal must be reused not re-derived. | `requeue_interrupted` skips an indeterminate item (`oc_runipd.py:6290-6296`, spec `c4gd2h` R19); `--retry-incomplete` is gated on the SAME predicate for the stated reason that "the two routes cannot disagree" (`:6436-6441`). |

## Proposed changes (ordered, validatable)

1. `runner_shared.py`: `turn_attempted_nothing(...)`, pure, conjunctive, fail-closed, returning a reasoned verdict, reading the LANE's own `commits_ahead`/`dirty` for an isolated turn rather than the main checkout's head and status, and documenting which conditions bite in which mode (E-01).
2. `runner_shared.py`: refusals for stopped/forced, deferred, dependency-blocked/not-attempted, and review items, reusing the existing predicates, with a note recording which are currently unreachable (E-02).
3. `runner_shared.py`: consume `attempt["host_truncation"]` in the documented role, required or supporting, decided and recorded (E-03).
4. `runner_shared.py` + the two drivers: re-queue once within the frozen `--retry-budget`, counting spend on the ITEM in the shipped `integration_attempts` shape rather than through `plan_retry`, using the existing requeue shape (E-04).
5. `oc_runipd.py` + `agy_runipd.py`: place that requeue INSIDE the dispatch loop after `execute_item` returns, not in the pre-loop `--retry-incomplete` block, so it fires for an in-run turn (E-06).
6. `runner_shared.py`: `zero-work-retry` event, one printed line, decision recorded on the item, plus the refusal reason surfaced in the report (E-05).
7. `tests/test_turn_bounds.py`: the conjunction with each negative control built in the mode where it can actually fail, each refusal class, both truncation cases, budget 0 / one / above-one / exhausted with the counter's value pasted, the ordering-against-the-cascade property, and the in-run-versus-resumed distinction.

## Deferred / out of scope (with reason)

- TELLING THE AGENT ITS REMAINING TURN BUDGET (`x7wfyx` item A) is NOT done here. It is a change to the shared execute prompt, which has its own regression surface (`tests/test_turn_bounds.py:875-931` asserts three properties, and `tests/test_defect_report.py:188` hard-codes a per-host prompt-length BASELINE that any prompt edit re-bases). Bundling a prompt change with a dispatch change would put two unrelated review surfaces in one plan. It also no longer addresses the measured cause: per F-7 the agent was not choosing when to stop.
  - Carrier: 4bhxni
  - CARRIER REPOINTED AT EXECUTION, from `x7wfyx` to the newly filed `4bhxni`, because `x7wfyx` was
    closed `done` on 2026-09-22 under the HANDOFF rule (citing THIS plan's `From-Backlog` plus its
    matching `Blocks-Release`) while this plan's scope excludes item A in terms. So item A had no live
    carrier and `aw ipd lint` reported `check.ipd-uncarried-obligation` for exactly this obligation
    and for `OQ-04`. `x7wfyx` is NOT reopened or edited: its close was legitimate on the rule as
    written, and the honest repair is a live successor rather than rewriting a correct history.
    `4bhxni` is filed `followup` rather than `bug` and carries NO release gate, because per F-7 the
    measured cause was a HOST truncation and not the agent choosing when to stop, so the prompt half
    no longer addresses the measured defect.
- NO DEPENDENCY, SUCCESS-BAR, OR RETIREMENT PREDICATE IS TOUCHED (F-4). The whole design of this plan is to fix the trigger and leave the propagation alone.
  - Carrier-Declined: A rejected alternative, recorded so it is not re-proposed. All four measured cascades were correct behavior on a wrong input, so there is no future state in which loosening them becomes right.
- NO NEW RETRY KNOB (F-5). Spec `25kzda` 5.5's budget governs, and `runner_shared.py:2544-2545` names conflating it with `--integration-retry-limit` as a category error.
  - Carrier-Declined: Nothing to carry: the existing frozen budget is judged sufficient, so declining to add a knob leaves no outstanding work.
- NOT RETRYING AN ITEM THAT PRODUCED ANY EVIDENCE OF WORK, even a dirty tree with no commit. The conjunction is deliberately strict: an uncommitted edit is work, and re-dispatching over it risks the agent duplicating or fighting its own prior changes. The honest cost is that a turn which did a little and then died is NOT retried; that is the safe direction, and it is why the predicate must be narrow rather than "the item did not reach executed".
  - Carrier-Declined: Nothing to carry: the strictness is the designed SAFETY property, not a gap. Re-dispatching over uncommitted work risks the agent fighting its own prior changes, so there is no future state in which widening this is desirable.
- NOT RETRYING A DELIBERATELY STOPPED ITEM (E-02, F-8). Spec `c4gd2h` R19 forbids it and an existing predicate already refuses it.
  - Carrier-Declined: Nothing to carry: a spec requirement already forbids it and an existing predicate already enforces it, so no work is pending.
- NOT UNBOUNDED. One retry per zero-work verdict, charged to the frozen budget, so an item that deterministically produces nothing cannot loop (`run_recovery.py:285-287`).
  - Carrier-Declined: Nothing to carry: boundedness is a property this plan DELIVERS rather than defers.

## Scope check

- Over-scope: the two host drivers are declared, which is broader than the single shared file, and only the requeue seam is touched in each. Justified because the requeue must be reached from each host's dispatch loop; the RULE itself is shared, per `7ckptx` R2.6 and R6.1.
- Under-scope: `x7wfyx` item A (the turn budget in the prompt) is deliberately left, so this plan does NOT fully close `x7wfyx`. Set the item `graduated`, not `done`, and do not clear its `Blocks-Release`.
- UNDECLARED PATH THIS PLAN WILL DEFINITELY EDIT, found at review: the gate instructs the executor to set `x7wfyx` `graduated`, and that transition REWRITES AND MOVES the backlog file (measured on a throwaway copy: `open -> graduated`, the file relocates to `.aw/records/backlog/graduated/`, the history message is written, and `- Blocks-Release: next` is correctly preserved). That path appears nowhere in `- Scope-Paths:`, so the finalize scope reconciliation will see an out-of-scope edited path and refuse without a `--scope-reason`. NOTE the sibling `ty7w6o` DOES declare the same item (at its `open/` location), so the Set is internally inconsistent about it. EITHER add the item to this plan's `- Scope-Paths:` (bearing in mind the path CHANGES as a result of the move, which is itself awkward to declare) OR plan to justify it with an explicit `--scope-reason` at finalize; `OQ-05` records the choice rather than guessing, because adding a path to `Scope-Paths` after a `begin` receipt is frozen has its own consequence (`25kzda` 5.5a makes an additive widening a finalize-time accept, not a refusal, so either route is workable and the difference is which record carries the justification).
- Scope fence: the four declared `- Scope-Paths:` plus whatever `OQ-05` settles for the backlog item are the whole intended surface. Do not expand it casually; if the work genuinely requires a file outside the fence, MAKE the edit and JUSTIFY it in the two-way scope reconciliation at finalize. Two files are worth naming because this plan shares them with siblings: `agent_workflows/runner_shared.py` (also declared by `skn8uk`) and `agent_workflows/agy_runipd.py` (also declared by `ty7w6o`); the runner isolates each item in its own lane and merges through the revalidate gate, so overlap is not a hazard, but a gratuitous edit to an unrelated region of either file is.

## Required tests / validation

`python3 -m pytest`, run BARE, with the actual summary pasted into each `V-*`. Cases belong in
`tests/test_turn_bounds.py`, beside the existing incident family. Every case must be built in `tmp_path`;
never read the live `.aw/records/runs/` tree, which is gitignored and absent in CI.

TWO PROPERTIES MATTER MORE THAN THE HAPPY PATH and each has a dedicated `V-*`. FIRST, the predicate must
be UNABLE to fire on a turn that did anything: `V-02` requires a negative control per condition, each
flipped independently. SECOND, the requeue must happen before the cascade observes the terminal status,
or the retry rescues nothing; `V-04` requires an end-to-end multi-item fixture proving the siblings are
NOT blocked, which is the actual user-visible defect.

## Spec / documentation sync

Spec `25kzda` 5.5 (retry policy) is the controlling contract and this plan CONFORMS to it rather than
amending it: the zero-work class fits the existing retryable list ("host nonzero exit that did not create
an ambiguous side effect" and "host spawn failure"), the frozen budget bounds it, and `0` still means no
retry. No `.spec.md` path is declared in `Scope-Paths`, so no spec edit may be made here. Whether 5.5's
retryable list should name this class EXPLICITLY (rather than being read as covered) is `OQ-01`; if the
reviewer wants that, it belongs to a plan that declares the spec file, per the AGENTS.md rule that a plan
amending a spec must declare it.

## Open questions

### OQ-01: Should spec `25kzda` 5.5 name the zero-work class explicitly in its retryable list?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: NON-BLOCKING: 5.5's existing entries already cover a turn that provably created no side effect, which is the cleanest possible member of "did not create an ambiguous side effect", so the implementation is conforming as it stands. Raised because a reader could reasonably read the list as exhaustive of the classes the engine may spend budget on, and an explicit entry would remove the inference. Deliberately not done here: this plan declares no spec file.
- Carrier: s0gnha

### OQ-02: Is the host-truncation signal REQUIRED evidence or merely SUPPORTING?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: DEFERRED TO THE EXECUTOR AS AN IMPLEMENTATION CHOICE, with the obligation (E-03) to decide it, implement one reading, and RECORD the reason in the code. Non-blocking because either reading is defensible and both are safe: the evidence conditions gate the retry in both cases, so the choice only changes how NARROW the retry is, never whether an item with real work can be re-dispatched. The tradeoff, stated so the choice is informed: REQUIRED confines the retry to the one measured cause and lets a future zero-work turn with a different cause block a Set again; SUPPORTING is cause-agnostic and therefore also fires on causes nobody has measured, which is a larger and less predictable surface. The recommendation is SUPPORTING with the truncation recorded in the event, because the predicate's own evidence is what proves nothing was attempted and the host's admission merely explains why - but the executor may choose REQUIRED and record that.
- Carrier-Declined: DISCHARGED BY THIS PLAN'S OWN EXECUTION, not handed off: E-03 REQUIRES the executor to decide the role, implement one reading, and record the reason in the code, and `V-03` requires the recorded rationale be quoted as evidence, so nothing remains outstanding once the plan executes. A SELF-CARRIER WAS REMOVED HERE AT REVIEW (`- Carrier: dy9ymn`) because it would have refused this plan's own finalize: measured by substituting an `executed` status for `dy9ymn` in the live carrier index, the row flipped from legitimate to failing with "carrier dy9ymn resolves only to a terminal/hidden artifact (executed); nothing revisits it", and since this plan's `- Date:` is on or after the carrier cutover `20260919` that finding is `error` severity and is evaluated at the `pre-transition` checkpoint - exactly the checkpoint this plan's gate requires to report conforming. Note the contrast with a sibling's `- Carrier: s0gnha`, which is legitimate: the orchestrator is still pending when a child finalizes, because the runner retires a parent only after every child is `executed`.

### OQ-04: Does this plan's per-item retry counter collide with `xipfy1`, which owns wiring the budget generally?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: NON-BLOCKING because the two can coexist and this plan's counter is the smaller, safer change, but a reviewer should confirm the division rather than discover it later. MEASURED at review: the frozen `--retry-budget` is readable from `state["options"]["retry_budget"]`, and NOTHING reads it - there is no per-item spend accounting anywhere, and `run_recovery.plan_retry` / `retry_budget_remaining` have zero callers outside their module because both require a `RunEngine` over a hash-chained `ledger.jsonl` that no driver run writes. `xipfy1` (`approved`, `Blocks-Release: next`, sharing three of this plan's four `Scope-Paths`) exists precisely to wire that consumption, and its own review escalated a BLOCKER that the ledger substrate is absent, so it may not land as written. THIS PLAN THEREFORE DOES NOT USE `plan_retry`: E-04 counts on the item, mirroring the shipped `integration_attempts` pattern, which needs no ledger and cannot conflict with a later general wiring (a second counter for a different failure class is exactly what `integration_retry_limit` already is, and `runner_shared` treats the two budgets as separate quantities by design). THE RESIDUAL QUESTION for the reviewer: if `xipfy1` later routes all retries through `plan_retry`, should this plan's counter be migrated or left as the zero-work-specific tally? Either is defensible; leaving it is the lower-risk default and needs no action now. Recorded so the two plans' authors do not each assume the other owns the accounting.
- Carrier: 4bhxni

### OQ-05: Should the `x7wfyx` backlog item be added to `- Scope-Paths:`, or justified with `--scope-reason` at finalize?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: NON-BLOCKING because BOTH routes complete successfully and the difference is only which record carries the justification, but the plan must not leave it unstated because as authored it would hit a finalize refusal with no instruction. MEASURED at review: the gate's `graduated` transition rewrites AND MOVES the file (`open` -> `graduated`, verified on a throwaway copy, with the history message written and `- Blocks-Release: next` correctly preserved), and that path is in no `- Scope-Paths:` entry, so the two-way reconciliation sees an out-of-scope edited path. ROUTE A, declare it: honest and visible before execution, but awkward because the path CHANGES as a result of the very edit being declared, so whichever location is written is wrong afterwards. ROUTE B, justify it at finalize with `--scope-reason`: needs no pre-declaration, and spec `25kzda` 5.5a makes an additive widening a finalize-time ACCEPT rather than a never-retryable refusal, so this is a supported path rather than a workaround. The reviewer's default should be ROUTE B for the move itself, because a moving path cannot be declared cleanly. NOTE the Set is currently inconsistent: sibling `ty7w6o` DOES declare the same item at its `open/` location, so if both plans touch it the Set should say so once rather than twice differently.
- Carrier-Declined: A ROUTING CHOICE WITH NO RESIDUAL WORK EITHER WAY: both routes are supported and complete, the Scope check section now states the consequence and names the default, so an executor cannot hit the refusal uninstructed. Nothing is owed to a future artifact; if the reviewer prefers route A, it is a one-line edit to this plan before approval.

### OQ-03: Should a refused verdict be reported even when nothing is retried?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: YES, and E-05 requires it. A predicate this strict will refuse in cases a human believes it should have fired, and the only way to tell "too strict" from "correctly cautious" is to see which condition failed. Reporting the refusal reason is cheap, cannot mislead (it asserts nothing about what was attempted, only about what could be proven), and is the difference between a predicate that can be tuned on evidence and one that can only be argued about.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted `pytest` output showing the verdict is POSITIVE for a reconstruction of the measured case (no outcome file, `starting_head == ending_head`, zero lane commits, clean `ending_status`) and that the returned verdict carries its reason and the facts it read. Plus a case per missing input (absent `ending_status`, unreadable lane, absent attempt record) showing the verdict is "cannot prove" and NOT a retry, demonstrating fail-closed behavior.
  - Observed evidence: |
      All commands run BARE except where per-test counts were needed, in which case the configured
      defaults were cleared explicitly with `-o addopts=""` (never by fighting individual flags).
      NOTE ON THE ENVIRONMENT: this lane's own shell exports `OPENCODE_CONFIG_CONTENT`, which an
      unrelated PRE-EXISTING assertion in this same file reads
      (`TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`,
      asserting a non-isolated turn carries NO denial policy). That test fails on THIS MACHINE at
      HEAD with or without this change, so every run below is `env -u OPENCODE_CONFIG_CONTENT`, which
      is the clean-environment condition CI runs in. Reported as a finding rather than worked around
      silently.

      POSITIVE: the measured shape is recognized, with its reason and facts.

          $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py \
              -o addopts="" -q -k "TestTheZeroWorkVerdictIsEvidenceBased"
          ..........                                                               [100%]
          10 passed, 134 deselected in 0.25s

      The ten cases are: the reconstruction of `zqs0px`'s shape (no outcome file, `starting_head ==
      ending_head == 7c233993`, zero lane commits, clean tree) verdict POSITIVE carrying
      `facts == {'disposition': 'partial', 'isolated': True, 'outcome_written': False,
      'host_truncation': False, 'lane_state': 'EMPTY', 'lane_commits_ahead': 0,
      'lane_dirty': False, 'lane_branch': 'aw/lane/zqs0px'}`; and FIVE fail-closed cases, each
      asserting `(attempted_nothing, proven) == (False, False)` and a reason containing
      `FAIL-CLOSED`: an unreadable lane reading, an ABSENT lane for an isolated turn, an
      unanswerable outcome question (`outcome_written=None`), a shared-tree attempt missing
      `ending_status`, a shared-tree attempt missing `ending_head`, and a lane whose `commits_ahead`
      is not an integer. Plus the purity assertion (the body calls no `run_checked`/`describe_lane`/
      `open`/`read_text`/`is_file` and names no `subprocess`), the mode documentation assertion, and
      the assertion that `holds_work` is NAMED as a refusal but never READ as the commit test.

      Verdict text as produced (pasted verbatim from an interpreter run of the shipped predicate):

          the turn PROVABLY attempted nothing: it wrote no outcome file and its lane holds no commit
          beyond its base and its tree is clean; no host-truncation record accompanied it, which does
          not weaken the verdict because the evidence conditions are what prove it (the truncation
          signal is SUPPORTING)
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted output of FOUR negative controls, each flipping ONE condition of the conjunction independently and each showing NO retry: an outcome file exists; `ending_head != starting_head`; the lane holds a commit; the tree is dirty.
    STATE THE MODE FOR EACH CONTROL, because two of them cannot fail in the mode the defect was measured in. Per E-01's measurement, on an ISOLATED turn `ending_head` and `ending_status` read the MAIN checkout and so are fixed regardless of what the lane did; the `ending_head != starting_head` and `dirty tree` controls are therefore only meaningful for a SHARED-TREE (`--no-isolate-worktree`) fixture, while the `outcome file exists` and `lane holds a commit` controls are the ones that bite on an isolated fixture. Build each control in the mode where it can actually fail and SAY WHICH, rather than asserting four controls in one mode where two are vacuously satisfied. A control that cannot fail is not a control, and presenting one as passing would misreport the predicate's strictness.
    Plus a refusal case per protected class: stopped, forced/indeterminate, `merge-retry`, `dependency-blocked`, `not-attempted`, and a `review` action. NOTE, established at review, that most of these are DEFENCE IN DEPTH rather than live paths: the zero-work branch is entered only for an item whose disposition is the terminal `partial`, and a stopped item carries `interrupted`, a forced one `unknown_outcome`, a deferred one `merge-retry`, and an unrun one `dependency-blocked`/`not-attempted` - none of which is `partial` - while a `review` turn's scorer returns `reviewed`/`approved`/`failed-safely` and never `partial`. Keep every refusal (a future change to the disposition vocabulary would make them live) but do not describe them as the property that makes this change safe; the evidence conjunction is that property. Plus evidence that the existing refusal predicates are REUSED rather than restated (name them: `runner_stop.is_indeterminate`, and the same gate `requeue_interrupted` applies).
  - Observed evidence: |
          $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py \
              -o addopts="" -q -k "TestTheNegativeControls"
          ................                                                         [100%]
          16 passed, 128 deselected in 0.30s

      THE FOUR CONTROLS, EACH IN THE MODE WHERE IT CAN ACTUALLY FAIL, and the mode is in each test
      name and docstring rather than left to a reader:

        1. `outcome file exists`  -> ISOLATED mode
           (`test_an_outcome_file_refuses_the_verdict_isolated_mode`); refusal reason contains
           `outcome file WAS written`.
        2. `the lane holds a commit` -> ISOLATED mode
           (`test_a_lane_commit_refuses_the_verdict_isolated_mode`); reason contains `3 commit(s)`.
        3. `ending_head != starting_head` -> SHARED-TREE mode
           (`test_a_moved_head_refuses_the_verdict_SHARED_TREE_mode`); reason contains `HEAD MOVED`.
        4. `dirty tree` -> SHARED-TREE mode
           (`test_a_dirty_shared_tree_refuses_the_verdict_SHARED_TREE_mode`); reason contains
           `DIRTY`. A fifth control, a DIRTY LANE, covers condition 4 in isolated mode.

      AND THE VACUITY CLAIM IS ITSELF ASSERTED rather than merely asserted in prose:
      `test_the_isolated_fixture_really_is_vacuous_for_those_two_conditions` builds an ISOLATED
      attempt whose lane holds FIVE commits, shows `starting_head == ending_head` and
      `ending_status == ""` are STILL both true (they read the MAIN checkout), and shows the verdict
      is refused on the LANE's commits. That is the measurement behind the mode split: a control
      flipping those two fields on an isolated fixture cannot fail, and presenting it as passing
      would misreport the predicate's strictness.

      REFUSAL PER PROTECTED CLASS: `interrupted`, `unknown_outcome`, `dependency-blocked`,
      `not-attempted` and `merge-retry` are parametrized in
      `test_every_protected_disposition_is_refused` (5 cases, each `proven=True`,
      `attempted_nothing=False`); plus `test_a_review_action_is_refused` (reason contains `REVIEW`),
      `test_a_deliberately_stopped_item_is_refused` (reason contains `DELIBERATE OPERATOR STOP`),
      and `test_an_indeterminate_item_is_refused_through_the_EXISTING_predicate`.

      THE EXISTING PREDICATES ARE REUSED, NOT RESTATED, and that is asserted mechanically rather
      than by reading: the indeterminate test PATCHES `runner_stop.is_indeterminate` and asserts
      `gate.called`, so the refusal genuinely routes through the same predicate `requeue_interrupted`
      applies (`oc_runipd.py` gates `--retry-incomplete` on it for the stated reason that "the two
      routes cannot disagree"). `test_the_merge_retry_refusal_uses_the_CONSTANT_not_a_bare_string`
      asserts the `merge-retry` refusal reads `INTEGRATION_DEFERRED_STATUS` rather than a literal.

      AND THE UNREACHABILITY IS RECORDED IN THE CODE so a later reader does not mistake defence in
      depth for the live guard: `test_the_unreachable_refusals_are_RECORDED_as_such` asserts the
      section header carries `DEFENCE IN DEPTH` and `EVIDENCE CONJUNCTION`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted output for both a zero-work turn WITH `attempt["host_truncation"]` and one WITHOUT, showing behavior consistent with the chosen reading; plus a case proving a truncation record ALONE (with work evidence present) does NOT authorize a retry. Quote the recorded rationale from the code showing the choice and its reason are documented.
  - Observed evidence: |
          $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py \
              -o addopts="" -q -k "TestTheHostTruncationSignalIsSupportingNotRequired"
          ....                                                                     [100%]
          4 passed, 140 deselected in 0.23s

      THE CHOICE IS **SUPPORTING**, NOT REQUIRED (OQ-02 discharged), and all three demanded cases
      pass:

        * WITHOUT a truncation record the verdict STILL FIRES
          (`test_a_zero_work_turn_WITHOUT_a_truncation_record_still_fires`): `attempted_nothing=True`,
          `truncated=False`, reason contains `SUPPORTING`.
        * WITH `attempt["host_truncation"]` it fires and SAYS SO
          (`test_a_zero_work_turn_WITH_a_truncation_record_fires_and_says_so`): `truncated=True`,
          reason contains `HOST ITSELF admitted`.
        * A TRUNCATION RECORD ALONE DOES NOT AUTHORIZE A RETRY
          (`test_a_truncation_record_ALONE_does_NOT_authorize_a_retry`): with
          `host_truncation` present AND `commits_ahead=1`, `attempted_nothing=False` while
          `truncated` is still True, proving the record is READ but is not sufficient.

      THE RECORDED RATIONALE, quoted from `runner_shared.turn_attempted_nothing`'s docstring (which
      `test_the_choice_and_its_reason_are_RECORDED_in_the_code` asserts on):

          THE HOST-TRUNCATION SIGNAL IS **SUPPORTING**, NOT REQUIRED (`dy9ymn` OQ-02, decided here).
          WHY: the four evidence conditions are what PROVE nothing was attempted; the host's
          admission merely explains WHY, so requiring it would confine the retry to the one measured
          cause and let a future zero-work turn with a different cause block a Set again. The cost of
          this choice, stated so it is not discovered later: the predicate is CAUSE-AGNOSTIC and so
          also fires on causes nobody has measured. That is judged acceptable precisely because the
          conjunction, not the cause, is the safety property. A truncation record therefore NEVER
          authorizes a retry by itself - a host may truncate a turn that had already done real work,
          and such a turn fails condition 1, 3 or 4.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted output of an END-TO-END multi-item fixture: a zero-work item plus a dependent plus an orchestrator, showing the item is re-dispatched and the SIBLINGS ARE NOT `dependency-blocked` - this is the actual user-visible defect and a unit test on the predicate alone does not prove it. The fixture must exercise a turn that happens DURING the run, not a resumed one, since that is the case E-06 exists to make reachable. Plus the ordering property asserted directly (the requeue precedes the cascade's observation of the terminal status), and an assertion that the requeue site is inside the dispatch loop rather than in the pre-loop `--retry-incomplete` block.
    Plus budget behavior on all three points: `--retry-budget 0` gives immediate `partial` with no retry; budget available gives exactly ONE retry; budget exhausted gives `partial`. EACH OF THESE REQUIRES THE PER-ITEM COUNTER E-04 ADDS, so paste the counter's value alongside each outcome (as `integration_attempts` is observable today) rather than inferring the budget was respected from the final status alone: a retry that fired once because the code hardcoded one attempt, and a retry that fired once because the budget allowed one, are indistinguishable from the status and only the former breaks at `--retry-budget 3`. Also paste a case at a budget ABOVE one, showing the second and subsequent retries are still bounded by the frozen value and that the counter persists across a resume. Plus confirmation that no new retry knob was added (the frozen `--retry-budget` remains the only limit) and that `plan_retry` was NOT called (it requires a `RunEngine` over a `ledger.jsonl` no driver run writes).
  - Observed evidence: |
          $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py \
              -o addopts="" -q \
              -k "TestTheZeroWorkRetryIsBoundedByTheFrozenBudget or TestTheSiblingsAreNotBlockedEndToEnd"
          ......................                                                   [100%]
          22 passed, 122 deselected in 1.76s

      THE END-TO-END MULTI-ITEM FIXTURE (`TestTheSiblingsAreNotBlockedEndToEnd`) drives each host's
      REAL `run_queue` over a real `git init` repo with THREE members: the zero-work item `zqs0px`, a
      DEPENDENT `qmgn12` declaring `executed:zqs0px`, and an ORCHESTRATOR `s0gnha`. Only
      `execute_item` is stubbed; nothing about the loop, the cascade, the dependency resolver or the
      orchestrator performer is mocked, and `retry_incomplete=False` throughout so nothing here can
      be satisfied by the pre-loop requeue block.

      THE USER-VISIBLE DEFECT IS FIXED, on BOTH hosts
      (`test_the_zero_work_item_is_re_dispatched_and_its_dependent_still_executes`):
      `turns == ["zqs0px", "zqs0px", "qmgn12"]`, statuses `zqs0px=executed` and `qmgn12=executed`,
      and ZERO `dependency-blocked` events. The item's counter reads
      `zero_work_retries == 1` and exactly ONE `zero-work-retry` event was emitted.

      AND THE FIXTURE GENUINELY REACHES THE CASCADE, which is what makes the above meaningful rather
      than tautological (`test_without_the_fix_the_cascade_would_fire_which_is_what_this_prevents`):
      with the shared seam neutralized, `turns == ["zqs0px"]`, `zqs0px=partial`,
      `qmgn12=dependency-blocked`, a `dependency-blocked` event naming `qmgn12`, and a nonzero exit.
      That is the MEASURED 2026-09-18 shape reproduced, then shown repaired.

      TWO HONEST LIMITS OF THIS FIXTURE, stated rather than papered over. (1) The ORCHESTRATOR is
      still TERMINATED, for a FIXTURE-LOCAL reason and NOT the cascade: the synthetic repo holds no
      orchestrator plan, so Set membership cannot be resolved and `dispatch_orchestrator_item`
      terminates with `reason == "no-orchestrator"` and `unfinished_children == []`. Both facts are
      ASSERTED, so the parent is provably not refused because of the zero-work child. (2) Exit code 0
      is consequently NOT asserted on the happy case, because the fixture cannot earn it for reasons
      unrelated to this plan; the budget cases below DO assert nonzero. (3) The end-to-end mode is
      SHARED-TREE with no mock of the evidence collector; the isolated-lane reading is unit-covered
      above.

      THE RETRY IS DISPATCHED IN RECOVERY MODE (`test_the_retry_is_dispatched_in_RECOVERY_mode`):
      the item's two attempt records read `[recovery=False, recovery=True]`, i.e. the ESTABLISHED
      `queued` + `recovery_next` pattern reaches the dispatch as the `recovery=` keyword.

      BUDGET BEHAVIOR ON ALL FOUR POINTS, WITH THE COUNTER'S VALUE PASTED RATHER THAN INFERRED:

        * `--retry-budget 0` -> `turns == ["zqs0px"]`, status `partial`, ZERO `zero-work-retry`
          events, stderr contains `budget is exhausted`, exit nonzero
          (`test_budget_zero_gives_no_retry_at_all_end_to_end`).
        * budget 2, transient zero-work -> exactly ONE retry, `zero_work_retries == 1` (above).
        * budget 2, PERMANENTLY zero-work -> `turns == ["zqs0px"] * 3` (budget + 1 dispatches, never
          more), final `partial`, `zero_work_retries == 2`, TWO `zero-work-retry` events, and
          `zero_work_refusal["exhausted"] is True`
          (`test_a_permanently_zero_work_item_cannot_loop_past_the_budget`).
        * budget 3 -> `turns == ["zqs0px"] * 4` and `zero_work_retries == 3`
          (`test_a_budget_above_one_bounds_the_same_way`). This is the case that distinguishes "the
          code hardcoded one attempt" from "the budget allowed one": a hardcoded single retry fails
          here.

      THE COUNTER PERSISTS ACROSS A RESUME (`test_the_counter_PERSISTS_across_a_resume`): the spend
      is written into `state.json` on the ITEM, re-read from disk as `2`, and
      `zero_work_retry_decision` on the re-read state returns `(retry=False, exhausted=True)` with
      `attempts == 2`, so a resume buys no fresh retries.

      THE UNIT MATRIX over the pure decision (`TestTheZeroWorkRetryIsBoundedByTheFrozenBudget`):
      budget 0 -> exhausted immediately; budget 1 -> exactly one then exhausted; budget 3 ->
      retries at used=0,1,2 then exhausted at 3; a REFUSED verdict never retries even at budget 10.

      NO NEW KNOB AND NO `plan_retry`, both asserted mechanically:
      `test_no_new_retry_knob_was_added` greps this plan's own section of `runner_shared.py` for
      `add_argument`/`zero_work_budget`/`zero-work-budget` and finds none, so the frozen
      `--retry-budget` remains the only limit; `test_plan_retry_is_NOT_called` asserts neither
      `zero_work_retry_decision` nor `handle_zero_work_retry` mentions `plan_retry` (it needs a
      `RunEngine` over a `ledger.jsonl` no driver run writes).
      `test_the_frozen_budget_is_READ_and_never_re_resolved` asserts the decision reads
      `frozen_retry_budget` and never `resolve_retry_budget`, and
      `test_the_counter_is_SEPARATE_from_the_other_two_budgets` asserts the three per-item counter
      keys are distinct (spec 5.5 counts corrections separately per action).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted output showing one `zero-work-retry` event per retry carrying the reason, the facts, the remaining budget and the truncation flag; ZERO such events on every refusal path; and the refusal reason present in the run report for an item that ended `partial` unretried. Plus the full bare `python3 -m pytest` summary line for the whole plan, and confirmation that the pre-existing tests in `tests/test_turn_bounds.py` (including the three FOREGROUND assertions at `:875-931` and the source-grep at `:357-368`, both verified accurate at review) still pass unweakened.
  - Observed evidence: |
          $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py \
              -o addopts="" -q -k "TestTheZeroWorkRetryIsAuditable"
          .......                                                                  [100%]
          7 passed, 137 deselected in 0.25s

      ONE EVENT PER RETRY, CARRYING EVERYTHING DEMANDED
      (`test_a_retry_emits_exactly_one_event_carrying_the_facts_and_the_budget`): exactly one
      `zero-work-retry` event, with `id6`, `attempt == 1`, `from_status == "partial"`, a `reason`
      containing `PROVABLY attempted nothing`, the `facts` it read
      (`facts["lane_commits_ahead"] == 0`), `retry_attempts_used == 1`, `retry_budget == 2`,
      `budget_remaining == 1`, and `host_truncation == False`. The item afterwards carries
      `zero_work_retries == 1`, `status == "queued"`, `recovery_next is True`,
      `requeue_from_status == "partial"`.

      THE PRINTED LINE, captured from stderr during that test:

            -> IPD zqs0px provably attempted nothing (no outcome, no commit, clean tree);
               re-dispatching instead of blocking its Set (zero-work retry 1 of 2)

      ZERO EVENTS ON EVERY REFUSAL PATH:
      `test_a_REFUSAL_emits_no_event_and_changes_no_status` (lane holds 2 commits) -> no
      `zero-work-retry` event, `status` still `partial`, no counter written, and the refusal RECORD
      present with `attempted_nothing=False` and a reason containing `2 commit(s)`.
      `test_an_item_that_did_not_end_partial_is_untouched` -> NO events at all and no refusal record.
      `test_the_exhausted_case_stands_terminal_and_records_a_refusal` (budget 0) -> no event, and
      `zero_work_refusal["exhausted"] is True` with a reason containing `budget is exhausted`.
      So the event's presence means "a turn was re-dispatched because it provably did nothing" and
      never "the check ran".

      THE REFUSAL REASON REACHES THE RUN REPORT (`test_the_report_names_BOTH_a_retry_and_a_refusal`):
      `render_zero_work_notes` emits a `## Zero-work turns (attempted nothing)` section containing
      `aaa111` RE-DISPATCHED (zero-work retry 1 of 2)` and
      `bbb222` not retried (status `partial`)` with the condition that failed. The section is ABSENT
      when nothing happened (`test_the_report_section_is_absent_when_nothing_happened` -> `[]`), so
      an unaffected run's report is byte-identical, and
      `test_the_renderer_is_reached_from_the_SHARED_report_writer` asserts the shared
      `write_report` actually calls it (so both hosts' reports carry it, and neither carries a copy).

      THE PRE-EXISTING TESTS IN THIS FILE STILL PASS UNWEAKENED. The whole file:

          $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py \
              -o addopts="" -q
          ........................................................................ [ 50%]
          ........................................................................ [100%]
          144 passed in 7.77s

      The three FOREGROUND assertions and the source-grep the plan names are inside that 144 and were
      NOT edited: the only edits to this file are two added imports (`contextlib`, `io`) and appended
      classes. THE FULL BARE SUITE:

          $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest
          9025 passed, 3 skipped, 2 xfailed, 6 warnings in 286.75s (0:04:46)

      Plus the highest-risk pinned invariants run together (the call-site census, the cross-host
      run_queue characterization, the sibling retry-consumption suite, the re-fork guard, and the
      defect-report family that pins `partial` as terminal):

          $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_runner_shared.py \
              tests/test_rununify_run_queue.py tests/test_retry_consumption.py \
              tests/test_runner_refork_guard.py tests/test_defect_report.py -o addopts="" -q
          431 passed in 114.25s (0:01:54)
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: pasted evidence that the requeue call site is INSIDE the dispatch loop on BOTH hosts, after `execute_item` returns - asserted on the call graph or by locating the site relative to `while True:` and to the `cascade_dependency_blocked` call, NOT by a byte offset. Must explicitly demonstrate the property the original wording would have lost: a zero-work turn occurring DURING a run (not a resumed one) is re-dispatched. State the measured relationship that makes this necessary: the `--retry-incomplete` block the plan originally cited runs BEFORE the loop and inspects statuses left by a previous invocation, so a check placed there never observes an in-run turn. Also paste the negative control proving the test can fail: with the call moved into the pre-loop block, the in-run fixture is NOT retried (name the assertion that fires).
  - Observed evidence: |
          $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py \
              -o addopts="" -q -k "TestTheRequeueFiresFromInsideTheDispatchLoop"
          .........                                                                [100%]
          9 passed, 135 deselected in 0.26s

      THE CALL SITE IS ASSERTED ON STRUCTURE, NEVER ON A BYTE OFFSET, and on BOTH hosts (each test is
      parametrized over `oc_runipd` and `agy_runipd` through the file's existing `DRIVERS` mark):

        * `test_the_call_is_inside_the_dispatch_loop` parses `run_queue`, collects every `ast.Call`
          reachable from its `ast.While` nodes, and asserts the single
          `handle_zero_work_retry` call is in that set.
        * `test_the_call_follows_execute_item_in_the_same_try_statement` locates the `ast.Try` whose
          BODY calls `execute_item` and asserts `handle_zero_work_retry` is on that statement's
          `orelse`, so it runs when and only when the turn RETURNED (never after a deliberate stop,
          an interrupt, or a `DriverError`, each of which breaks or re-raises).
        * `test_the_call_precedes_the_cascade_on_the_next_iteration` asserts
          `cascade_dependency_blocked` appears BEFORE the seam in `run_queue`'s source, i.e. the
          cascade is at the TOP of the loop and first observes this turn's terminal status on the
          NEXT iteration, so the seam sits inside the window.
        * `test_the_rule_is_not_reimplemented_per_host` asserts neither driver defines
          `turn_attempted_nothing`, `zero_work_retry_decision` or `handle_zero_work_retry`.

      THE IN-RUN PROPERTY (not a resumed one) is demonstrated by V-04's end-to-end fixture, which
      runs with `retry_incomplete=False` and still produces
      `turns == ["zqs0px", "zqs0px", "qmgn12"]`.

      THE MEASURED RELATIONSHIP THAT MAKES THIS NECESSARY, re-verified at execution: the
      `--retry-incomplete` block is at function-relative lines 36-78 of `run_queue` while
      `while True:` is at function-relative 152 and the `execute_item` call at 340. The block is
      therefore a resume-time, run-once pass over statuses left by a PREVIOUS invocation and can
      never observe an in-run turn. `test_the_reason_the_pre_loop_block_is_wrong_is_RECORDED` asserts
      that reason is written at `handle_zero_work_retry` so nobody "tidies" the seam into the block
      whose SHAPE it copies.

      THE NEGATIVE CONTROL, RUN RATHER THAN ARGUED. The in-loop seam was DELETED from
      `agent_workflows/oc_runipd.py` and an equivalent call injected into the pre-loop
      `--retry-incomplete` block instead (a scratch copy of the file was kept and restored
      afterwards; the restore was confirmed by re-running the file green at 144 passed):

          $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py \
              -o addopts="" -q -k "oc_runipd and (TestTheRequeueFiresFromInsideTheDispatchLoop \
              or TestTheSiblingsAreNotBlockedEndToEnd)"
          8 failed, 3 passed, 133 deselected in 1.10s

          FAILED ...TestTheRequeueFiresFromInsideTheDispatchLoop::test_the_call_is_inside_the_dispatch_loop[oc_runipd]
          FAILED ...TestTheRequeueFiresFromInsideTheDispatchLoop::test_the_call_precedes_the_cascade_on_the_next_iteration[oc_runipd]
          FAILED ...TestTheRequeueFiresFromInsideTheDispatchLoop::test_the_call_follows_execute_item_in_the_same_try_statement[oc_runipd]
          FAILED ...TestTheSiblingsAreNotBlockedEndToEnd::test_a_permanently_zero_work_item_cannot_loop_past_the_budget[oc_runipd]
          FAILED ...TestTheSiblingsAreNotBlockedEndToEnd::test_a_budget_above_one_bounds_the_same_way[oc_runipd]
          FAILED ...TestTheSiblingsAreNotBlockedEndToEnd::test_budget_zero_gives_no_retry_at_all_end_to_end[oc_runipd]
          FAILED ...TestTheSiblingsAreNotBlockedEndToEnd::test_the_zero_work_item_is_re_dispatched_and_its_dependent_still_executes[oc_runipd]
          FAILED ...TestTheSiblingsAreNotBlockedEndToEnd::test_the_retry_is_dispatched_in_RECOVERY_mode[oc_runipd]

      THE ASSERTION THAT FIRES on the in-run fixture, named as required, is in
      `test_the_retry_is_dispatched_in_RECOVERY_mode`:

          >       assert [a["recovery"] for a in item["attempts"]] == [False, True]
          E       assert [False] == [False, True]
          E         Right contains one more item: True

      i.e. with the call in the pre-loop block the in-run zero-work turn is NOT retried at all, which
      is exactly the property the original wording would have lost.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is release-blocking (`Blocks-Release: next`, inherited from backlog `x7wfyx`) and must not be
executed before explicit human approval, which `- Status:` records and which no agent may write on the
maintainer's behalf.

IT DECLARES `executed:ty7w6o` and must not be executed before that plan is `executed`, because it
consumes the `attempt["host_truncation"]` record `ty7w6o` produces.

EXECUTION CONTRACT. Commit only the files this plan changed, path-scoped (`git commit -m msg -- <path>`),
never `git add -A`/`-a`/bare, and never push. Before every commit run `git diff --cached --name-only` and
`git restore --staged` anything not yours: this is a SHARED CHECKOUT with concurrent workers, and a
failed pre-commit hook can leave paths in the index you never staged, so re-verify after any failed
attempt. Prefer `aw commit <plan> -- <paths>`.

When reporting tests passed, paste the ACTUAL bare `python3 -m pytest` output. Do not add `-n0`, a second
`-q`, or `-p no:randomly`.

ON CLOSING `x7wfyx`: set it `graduated`, NOT `done`. This plan implements its item B only; item A (the
turn budget in the prompt) remains, and the item carries `Blocks-Release: next`, so a `done` would trip
the close-legitimacy gate. Do not clear its release gate.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` reports conforming and every `V-*` carries concrete pasted evidence.
This plan SPENDS MONEY when it fires, so a `V-*` marked without observed output would authorize unbounded
unaudited spend.
