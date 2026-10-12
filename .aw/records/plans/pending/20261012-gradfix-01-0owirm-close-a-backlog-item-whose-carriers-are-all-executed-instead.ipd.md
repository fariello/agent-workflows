# IPD: Close a backlog item whose carriers are all executed instead of re-graduating it

- Date: 2026-10-12
- Kind: child
- Concern: Eight of the ten fail-gate items in the 2026-10-12 runs were backlog items queued for a fresh graduation turn while sitting at `open`. In seven of them every plan linked by `- From-Backlog:` was already `executed`. In the eighth, `vy20et`, the three plans were executed too, but its spec carrier `89xjll` is `approved` and not `implemented`. The agent correctly saw there was nothing left to plan and wrote no plan, and the graduation count check (`production_checks.backlog_graduate_count`) then failed the item with "produced 0 linked IPDs". So a correct agent was failed for not duplicating finished work, and the item can never reach `done` on its own, because `runner_shared.evaluate_backlog_close` only closes an item when THIS run executed a carrier.
- Scope: (1) Before dispatching an `open` backlog item for graduation, if it is ALREADY COMPLETE (at least one IPD carrier, every IPD carrier `executed`, every spec carrier `implemented`), do not spend an agent turn: close the item `done` citing an executed carrier, through the existing gated setter and therefore `check_engine.evaluate_blocking_close`, inside the item's isolated lane so nothing is written to the shared checkout mid-run. (2) Make `backlog_graduate_count` accept a production turn that wrote no plan when the item is ALREADY COMPLETE, and route that post-turn case to the same close instead of to the `graduated` setter. (3) Amend the two specs that describe the `open` dispatch and the automated close. (4) Close the stranded items that are ALREADY COMPLETE at execution time. No change to how a live, unfinished item graduates.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/production_checks.py, tests/test_backlog_already_complete.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, .aw/records/specs/to-review/20260920-llbr2b-01-llbr2b-lifecycle-automation-policy.spec.md, .aw/records/backlog
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- Blocks-Release: next
- Set: gradfix
- Order: 1
- Highest E allocated: 07
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us
- Id: 0owirm
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010. Record: .aw/records/reviews/20261012-gradfix-01-0owirm-close-a-backlog-item-whose-carriers-are-all-executed-instead.review.md Round 1
- 2026-10-12 to-review (aw set): authored to fix the 2026-10-12 fail-gate cluster (Set gradfix)

