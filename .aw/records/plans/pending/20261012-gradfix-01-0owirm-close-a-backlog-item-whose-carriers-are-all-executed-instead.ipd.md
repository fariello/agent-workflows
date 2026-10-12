# IPD: Close a backlog item whose carriers are all executed instead of re-graduating it

- Date: 2026-10-12
- Kind: child
- Concern: Eight of the ten fail-gate items in the 2026-10-12 runs were backlog items whose work was ALREADY DONE: every plan linked to them by `- From-Backlog:` was `executed`, yet the item sat at `open`, so the runner queued it for a fresh graduation turn. The agent correctly saw there was nothing left to plan and wrote no plan, and the graduation count check (`production_checks.backlog_graduate_count`) then failed the item with "produced 0 linked IPDs". So a correct agent was failed for not duplicating finished work, and the item can never reach `done` on its own.
- Scope: (1) Before dispatching a backlog item for graduation, if it has at least one `From-Backlog` carrier and every carrier is terminal-and-done (`executed`, or for a spec carrier `implemented`), do not spend an agent turn: close the item `done` citing the executed carrier, through the existing release-gate close predicate. (2) Make `backlog_graduate_count` accept a production turn that wrote no plan when every existing carrier is already executed, reporting it as "already complete" instead of a failure. (3) Close the eight stranded items found today. No change to how a live, unfinished item graduates.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/production_checks.py, tests/test_backlog_already_complete.py, .aw/records/backlog
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- Set: gradfix
- Order: 1
- Highest E allocated: 05
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us
- Id: 0owirm

## Workflow history
- 2026-10-12 to-review (aw set): authored to fix the 2026-10-12 fail-gate cluster (Set gradfix)

