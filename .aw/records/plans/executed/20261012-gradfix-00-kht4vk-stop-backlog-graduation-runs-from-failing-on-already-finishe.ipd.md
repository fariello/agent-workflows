# IPD: Stop backlog graduation runs from failing on already-finished or concurrently-landed work

- Date: 2026-10-12
- Kind: orchestrator
- Concern: The four overnight runs of 2026-10-12 (`run-20261012T005606Z-2321569`, `run-20261012T005617Z-2321742`, `run-20261012T005641Z-2321995`, `run-20261012T005650Z-2322198`) ended ten items `fail-gate`. All ten were backlog items queued for graduation (action `plan`), and all ten were failed by the same check, `production_checks.backlog_graduate_count` (`BACKLOG-GRADUATE-COUNT`). In every case the agent did the right thing and the runner failed it. There were no `fail-verify` or other failure statuses in these runs; each item's underlying attempt disposition was `fail-verify` and the queue status `fail-gate`, so this Set covers every failure in them.
- Scope: Two independent root causes, one child each. Order 01: eight items had every linked plan executed but were still `open` (seven are provably finished; `vy20et` also has an unimplemented spec carrier), so the runner asked an agent to plan finished work and failed it for writing nothing. Order 02: two items were failed because other runs merged plans into main during the item's start, and the check counted those as plans this item produced. This plan coordinates and confirms both children.
- Scope-Paths: .aw/records/plans/pending/20261012-gradfix-00-kht4vk-stop-backlog-graduation-runs-from-failing-on-already-finishe.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Coverage: pass
- Coverage-Fingerprint: 3a4f6e35bc6846351ec7c250bed126471f18995341c418e876844f41ec957c0a
- Coverage-Checked: 2026-10-12 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: bug
- Priority: high
- Blocks-Release: next
- Set: gradfix
- Order: 0
- Highest E allocated: 02
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us
- Id: kht4vk

## Workflow history
- 2026-10-14 executed (aw agy run model=Gemini-3.8-Flash-High): RETIRED as the orchestrator rollup step of a runner Set completion, not executed by an agent: every child of Set gradfix reached executed, so the runner (run run-20261014T055436Z-2108478) retired this Order-0 plan as bookkeeping. Its own E-*/V-* items were NOT performed; the runner superseded them by enforcing the ordering, the isolation and the per-child merge gate. Justifying children: 0owirm, s95x79.
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007. Record: .aw/records/reviews/20261012-gradfix-00-kht4vk-stop-backlog-graduation-runs-from-failing-on-already-finishe.review.md Round 1
- 2026-10-12 coverage pass (aw oc run): fingerprint 3a4f6e35bc68, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-12 to-review (aw set): authored to fix the 2026-10-12 fail-gate cluster; coverage pass recorded