- 2026-10-12 draft (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

An `open` backlog item whose work is provably finished (every IPD carrier executed, every spec carrier implemented) is closed `done` automatically, through the release-gate predicate and without an agent turn, and is never queued for re-graduation. The runner stops failing correct agents for declining to duplicate finished work. An item that is not provably finished graduates exactly as it does today.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: reproduce and add the predicate

- [ ] E-01 REPRODUCE on real records before changing code, RE-DERIVING the population rather than trusting F-01. For each of `ariaau`, `ildjse`, `mflqqf`, `7yz545`, `s8veyk`, `oq05nc`, `vy20et`, `h0tiaw`, and for any other `open` backlog item you find with at least one `From-Backlog` carrier, record: its directory, every carrier from `check_engine.find_from_backlog_artifacts` (plans AND specs), each carrier's bucket (plans) or `- Status:` (specs), `runner_shared.evaluate_backlog_close(repo, <id6>, [])`'s reason, and `production_checks.backlog_graduate_count(repo, <id6>, <every current plan id>)`. Paste the table. Expected at review time: the seven items other than `vy20et` have only executed IPD carriers; `vy20et` also carries spec `89xjll` at `approved`; all eight `evaluate_backlog_close` reasons read "this run executed none of its carriers, so the close was not earned"; all eight count checks return "produced 0 linked IPDs". An item with any carrier in `pending/`, or with an unimplemented spec carrier, is NOT this defect's close target. Record it as such and continue. Do not stop.
  - Depends on: none
  - Expected outcome: a pasted table, re-derived at execution HEAD, that splits the items into ALREADY COMPLETE and NOT COMPLETE with the carrier that decides each. The count is whatever the table shows, not "eight".
  - Execution state: pending

- [ ] E-02 Add ONE predicate, `runner_shared.backlog_item_already_complete(repo, item_id6)`, returning a typed result: `COMPLETE` (with the carrier paths, and the executed IPD carrier to cite as close evidence), `NOT_COMPLETE` (with the unfinished or retired carriers named), or `NO_IPD_CARRIER` (no carrier at all, or only non-IPD carriers). Do NOT write a second carrier scan. Factor the carrier-classification half of `runner_shared.evaluate_backlog_close` (the `find_from_backlog_artifacts` lookup, the `_carrier_kind` partition, `plan_bucket(...) == "executed"` for IPDs, `check_engine._carrier_is_executed` for spec carriers) into a shared private helper that BOTH functions call, so the two cannot disagree. `evaluate_backlog_close` keeps its earned clause (E-04 of `zhr6mc`) and its non-IPD existence rule, unchanged in behaviour. The new predicate differs from it in exactly two ways, both recorded in its docstring: it does NOT require the run to have earned the close (D-1), and an item with no IPD carrier is `NO_IPD_CARRIER`, never `COMPLETE` (D-3). A carrier under `superseded/` or `not-executed/` is not done. An item whose carriers are all retired, or any mix that includes a retired or pending carrier, is `NOT_COMPLETE`, because deciding that work is abandoned is a human act (OQ-01). The predicate fails closed: any lookup or read error returns `NOT_COMPLETE` with the error as its reason, never `COMPLETE`.
  - Depends on: E-01
  - Expected outcome: a function that returns `COMPLETE` for exactly the E-01 rows classed ALREADY COMPLETE and `NOT_COMPLETE` for `vy20et` (spec `89xjll` not implemented) and for any row with a pending or retired carrier, with `evaluate_backlog_close`'s verdicts unchanged for every E-01 item.
  - Execution state: pending

### Task group 2: stop the wasted turn and the false failure

- [ ] E-03 Close instead of dispatch, at the one place every route converges on. In `runner_shared.execute_item_core`, on the `is_backlog_production` path, evaluate E-02 against MAIN (`repo`) BEFORE `build_prompt`/`write_prompt` (the placement the `planstale` refusal uses, so no orphan prompt file is written) and before any agent spawn. On `COMPLETE`:
  (i) close the item in the item's own isolated lane when isolation is on: allocate it with `allocate_isolation_worktree` as the production path already does, call `close_backlog_item(lane, item_path_in_lane, id6, evidence=<cited executed carrier>, message=..., gate_root=repo, run_checked=...)` so `check_engine.evaluate_blocking_close` decides any `Blocks-Release` item against main, commit the move in the lane with `commit_backlog_transition_output(lane, id6, status_label="done", run_id=...)`, and publish it through `integrate_under_repository_lock` with the same `integrate_review_lane_branch` integrate callable the graduation success path uses. Under `--no-isolate-worktree`, close in `repo` and commit with `commit_backlog_close`, the existing non-isolated route. Never write the shared checkout mid-run on the isolated path (the measured `dirtygates-03` `9iq461` harm).
  (ii) append a `backlog-already-complete` event to `events.jsonl` naming the item, every carrier and the evidence, set the queue item `executed`, record `item["backlog_close"]` with `closed: True` and the predicate's reason so `unclosed_backlog_items` does not report it, and spawn no agent session.
  (iii) If the close or its integration REFUSES (for example a release gate the cited evidence does not satisfy, or a refused fast-forward), do NOT fall through to an agent turn, since an agent can author nothing for finished work: set the queue status `fail-gate`, set `item[NEEDS_INPUT_KEY] = True`, record the refusal with `record_refusal` carrying the setter's or integrator's message and a remedy, and preserve the lane with `lane_containment.record_lane_preserved`. `needs-input` is NOT written as a queue status: it is in neither `TERMINAL_STATES` nor `runner_shutdown.KNOWN_ITEM_STATUSES`, so writing it would make the R3 ledger-coherence check refuse the run's own resume. The `fail-gate` + `NEEDS_INPUT_KEY` pair is the shipped precedent for "a human decision is missing".
  On `NOT_COMPLETE` or `NO_IPD_CARRIER`, dispatch exactly as today.
  - Depends on: E-02
  - Expected outcome: an `open` backlog item whose carriers are all finished is closed `done` with no agent session started, via the lane and the integration lock on the isolated path; a refused close ends `fail-gate` with `needs_input` and no agent session.
  - Execution state: pending

- [ ] E-04 Make the post-turn path tell "already done" from "failed to plan". (a) In `production_checks.backlog_graduate_count`, before the "produced 0 linked IPDs" refusal, when no linked plan is active AND no new plan was produced, return no finding if `runner_shared.backlog_item_already_complete` is `COMPLETE` (lazy import, as `production_checks` already does for `runner_shared` elsewhere). Keep every other refusal: an item with no carriers that produced nothing still fails, `NOT_COMPLETE` still fails, and an unlinked new plan still fails. (b) In `execute_item_core`'s backlog-production success branch, BEFORE the `aw backlog set ... --status graduated` setter, if the predicate is `COMPLETE` and the turn produced no plan, perform the E-03 close through the SAME helper instead of graduating. Without (b), (a) alone would let the run reach the `graduated` setter with an empty produced list and mark a finished item `graduated`. This is the safety net for an item that reaches the check by another path (a queue built before E-03 shipped, a resume, or a correction turn).
  - Depends on: E-03
  - Expected outcome: the count check returns no finding for an ALREADY COMPLETE item and still refuses a genuinely empty graduation; a production turn on an ALREADY COMPLETE item ends with the item in `done/`, never `graduated/`.
  - Execution state: pending

### Task group 3: prove, document, and clear today's stranded items

- [ ] E-05 Add `tests/test_backlog_already_complete.py` (P16: drive real fixture repos and the real runner, assert on queue status, `events.jsonl`, the backlog file's directory and the agent fake's call count, never on source text). Reuse the shape of `tests/test_backlog_production.py` (`_make_test_repo`, `_write_backlog_item`, `_patch_host_agent`, and its `_HOSTS` loop so BOTH `oc_runipd` and `agy_runipd` are driven), with a fake agent that records whether it was called. Cases: (a) every IPD carrier executed: item closed `done`, agent never called, `backlog-already-complete` event present, queue `executed`; run once with `--no-isolate-worktree` and once with isolation on, and for the isolated run assert the shared checkout's `git status --porcelain` is empty before integration and the close arrives on `main` as a commit; (b) one carrier pending: agent called and the item graduates or fails exactly as today; (c) every carrier retired (`superseded/`): item NOT closed, dispatched as today; (d) one executed and one superseded carrier: NOT closed; (e) one executed IPD carrier plus an `approved` (not `implemented`) spec carrier: NOT closed; (f) `Blocks-Release: rel001` item whose executed carrier carries the same gate: closed through the predicate; (g) `Blocks-Release` item whose executed carrier carries NO gate and no other route satisfies it: not closed, agent never called, queue `fail-gate` with `needs_input` true and the setter's refusal recorded; (h) `backlog_graduate_count` returns no finding for (a)'s tree and still refuses an item with zero carriers that produced nothing; (i) the post-turn route of E-04 (b), driven by bypassing the dispatch-time check (for example a fake agent invoked on a queue whose item becomes COMPLETE during the turn): item ends in `done/`, never `graduated/`. Cases (a), (h) and (i) must FAIL on the base commit; show it.
  - Depends on: E-03, E-04
  - Expected outcome: the new module passes on both hosts, and (a), (h), (i) are shown failing on the base commit with their actual failure lines.
  - Execution state: pending

- [ ] E-06 Amend the specs this changes, in the same change. (1) Spec `25kzda` 3.4, `open` row, Interactive action: add one sentence stating that an `open` item whose carriers are already complete (at least one IPD carrier, every IPD carrier `executed`, every spec carrier `implemented`) is CLOSED `done` through the release-gate predicate with no agent turn, and that a refused close needs a human, rather than being re-graduated. (2) Spec `llbr2b` 3.4 (the catalog of automated transitions): add the new route as its own row or paragraph, naming `runner_shared.backlog_item_already_complete` and the dispatch site, and state that it is the ONE automated close that does not require the run to have earned it, with the reason (D-1). Also correct the plan's stale claim that a runner event list documents `backlog-item-closed`: no such doc list exists, so the event is documented in `llbr2b` 3.4 beside `backlog-item-left-open`.
  - Depends on: E-03
  - Expected outcome: `git diff` of both spec files showing exactly those additions, and `aw specs check` (or `aw check all`) reporting no new finding for either spec.
  - Execution state: pending

- [ ] E-07 Close the stranded items that E-02 reports `COMPLETE` at execution HEAD, re-running E-02 on each immediately before closing it. For each: `aw backlog set done <id6> --evidence <executed IPD carrier path> --message "closed by 0owirm: every carrier executed (<carriers>)"`, paste each result. Do NOT close an item E-02 reports `NOT_COMPLETE` (at review time `vy20et`, whose spec `89xjll` is `approved`, not `implemented`); list each such item with its reason in the evidence. Commit the moves through `aw commit 0owirm -- <each moved backlog path>`. Then run the bare suite `python3 -m pytest` and paste its summary line, against a pre-edit bare-suite baseline taken at the start of execution: the failing-test set after the change must be a subset of the baseline's, compared by name.
  - Depends on: E-05, E-06
  - Expected outcome: every item E-02 reports `COMPLETE` is under `backlog/done/` with a resolvable evidence citation; every `NOT_COMPLETE` item is untouched and listed with its reason; bare suite shows no newly failing test against the baseline.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Suite BARE as `python3 -m pytest`; narrowed runs `-o addopts=""`. Tests drive surfaces, never read source (P16).
- Commit through `aw commit <plan> -- <paths>`; never push.
- Release-gated closes go through `check_engine.evaluate_blocking_close` via the gated `aw backlog set <id6> --status done --evidence` spelling (`runner_shared.close_backlog_item`); never write `done` around it.
- An isolated runner turn writes only its lane; the shared checkout changes only through `integrate_under_repository_lock` (`dirtygates-03` `9iq461`).
- A queue status must be in `TERMINAL_STATES` and `runner_shutdown.KNOWN_ITEM_STATUSES`; "needs a human" is the `NEEDS_INPUT_KEY` flag beside `fail-gate`, not a status.
- A plan may amend a spec and must list it in `- Scope-Paths:`.
- Cite code by SYMBOL.

## Findings

| ID | Finding | Evidence |
|----|---------|----------|
| F-01 | Eight fail-gate items are `open` backlog items whose IPD carriers are all executed; seven have no other carrier, and `vy20et` also has spec carrier `89xjll` at `approved`. | `ariaau`->`qtz0us,bec7ee,38pxaz,dmjp0u`; `ildjse`->`i18yaz,32jpl1,eow7p4`; `mflqqf`->`u57rfv,gqyold,d0lg63`; `7yz545`->`1u4olp,czut8j,ov2c9n,r5fk4k`; `s8veyk`->`4qv834,bqtgmo,y9m1ya`; `oq05nc`->`l4vw9o,x2dwu5,pi3bk8,wzhe4n`; `vy20et`->`9wzlou,jjh4aj,rtvdak` + spec `.aw/records/specs/approved/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md` (`- Status: approved`, `- From-Backlog: vy20et`); `h0tiaw`->`l8wvv3,dq9bj9,9i2hge`. All plans under `plans/executed/` (re-measured at review, 2026-10-12). Live population: re-derive at execution (E-01). |
| F-02 | They were set back to `open` on purpose, then never re-closed. | Commit `02bfc7618` ("reopen(backlog): reopen 13 backlog items and record note on h0tiaw", plan `52opph`, 2026-10-06): each item's newest history line reads "<orchestrator> returned to authoring: uncovered obligation: ...; re-run graduation to complete the handoff". The orchestrators then executed 2026-10-09..11 (e.g. `qtz0us`, `u57rfv`, `1u4olp` 2026-10-09; `i18yaz`, `l4vw9o` 2026-10-11). |
| F-03 | The runner's close never fired for them, by design. | `runner_shared.evaluate_backlog_close` refuses with "this run executed none of its carriers, so the close was not earned" when the deciding carrier is not in the run's earned set; that clause is executed plan `zhr6mc` E-04 and is catalogued as a condition in spec `llbr2b` 3.4 ("the run EARNED it"). `runner_shared.dispatch_orchestrator_item` never calls `process_backlog_close`. Measured at review: `evaluate_backlog_close(repo, "ariaau", [])` returns exactly that reason. |
| F-04 | `open` maps to `plan` with no carrier check. | `run_selection_policy._BACKLOG_ACTIONS["open"] = ACTION_PLAN`. |
| F-05 | The agent behaved correctly; the check failed it. | `production_checks.backlog_graduate_count` condition (a) `if not all_linked` returns "produced 0 linked IPDs", and `production_checks.existing_handoff_plans` skips every plan whose disposition is terminal. Measured at review: `backlog_graduate_count(repo, "ariaau", <all plan ids>)` returns that finding. |
| F-06 | Passing the count check alone would lead into the `graduated` setter. | `execute_item_core`'s backlog-production success branch calls `aw backlog set <id6> --status graduated` whenever no finding remains and the item is still `open`, building its message from `all_verified_plans`, which is empty for a turn that wrote nothing. |
| F-07 | A dispatch-time close must not write the shared checkout mid-run. | `runner_shared.process_backlog_close` docstring (dirtygates-03 `9iq461`): "NOTHING is written to the shared checkout while the run is still going", citing the 2026-09-13 measurement where one uncommitted close made a whole-tree gate refuse 27 of 42 items. |

## Proposed changes (ordered, validatable)

1. Reproduce and classify (E-01).
2. One shared "already complete" predicate (E-02).
3. Close instead of dispatch, in the lane (E-03).
4. Count check plus post-turn route to the same close (E-04).
5. Tests on both hosts (E-05).
6. Spec amendments (E-06).
7. Close today's ALREADY COMPLETE items, bare suite (E-07).

## Deferred / out of scope (with reason)

- Teaching orchestrator retirement to close its source backlog item: the dispatch-time check (E-03) covers every route by which an item ends up `open` with finished carriers (a reopen like `52opph`, a close that never fired because the work finished in another run, a retirement that skipped the close), so a second close site is unnecessary.
- An item stranded in `graduated` (not `open`) with finished carriers: NOT covered here, because `_BACKLOG_ACTIONS["graduated"]` is `skip`, so it is never dispatched. That case is owned by pending plan `isnqja` (Set `wfswdb`), which surfaces such items in `aw attention`. None of today's eight is `graduated`.
- Closing `vy20et`: its spec carrier `89xjll` is not `implemented`, so the item is not provably finished. It needs the spec to reach `implemented` or a human close.
- Changing what `52opph` did: it is executed history.

## Scope check

- Over-scope: none.
- Under-scope: none known after review (the spec amendments, the post-turn route, the lane-based write and the both-hosts tests were added by review).

## Required tests / validation

- `tests/test_backlog_already_complete.py` (new), both hosts, with (a), (h) and (i) shown failing on the base commit.
- Bare suite `python3 -m pytest` against a pre-edit baseline.
- Each `aw backlog set done` output pasted, plus the list of items left open with reasons.

## Spec / documentation sync

Required, done by E-06. Spec `25kzda` 3.4 (approved) defines the `open` action as authoring artifacts and graduating; this plan adds a close-instead branch to that row, so the row must say so. Spec `llbr2b` 3.4 (to-review) catalogues automated backlog closing and lists "the run EARNED it" as a condition; this plan adds an automated close that deliberately omits that condition, which must be catalogued with its reason (D-1). Both files are listed in `- Scope-Paths:` so the runner announces the spec edits. No user-facing doc lists runner events, so no README or CHANGELOG change is required; the new `backlog-already-complete` event is documented in `llbr2b` 3.4.

## Open questions

### OQ-01: Should an item whose carriers are all RETIRED be closed automatically too?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: No. A retired carrier means someone decided not to do that work; whether the backlog item is therefore finished or still needs a different plan is a human judgement. E-02 returns `NOT_COMPLETE` for that case and for any mix including a retired carrier, and E-05 (c) and (d) pin it. Reversible.

### OQ-02: May the dispatch-time close skip `evaluate_backlog_close`'s "the run earned it" condition?

- Blocking: no
- Status: resolved
- Owner: plan reviewer
- Resolution or deferral rationale: Yes, for this one route only (review decision D-1). The earned clause (executed plan `zhr6mc` E-04) stops a run closing an item it merely observed while executing something else. Here the runner has already chosen to act on this exact item, and the alternative measured on 2026-10-12 is an item that can never close and fails a correct agent on every run. Every carrier still has to be finished, the release-gate predicate still decides any `Blocks-Release` item, and `evaluate_backlog_close` keeps the clause unchanged for its own callers. The exception is catalogued in spec `llbr2b` 3.4 by E-06. Reversible: deleting the E-03 branch restores today's behaviour.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the pasted table re-derived at execution HEAD, with each item's carriers, carrier buckets/statuses, `evaluate_backlog_close` reason and `backlog_graduate_count` result, and the ALREADY COMPLETE / NOT COMPLETE split it implies.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the predicate's pasted output for every E-01 row (matching the split), for a fixture with one pending carrier, an all-retired fixture, a mixed executed+superseded fixture, and a spec-only fixture (`NO_IPD_CARRIER`); plus `evaluate_backlog_close` reasons for the E-01 items unchanged from V-01.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: E-05 cases (a) (both isolation modes), (f) and (g) passing on both hosts, with the pasted test output, showing the `backlog-already-complete` event, the backlog file in `done/` (or untouched for (g)), the agent fake's zero call count and, for (g), `fail-gate` with `needs_input`. Observation produced by `execute_item_core`'s backlog-production path through the E-03 branch, driven by `run_queue`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: E-05 (h) passing, both halves, and (i) passing, showing the item in `done/` and absent from `graduated/`, with the pasted test output. Observation for (i) produced by the E-04 (b) branch before the `graduated` setter.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the new module's pasted pass output on both hosts, and the pasted failure lines for (a), (h) and (i) on the base commit.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the pasted `git diff` of both spec files, and the pasted spec check output showing no new finding for either.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: each `aw backlog set done` output pasted, each closed item's new `done/` path, the list of items left open with their predicate reason, the `aw commit` output, and the bare-suite summary line beside the baseline's failing-test set compared by name.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval. Open questions: OQ-01 and OQ-02 are resolved; none remain. `- Scope-Paths:` is a DECLARATION reconciled at finalize: an out-of-scope edit that proves necessary is made and justified with `--scope-reason`, not a reason to stop. STOP and report only if a co-worker's uncommitted change occupies a region you must edit and the two cannot be safely combined, or if a symbol this plan cites by name is absent. HONESTY RULE: every `V-*` item MUST paste the ACTUAL runner output; a claimed pass with no output does not satisfy it. Start with `aw ipd begin 0owirm`. Commit only through `aw commit 0owirm -- <paths>` (never `git add -A`, `-a`, or `--no-verify`), verify the staged set with `git diff --cached --name-only` first, and never push. The terminal transition is MANDATORY and its owner is conditional: under `aw oc run` / `aw agy run` the runner performs the finalize after its merge-and-revalidate gate, so the executor must NOT run `aw ipd finalize`; executed by hand, the executor runs `aw ipd finalize 0owirm` once `aw ipd lint --phase pre-transition` conforms and every `V-*` records concrete pasted evidence with Result: pass. Never hand-roll the move or `git mv` this plan into `executed/`. Release gate: this plan carries `- Blocks-Release: next` as a live `bug` plan; keep it.