- 2026-10-12 draft (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A backlog item whose linked plans have all executed is closed `done` automatically and never queued for re-graduation, so the runner stops failing correct agents for declining to duplicate finished work.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: reproduce and add the predicate

- [ ] E-01 REPRODUCE on real records before changing code. For each of `ariaau`, `ildjse`, `mflqqf`, `7yz545`, `s8veyk`, `oq05nc`, `vy20et`, `h0tiaw`, list its `From-Backlog` carriers with their directory, and call `production_checks.backlog_graduate_count(repo, <id6>, <all current plan ids>)`. Expected: every carrier is under `executed/`, and every call returns `BACKLOG-GRADUATE-COUNT ... produced 0 linked IPDs`. Paste the table. If any carrier is not executed, STOP: that item is not this defect.
  - Depends on: none
  - Expected outcome: a pasted table showing all carriers executed and the check failing for each.
  - Execution state: pending

- [ ] E-02 Add one predicate, `runner_shared.backlog_item_already_complete(repo, item_id6)`, returning a typed result: COMPLETE (at least one `From-Backlog` carrier, every carrier `executed` or `implemented`, citing the carrier to use as close evidence), NOT-COMPLETE (with the unfinished carriers), or NO-CARRIERS. It reads carriers the same way the close path already does (`check_engine` carrier scan used by `evaluate_backlog_close`), so it cannot disagree with the closer. A carrier under `superseded/` or `not-executed/` does not count as done, and if every carrier is retired, the result is NOT-COMPLETE: deciding that work is abandoned is a human act.
  - Depends on: E-01
  - Expected outcome: a pure-with-respect-to-git function returning COMPLETE for all eight items from E-01, and NOT-COMPLETE for an item with one pending carrier.
  - Execution state: pending

### Task group 2: stop the wasted turn and the false failure

- [ ] E-03 Close instead of dispatch. Where the runner dispatches a backlog item with action `plan` (`execute_item_core`'s backlog-production path), call E-02 first. On COMPLETE: close the item `done` through `close_backlog_item` with the cited carrier as evidence (so `check_engine.evaluate_blocking_close` still governs any `Blocks-Release` item), record an `backlog-already-complete` event naming the carriers, set the queue item `executed` with reason "already complete", and spend no agent turn. If the close itself refuses (for example a release gate the evidence does not satisfy), the item ends `needs-input` with that refusal, not `fail-gate`, because a human decision is what is missing.
  - Depends on: E-02
  - Expected outcome: a backlog item whose carriers are all executed is closed with no agent session started.
  - Execution state: pending

- [ ] E-04 Make the count check tell "already done" from "failed to plan". In `backlog_graduate_count`, when no linked plan is active and no new plan was produced, but `backlog_item_already_complete` is COMPLETE, return no finding. Keep the existing refusals for every other case: an item with no carriers at all that produced nothing still fails, and an unlinked new plan still fails. This is the safety net for an item that reaches the check by another path (for example a pre-existing queue built before E-03 shipped).
  - Depends on: E-02
  - Expected outcome: the check passes for the eight items from E-01 and still refuses a genuinely empty graduation.
  - Execution state: pending

### Task group 3: prove, and clear today's stranded items

- [ ] E-05 Add `tests/test_backlog_already_complete.py`, driving real fixture repos and the real runner path (scripted host, as `tests/test_oc_runipd.py` does), asserting on queue status, events, the backlog file's directory and the absence of a spawned agent, never on source text. Cases: (a) all carriers executed: item closed `done`, no agent spawned, event recorded; (b) one carrier pending: item dispatched for graduation as today; (c) all carriers retired: item NOT closed, dispatched or left for a human; (d) `Blocks-Release` item whose carrier is executed with the same gate: closed through the existing predicate; (e) `backlog_graduate_count` returns no finding for (a) and still refuses an item with zero carriers that produced nothing. Cases (a) and (e) must FAIL on the base commit; show it. Then close the eight stranded items with `aw backlog set done <id6> --evidence <executed carrier path>`, paste each result, run the bare suite, and paste its summary line.
  - Depends on: E-03, E-04
  - Expected outcome: the new module passes, (a) and (e) shown failing before the change, eight items now under `backlog/done/`, bare suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Suite BARE as `python3 -m pytest`; narrowed runs `-o addopts=""`. Tests drive surfaces, never read source (P16).
- Commit through `aw commit <plan> -- <paths>`; never push.
- Release-gated closes go through `check_engine.evaluate_blocking_close`; never write `done` around it.
- Cite code by SYMBOL.

## Findings

| ID | Finding | Evidence |
|----|---------|----------|
| F-01 | Eight fail-gate items are backlog items with every carrier executed. | `ariaau`->`qtz0us,bec7ee,38pxaz,dmjp0u`; `ildjse`->`i18yaz,32jpl1,eow7p4`; `mflqqf`->`u57rfv,gqyold,d0lg63`; `7yz545`->`1u4olp,czut8j,ov2c9n,r5fk4k`; `s8veyk`->`4qv834,bqtgmo,y9m1ya`; `oq05nc`->`l4vw9o,x2dwu5,pi3bk8,wzhe4n`; `vy20et`->`9wzlou,jjh4aj,rtvdak`; `h0tiaw`->`l8wvv3,dq9bj9,9i2hge`. All under `plans/executed/` (measured 2026-10-12). |
| F-02 | They were set back to `open` on purpose, then never re-closed. | Commit `02bfc7618` (plan `52opph`, 2026-10-06) reopened 13 items with "returned to authoring ... re-run graduation to complete the handoff" when their orchestrators failed a coverage check. The orchestrators were later repaired and executed (2026-10-07..09), but the items stayed `open`. |
| F-03 | The runner's close never fired for them. | `runner_shared.evaluate_backlog_close` closes only when THIS run executed a carrier ("this run executed none of its carriers, so the close was not earned"). Orchestrator retirement does not call `process_backlog_close` at all (`dispatch_orchestrator_item` sets `executed` and returns), and run summaries recorded "IPD 1u4olp ended executed, so the close was never evaluated". |
| F-04 | `open` maps to `plan` with no carrier check. | `run_selection_policy._BACKLOG_ACTIONS["open"] = ACTION_PLAN`. |
| F-05 | The agent behaved correctly; the check failed it. | Agent transcripts: "The whole malgate Set ... appears already executed", "All three carriers are already executed", "already exists and is executed ... rather than author duplicates". `backlog_graduate_count` returns "produced 0 linked IPDs" whenever no carrier is ACTIVE, and `existing_handoff_plans` excludes executed plans. |

## Proposed changes (ordered, validatable)

1. One "already complete" predicate (E-02).
2. Close instead of dispatch (E-03).
3. Count check accepts already-complete items (E-04).
4. Tests, clear today's items, bare suite (E-05).

## Deferred / out of scope (with reason)

- Teaching orchestrator retirement to close its source backlog item: Order 01 of this Set closes the gap at dispatch time, which covers every route an item can be stranded by (reopen, retirement, a lost close). Adding a second close site is unnecessary once the dispatch-time check exists.
- Changing what `52opph` did: it is executed history.

## Scope check

- Over-scope: none.
- Under-scope: none known.

## Required tests / validation

- `tests/test_backlog_already_complete.py` (new), with (a) and (e) shown failing on the base commit.
- Bare suite `python3 -m pytest`.
- The eight items closed, each `aw backlog set` output pasted.

## Spec / documentation sync

N/A: no spec states that an `open` item with executed carriers must be re-graduated; spec `25kzda` 3.4 describes graduation of unfinished items. The new event name is documented in the runner's event list where `backlog-item-closed` is.

## Open questions

### OQ-01: Should an item whose carriers are all RETIRED be closed automatically too?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: No. A retired carrier means someone decided not to do that work; whether the backlog item is therefore finished or still needs a different plan is a human judgement. E-02 returns NOT-COMPLETE for that case and E-05 (c) pins it. Reversible.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the pasted carrier table and the eight failing check results.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the predicate's output for the eight items (COMPLETE) and for a fixture with one pending carrier (NOT-COMPLETE), and for all-retired (NOT-COMPLETE).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: E-05 (a) and (d) passing, showing the event, the closed file location and no agent spawn (produced by the runner's backlog dispatch path through the scripted host).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: E-05 (e) passing, both halves.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the new module passing, (a) and (e) failing on the base commit, the eight `aw backlog set done` outputs, and the bare-suite summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval. Commit only Scope-Paths files through `aw commit 0owirm -- <paths>`; never push. Paste actual output for every test claim.