- 2026-10-12 coverage pass (aw oc run): fingerprint 28b24ac431b7, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-12 coverage fail (aw oc run): fingerprint ad7be4b0e796, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-12 draft (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

No run fails a backlog graduation because the work was provably already done (every IPD carrier `executed`, every spec carrier `implemented`), or because another run merged plans at the same time. Order 01 (`0owirm` E-07) closes every stranded item its predicate reports ALREADY COMPLETE at execution time; at review that is seven of the eight Cause-1 items, and `vy20et` is NOT closable because its spec carrier `89xjll` is `approved`, not `implemented` (see Deferred). The two concurrency victims (`2rm0gz`, `iosmvn`) need no closing: they stay `open` and are re-dispatched as fresh graduation turns on the next run after Order 02 (`s95x79`) ships. Their earlier, correct plans exist only on the preserved lanes `aw/lane/2rm0gz` and `aw/lane/iosmvn` (`aw lanes list` reports both "keep: no run record"); the next run does NOT reuse them, because `runner_shared.allocate_isolation_worktree` attempt-scopes a new lane when the existing one holds work and `runner_shared.integrate_stranded_lanes` only integrates lanes recorded in the current run's state. Integrating or pruning those lanes is a human choice and is out of scope.

## Detailed Implementation Checklist (TODO)


> Its own E-*/V-* items were NOT performed; the runner superseded them by enforcing the ordering, the isolation and the per-child merge gate.

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: children

- [ ] E-01 CONFIRM 0owirm REACHED executed
  - Depends on: none
  Confirm child 01 (`0owirm`, close already-complete backlog items instead of re-graduating them) reached `executed`, and that its E-07 closed exactly the items its predicate reported `COMPLETE`. Re-derive the population from `0owirm`'s recorded V-01/V-07 evidence, not from the list below: at review the Cause-1 items were `ariaau`, `ildjse`, `mflqqf`, `7yz545`, `s8veyk`, `oq05nc`, `vy20et`, `h0tiaw`, of which `vy20et` was `NOT_COMPLETE`.
  - Expected outcome: `0owirm` is under `plans/executed/`; every item `0owirm` E-07 reported `COMPLETE` is under `backlog/done/`; every item it reported `NOT_COMPLETE` is still `open` and is named with its reason.
  - Execution state: pending

- [ ] E-02 CONFIRM s95x79 REACHED executed
  - Depends on: none
  Confirm child 02 (`s95x79`, take the graduation baseline from the lane's base commit) reached `executed`.
  - Expected outcome: `s95x79` is under `plans/executed/`; its concurrent-merge test passes.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `0owirm` | `20261012-gradfix-01-0owirm-close-a-backlog-item-whose-carriers-are-all-executed-instead.ipd.md` | Closes an `open` backlog item whose linked plans are all executed, instead of dispatching it; makes the count check accept that case; closes the eight stranded items. | none |
| 02 | `s95x79` | `20261012-gradfix-02-s95x79-take-the-graduation-baseline-from-the-same-commit-the-lane-i.ipd.md` | Builds the "plans before this turn" list from the lane's base commit, so plans merged by other runs are never counted as produced. | none |

The two children are independent: they change different steps of the same function and either can ship first.

## The causes, the fixes, and why they prevent recurrence

### Cause 1 (eight items: `ariaau`, `ildjse`, `mflqqf`, `7yz545`, `s8veyk`, `oq05nc`, `vy20et`, `h0tiaw`): finished work left `open`

HOW IT HAPPENED. On 2026-10-06, plan `52opph` (commit `02bfc7618`) re-checked every pending orchestrator and, for those that failed a coverage check, moved each source backlog item from `graduated` back to `open` with the note "re-run graduation to complete the handoff". The orchestrators were then repaired by hand and executed between 2026-10-07 and 2026-10-09, but nothing moved the items back out of `open`. Three things let that happen:
1. The runner's backlog close (`runner_shared.evaluate_backlog_close`) closes an item only when THE CURRENT RUN executed one of its carriers. When the carriers executed in earlier runs, the close refuses ("this run executed none of its carriers, so the close was not earned").
2. Orchestrator retirement (`runner_shared.dispatch_orchestrator_item`) never evaluates the backlog close at all. Run summaries recorded "IPD 1u4olp ended executed, so the close was never evaluated".
3. `open` always maps to a graduation turn (`run_selection_policy._BACKLOG_ACTIONS["open"] = "plan"`), with no check for already-finished carriers.

So the runner gave an agent a finished item. The agent correctly refused to duplicate it (transcripts: "The whole malgate Set ... appears already executed"; "All three carriers are already executed"), and `backlog_graduate_count` failed it because no ACTIVE linked plan remained (`existing_handoff_plans` excludes executed plans).

FIX (Order 01). Before dispatching an `open` item, check whether every linked plan is executed; if so, close it `done` through the existing release-gate close, with no agent turn. Make the count check accept the same case as a safety net.

WHY IT PREVENTS RECURRENCE. The check is at DISPATCH, the single point every route converges on. It doesn't matter how an item ended up `open` with finished carriers (a reopen like `52opph`, a close that never fired because the work finished in another run, a retirement that skipped the close): the next run closes it instead of failing it. It does not depend on fixing each of the routes individually, which is why this Set does not try to.

### Cause 2 (two items: `2rm0gz`, `iosmvn`): other runs' plans counted as this item's

HOW IT HAPPENED. Four runs ran in parallel. To judge what a graduation turn produced, the runner lists the plans that existed before the turn and compares that list against the lane afterwards. The list came from reading the main checkout, but the lane was cut from main's HEAD a moment later. In both incidents another run merged a plan into main in between: `2rm0gz` started 26 seconds after its previous item finished, during which `jykyqb` and `ml7b9e` landed; `iosmvn` started 23 seconds after, during which `k6clui` landed. The lane contained those plans, the list did not, so the check reported them as new plans "linking a different item". Reproduced exactly: with the list taken at main-before-merge the check refuses naming those plans, and with the list taken at the lane's base commit it passes.

FIX (Order 02). Build the "before" list from the lane's own base commit (or the untouched lane before the turn), so before and after are two states of one tree.

WHY IT PREVENTS RECURRENCE. The failure needs the two reads to see different versions of main. After the fix there is only one version involved, the lane's base, so no concurrent merge can fall between them, however many runs are active. The test drives exactly that interleaving.

## Completion criteria (the whole Set is done only when)

- An `open` backlog item that is ALREADY COMPLETE (at least one IPD carrier, every IPD carrier executed, every spec carrier implemented) is closed with no agent turn, and every stranded item that is ALREADY COMPLETE at execution time is closed. OWNER: `0owirm`.
- A graduation turn that writes correctly linked plans passes while another run merges unrelated plans into main. OWNER: `s95x79`.

## Cross-IPD validation

- THE TWO FIXES MUST NOT DISAGREE ABOUT "DONE". Order 01 decides an item is already complete from its executed carriers; Order 02 changes only what counts as a NEW plan. An item with every carrier executed must be closed by Order 01 before Order 02's comparison is ever reached, and Order 02 must not change which plans count as linked.
- NEITHER CHILD MAY CLOSE A RELEASE-GATED ITEM AROUND THE EXISTING PREDICATE. Order 01 closes through `close_backlog_item`, which consults `check_engine.evaluate_blocking_close`.

## Deferred / out of scope (with reason)

- Making orchestrator retirement close its source backlog item: Order 01's dispatch-time check already covers that route and every other one.
  - Carrier-Declined: Nothing is owed. `0owirm` E-03 closes the item at its next dispatch whichever route left it `open` with finished carriers, so a second close site at retirement would duplicate that close.
- Serializing parallel runs: not needed once Order 02 lands.
  - Carrier-Declined: Nothing is owed. `s95x79` E-03 takes the baseline and the post-turn scan from one tree, so no concurrent merge can fall between them; serializing would only slow every parallel run.
- `vy20et` (a Cause-1 item whose three IPD carriers are executed but whose spec carrier `89xjll` is `approved`, not `implemented`) is NOT closed by this Set, because `0owirm`'s predicate correctly refuses to call it finished. CONSEQUENCE, stated so it is not mistaken for a fix: until `89xjll` reaches `implemented` with cited evidence (an act an agent may not perform without that evidence) or a human closes or re-scopes the item, it stays `open`, is dispatched for graduation, and can fail `BACKLOG-GRADUATE-COUNT` again if the agent again finds nothing to plan.
  - Carrier: vy20et
- The preserved lanes `aw/lane/2rm0gz` and `aw/lane/iosmvn` holding the concurrency victims' earlier correct plans (`hdep9j`; `6jp1ox`, `yuhl6o`, `9rthek`, `ev7t1w`, `ellenm`): integrating them by hand instead of letting the next run re-author, or pruning them, is the maintainer's choice.
  - Carrier-Declined: Nothing is owed by this Set. Both items stay `open` and are re-graduated by the next run, so no work is lost if the lanes are pruned; the lanes are evidence, and `aw lanes list` already surfaces them.

## Scope check

- Over-scope: none.
- Under-scope: none known. All ten fail-gate items in the four runs map to one of the two causes, and the four later runs (`run-20261012T0416*`) had no failures when investigated. The one residual recurrence path, `vy20et`, is recorded under Deferred with its carrier.

## Required tests / validation

NONE OWNED BY THIS PLAN: each child carries its own tests and the bare suite. This plan confirms both children executed (E-01, E-02).

## Spec / documentation sync

N/A here; each child records its own.

## Open questions

### OQ-01: Is either cause a one-off that needs no code fix?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: No. Cause 1 was triggered by one bulk reopen (`52opph`), but the gap it exposed, an `open` item with finished carriers being dispatched, is open to any route that leaves such an item behind, including the runner's own close declining because the work finished in another run. Cause 2 needs only two parallel runs and a merge during an item's start, which is ordinary with `aw partition`. Both are fixed in code.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: the pasted `- Status: executed` line of `0owirm`; `0owirm`'s recorded `COMPLETE`/`NOT_COMPLETE` split from its V-07; pasted `aw find backlog <id6>` output for every `COMPLETE` item showing it under `backlog/done/`, and for every `NOT_COMPLETE` item showing it still under `backlog/open/`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the pasted `- Status: executed` line of `s95x79`, and its V-03 pasted concurrent-merge test output showing a pass.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

The children are independent and may run in either order or together. Execute only after explicit human approval. Open questions: OQ-01 is resolved; none remain. `- Scope-Paths:` is a DECLARATION reconciled at finalize: this plan edits only itself, and an out-of-scope edit that proves necessary is made and justified with `--scope-reason`, not a reason to stop. HONESTY RULE: every `V-*` item MUST paste the ACTUAL output it cites; a claimed pass with no output does not satisfy it. Commit only through `aw commit kht4vk -- <paths>` (never `git add -A`, `-a`, or `--no-verify`), verify the staged set with `git diff --cached --name-only` first, and never push. The terminal transition is MANDATORY and its owner is conditional: under `aw oc run` / `aw agy run` the runner retires this orchestrator once both children are `executed`, so no agent runs `aw ipd finalize` on it; executed by hand, the executor runs `aw ipd finalize kht4vk` once `aw ipd lint --phase pre-transition` conforms and V-01 and V-02 record concrete pasted evidence with Result: pass. Never hand-roll the move or `git mv` this plan into `executed/`. Release gate: this plan carries `- Blocks-Release: next` as a live `bug` plan; keep it.
