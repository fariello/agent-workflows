# IPD: Close the reaskscore Set: receipt-check svacmz and transition both source backlog items honestly

- Date: 2026-09-21
- Kind: child
- Concern: The `reaskscore` Set's closing acts are owned by nobody who will perform them. They sit on the Order-0 orchestrator `s0gnha` as its E-02 (a receipt check over `svacmz`'s evidence) and E-03 (transitioning the two source backlog items), and the runner RETIRES an orchestrator once every child is `executed` while deliberately SKIPPING the pre-transition E/V checkpoint. E-03 IS THE SHARP CASE, because the parent's own text calls it "the one substantive act that belongs on this plan because it is a Set-level record change no child owns": two backlog items carrying `Blocks-Release: next` would be left untransitioned while the Set reported complete, so a release gate would silently survive a Set that claimed to have discharged it. MEASURED 2026-09-22 by the orchestrator coverage probe, which refused a 34-set launch naming `s0gnha` among five uncovered parents (event `orchestrator-probe-gate`, emitted at `runner_shared` symbol `run_orchestrator_probe_gate`).
  THIS PLAN IS NOT RUNNABLE YET, AND THAT IS THE FIRST THING AN EXECUTOR MUST KNOW. It declares `Item-Dependencies: executed:svacmz`, and `svacmz` is `approved` in `pending/`, not `executed`. Measured at review HEAD `73e370ae` with the shipped predicate: `oc_runipd.dependency_status_detailed` returns unsatisfied for `executed:svacmz`, reason "external target svacmz is 'approved' (directory 'pending'), needs one of ['executed']". So a run dispatching this item today marks it `dependency-blocked` and moves on. TWO SIBLINGS ARE OUTSTANDING, not one: `runner_shared.evaluate_set_retirement` reports `Set 'reaskscore' has 3 child(ren) that are not 'executed': dy9ymn (approved), svacmz (approved), p9j6c0 (to-review)`. The order is therefore `dy9ymn` -> `svacmz` -> this plan, and the ordering is the runner's to enforce (dependency depth is its first sort key), so this is a STATE OF THE WORLD to be aware of and NOT a defect in this plan.
  THE CONSEQUENCE FOR E-01 IS SUBSTANTIVE, however. A receipt check reads evidence somebody else wrote, and at review HEAD all four of `svacmz`'s `Observed evidence` blocks are EMPTY with all four `Result: pending`, because that plan has not run. So E-01 is not merely early: executed against today's tree it would read four blank blocks and correctly report an upstream failure, which by this plan's own OQ-01 blocks both backlog transitions. That is the designed behavior rather than a flaw, and it is why E-01's failure path is the load-bearing half of this plan rather than a formality.
- Scope: Perform `s0gnha`'s E-02 and E-03 as a real agent turn. IN: the receipt check over `svacmz`'s `V-01`..`V-04` evidence; the honest transition of backlog `yxfw4k` and `x7wfyx` through `aw backlog set`, respecting the close-legitimacy gate and each item's `Blocks-Release: next`; and a bare green suite on the merged result. OUT: `s0gnha` E-01's dispatch orchestration, which is the runner's act and not an agent's; any re-performance of `svacmz`'s verifications (it owns them, and duplicating them would put the same assertions in two places with no second observer); and any product code change.
- Scope-Paths: .aw/records/plans/pending, .aw/records/backlog/graduated, .aw/records/backlog/open, .aw/records/backlog/done
- Item-Dependencies: executed:svacmz
- Status: approved
- Readiness: go-pending-approval
- From-Backlog: yxfw4k
- Blocks-Release: next
- Set: reaskscore
- Order: 5
- Highest E allocated: 03
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: p9j6c0
- Approval: 2026-09-23, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-23 approved (aw set): status set to approved
- 2026-09-22 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008. THE PLAN SHOULD EXIST AND ITS PREMISE CHECKS OUT: re-verified in code rather than from the gitignored run log, `runner_shared.evaluate_set_retirement` reports `Set 'reaskscore' has 3 child(ren) that are not 'executed'`, and both source backlog items are exactly as F-02 describes (`yxfw4k` graduated, `x7wfyx` open, both `Blocks-Release: next`, both `Work-Kind: bug`). PR-001 (BLOCKER): E-02's central safety claim is FALSE for this item. It asserted `aw backlog set done yxfw4k` "FAILS CLOSED unless the gate is provably preserved or released"; measured by calling the shipped predicate, `evaluate_blocking_close(repo, yxfw4k, 'done', evidence=None)` returns LEGITIMATE via route HANDOFF, because four plans carry `From-Backlog: yxfw4k` with the same gate (`skn8uk`, `ty7w6o`, `s0gnha`, `svacmz`) and HANDOFF is checked before SATISFIED. So the command exits 0 on absent evidence, two of those four carriers have not themselves executed, and the plan rested its most dangerous step on a refusal that never arrives. E-02, OQ-01, V-02 and the gate now all state that exit 0 proves nothing here and that OQ-01's answer is enforced only by E-01 plus the executor's honesty. PR-002 (HIGH): the receipt-check bar was WEAKER than the bar it checks, in the exact place `svacmz`'s own review closed a hole - E-01 asked for five constants' values while `svacmz`'s V-01 demands EIGHT definition sites and says in terms that a five-site paste FAILS; and E-01 demanded a `git diff` for both pin files while `svacmz`'s V-02 was re-expressed at ASSERTION level after its review measured the empty-diff bar unsatisfiable. E-01/V-01 now quote that plan's live wording. PR-003 (HIGH): the plan is not runnable at review HEAD - `oc_runipd.dependency_status_detailed` reports `executed:svacmz` unsatisfied ("external target svacmz is 'approved' (directory 'pending')") and `dy9ymn` is outstanding too, so E-01 can today only take its failure path; stated in the Concern and the gate, with the run order `dy9ymn` -> `svacmz` -> this plan, and explicitly NOT treated as a plan defect since the runner owns ordering. PR-004 (HIGH): the Set's release gate died at its closing child (parent and `svacmz` both carry `From-Backlog: yxfw4k` + `Blocks-Release: next`; this plan carried neither) - set through the setter. PR-005 (MEDIUM): E-03 named the delivered half only by letter; both halves now named by content, with the item's own 2026-09-22 correction that item B's trigger is a HOST truncation recorded by `ty7w6o` and consumed by `dy9ymn`. PR-006 (MEDIUM): `graduated` is NOT gated by the predicate, so nothing would notice a dropped gate on that route; V-03 now makes the pasted front matter the only proof. PR-007 (LOW): five Deferred rows lacked a durable carrier, and the workflow history's three 2026-09-21 entries were oldest-first, reading as a backwards `to-review` -> `draft` transition; both repaired and `aw check plans` now reports clean for this plan. PR-008 (LOW): V-01 did not say that a reported upstream failure IS a pass, which risked an executor running `svacmz`'s checks itself to produce something green. `aw ipd lint --phase author` conforming before, `--phase review-finalize` conforming after.

- 2026-09-21 note (opencode/its_direct-pt3-claude-opus-5-1m-us): This Set was ALREADY partly self-aware of the retirement hazard: `svacmz` was authored to own the verifications "so it is performed and verified by an agent turn instead of being retired unperformed" (its child-table row says exactly that). What that fix missed is the BACKLOG TRANSITION, which no child took, and which is the release-gate-bearing half.
- 2026-09-21 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored at the maintainer's direction after the orchestrator coverage gate refused run `run-20260922T003414Z-1020752`, naming `s0gnha` as carrying work no child covers. Content is lifted from the parent's E-02 and E-03 rather than invented, so the obligation is unchanged and only its owner moves; the parent's checklist stays in place. NOTE the parent's E-01 is deliberately NOT lifted: it is dispatch ordering, which a runner performs by construction and an agent cannot meaningfully "do".
- 2026-09-21 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Make the `reaskscore` Set's completion honest at its two weakest points: that `svacmz` actually pasted
evidence rather than asserting success, and that the two source backlog items reach the state the work
actually justifies. The second matters most: both carry `Blocks-Release: next`, so leaving them
untransitioned lets a Set report complete while a release gate it was meant to discharge quietly persists.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: receipt check, then the record transitions

- [ ] E-01 RECEIPT-CHECK `svacmz`'s FOUR VALIDATION ITEMS, by reading its executed plan file rather than by re-performing its work. This is deliberately a receipt check and NOT a second verification: `svacmz` owns the predicate-unweakened pins (its E-01/E-02) and both measured-shape reconstructions plus the collision case (its E-03/E-04), and duplicating them here would put the same assertions in two places with no second observer.
  READ `svacmz`'s OWN V-ITEM TEXT AS THE BAR, NOT THE PARAPHRASE BELOW, because that plan's review CHANGED two of these bars and a receipt check against a stale paraphrase would pass evidence its owner would reject. Two corrections, both measured at review HEAD `73e370ae` against `svacmz`'s current file. (1) `V-01` REQUIRES EIGHT DEFINITION SITES, NOT FIVE: its text reads "A statement that 'the constants are unchanged' without the values FAILS this item, and so does a paste covering only five sites, because the duplicated names are the ones a one-sided edit hides in" - five NAMES across EIGHT sites in three files, plus the three `TERMINAL_STATES` copies shown mutually equal and `EXECUTE_REPORTING_SUCCESS_STATES` shown still equal to `SUCCESS_STATES - {"reviewed"}` as a DERIVATION. A five-site paste FAILS by that item's own words, so accepting one here would launder the exact hole its review closed. (2) `V-02` DOES NOT DEMAND A CLEAN `git diff`: its review found the empty-diff bar already unsatisfiable (3 insertions / 2 deletions from unrelated main commit `eee6f427`, zero assertion lines) and re-expressed it at ASSERTION level, so the bar is that each changed line is a comment, docstring or citation, or else is attributed to the sibling that changed it. Requiring a clean diff here would manufacture a failure its owner explicitly ruled out.
  CONFIRM, then, on `svacmz`'s file: `V-01` carries the eight sites' ACTUAL VALUES plus the two derivation checks; `V-02` carries the pin output plus the assertion-level diff attribution for both pin files; `V-03` and `V-04` carry the SHAPE A and SHAPE B reconstruction output, the per-item retry counter values, and the collision case. An empty or hand-waved `Observed evidence` block on any of those four is a FAILURE of this item, and the Set is not complete - report it rather than compensating by running the checks here.
  EXPECT THE FAILURE PATH TODAY AND DO NOT TREAT IT AS YOUR OWN FAULT. Measured at review HEAD, `svacmz` is `approved` in `pending/` with all four `Observed evidence` blocks EMPTY and all four `Result: pending`. If that is still true when you run, the correct output of this item is a named upstream failure, E-02 and E-03 must NOT proceed (OQ-01), and this plan should report that the Set is not closeable yet. Say which blocks were empty.
  - Depends on: none
  - Expected outcome: a per-item statement quoting the evidence line that satisfies each of `svacmz`'s `V-01`..`V-04` AGAINST THAT PLAN'S CURRENT TEXT (eight sites for `V-01`, assertion-level attribution for `V-02`), or a named upstream failure identifying which block was empty.
  - Execution state: pending

- [ ] E-02 TRANSITION `yxfw4k` HONESTLY, RESPECTING ITS RELEASE GATE. Set it `done` ONLY IF its defect is fixed AND validated by `svacmz`'s evidence, as confirmed in E-01; if E-01 found that evidence absent, this item must NOT close it. Pass `--evidence` citing `svacmz`'s plan file, because that is the artifact that actually validated the fix, and do NOT clear the gate with `--blocks-release -`, which would discharge a release blocker by deleting it.
  DO NOT RELY ON THE CLOSE-LEGITIMACY GATE TO CATCH YOU, because for THIS item it does not. The item's text formerly asserted that `aw backlog set done` "FAILS CLOSED" here; measured at review HEAD `73e370ae` by calling the shipped predicate directly, `check_engine.evaluate_blocking_close(repo, yxfw4k, "done", evidence=None)` returns LEGITIMATE via route HANDOFF, reason "gate 'next' handed off to a From-Backlog plan or spec" - with NO evidence passed at all. The cause is that four plans carry `From-Backlog: yxfw4k` with the same `Blocks-Release: next` (`skn8uk`, `ty7w6o`, `s0gnha`, `svacmz`), and the predicate checks HANDOFF before SATISFIED, so the handoff route short-circuits. TWO CONSEQUENCES, and the second is the one that matters. FIRST, `--evidence` here is BELT-AND-BRACES rather than the thing that unlocks the command, so its route will report HANDOFF and not SATISFIED; do not read that as a failure, and do not go hunting for a different citation to force the SATISFIED route. SECOND, and this is the real point: the tool will NOT stop you closing this item on absent evidence. Two of its four handoff carriers (`s0gnha`, `svacmz`) are themselves still `approved` in `pending/`, so the gate is being preserved by plans that have not run. THE ONLY THING STANDING BETWEEN THIS ITEM AND A FALSE CLOSE IS E-01's RECEIPT CHECK AND YOUR HONESTY. State in your evidence which route the predicate actually reported.
  - Depends on: E-01
  - Expected outcome: `yxfw4k` is `done` with a tool-written history entry citing `svacmz`'s plan file via `--evidence`, and the gate was NOT cleared; pasted command output, plus the route the predicate reported (expected HANDOFF, per the measurement above) stated explicitly rather than assumed to be SATISFIED.
  - Execution state: pending

- [ ] E-03 TRANSITION `x7wfyx` TO `graduated`, NOT `done`, AND DO NOT CLEAR ITS `Blocks-Release`. The reason is substantive and is the parent's: only its item B is implemented, so `done` would assert delivery of work that was not delivered. `graduated` is the correct state - the design is handed off while code for the remainder is not written - and the release gate must SURVIVE the transition, because the undelivered half still gates the release. Use `aw backlog set` so the history entry is tool-written.
  NAME BOTH HALVES BY THEIR ACTUAL CONTENT, verified against the item's own "What is still missing" section at review HEAD `73e370ae`, so the history entry is checkable rather than a bare letter. DELIVERED, ITEM B: "a zero-work turn is terminal when it could be retryable" - and record the CORRECTION the item itself carries, because it changes what was delivered: its trigger is a HOST truncation and not an agent choice, so the signal is recorded by `ty7w6o` as `attempt["host_truncation"]` plus a `host-truncated-turn` event and `dy9ymn` consumes it to decide the retry. NOT DELIVERED, ITEM A: "the agent is not told how much turn it has left" - the driver knows `stall_timeout` and `MAX_TURN_TIMEOUT` and the agent knows neither, which the item records as "still worth doing but would NOT have prevented the measured incident". That last clause is why `graduated` rather than `done` is honest and also why the gate must survive: the remaining half is real work, and the item is `Work-Kind: bug`, which under this repo's every-live-bug-gates-the-release rule MUST carry `Blocks-Release` while it is live - and `graduated` IS live.
  NOTE `graduated` IS NOT GATED by the close-legitimacy predicate (only `done` is checked, and `parked` warns), so no refusal will stop you here and nothing will complain if the gate goes missing. Preserving it is therefore entirely on you: `aw backlog set graduated` without `--blocks-release -` leaves it in place, so simply do not pass that flag, and then PROVE it by pasting the front matter afterwards.
  - Depends on: E-01
  - Expected outcome: `x7wfyx` is `graduated` with its `- Blocks-Release: next` intact, and its history entry names both halves BY CONTENT (B delivered via the `host_truncation` signal, A outstanding), not merely by letter; pasted command output plus the item's front matter showing the gate still present.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR HOLDS ORCHESTRATION, NOT WORK OF ITS OWN, and the remedy for a parent carrying uncovered work is to ADD A CHILD, never to delete the parent's items: that checklist is what makes a hand-run `execute <setid>` complete when no runner is involved (`AGENTS.md`). This plan adds coverage and changes nothing on `s0gnha` except its child table.
- THE CLOSE-LEGITIMACY GATE IS REAL AND FAILS CLOSED IN GENERAL, AND IS ALREADY SATISFIED FOR THIS SET'S ITEM, which is a different thing and is the distinction that matters here. `aw backlog set done` on an item carrying `- Blocks-Release:` refuses unless the gate is preserved via a `From-Backlog` handoff, released via a cited in-tree `--evidence`, or explicitly cleared with `--blocks-release -`; one shared predicate (`check_engine.evaluate_blocking_close`) backs the setter, the `aw check` rules and the opt-in hook, so they cannot diverge (`AGENTS.md`). BUT the routes are checked in order and HANDOFF comes first, so an item with an existing `From-Backlog` carrier is ALREADY legitimate before any evidence is offered. Measured for `yxfw4k`: four carriers, verdict legitimate with `evidence=None` (F-05). So for this plan the gate is not a safety net, and E-02 says so rather than relying on it.
- `graduated` MEANS THE DESIGN IS HANDED OFF; `done` MEANS THE CODE IS WRITTEN AND VALIDATED. That distinction is why E-03 refuses `done` for a partly-implemented item. NOTE the predicate checks only the `done` transition (and warns on `parked`), so `graduated` passes unexamined and nothing will notice a gate dropped on that route.
- EVERY LIVE BUG GATES THE NEXT RELEASE (`AGENTS.md`): an item whose `- Work-Kind:` is `bug` MUST carry `- Blocks-Release:` while it is `open`, `blocked` or `graduated`. Both items here are `Work-Kind: bug`, and `graduated` is LIVE, so E-03's refusal to drop `x7wfyx`'s gate is not merely prudent - keeping it is what the rule requires.
- A RELEASE GATE IS INHERITED, NOT RE-DECIDED PER CHILD (`AGENTS.md`): a plan graduating from a backlog item inherits its `Blocks-Release`. The parent and `svacmz` both carry `From-Backlog: yxfw4k` with `Blocks-Release: next`, so this plan does too (F-08).
- A RECEIPT CHECK IS BOUNDED BY THE CHECKED PLAN'S CURRENT TEXT, not by a paraphrase of it. `svacmz`'s `V-01`/`V-02` bars were both CHANGED by its 2026-09-19 review, so E-01 quotes that plan's live wording (F-06). A receipt check written against a stale summary silently lowers the bar it exists to enforce.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH | `runner_shared` symbol `run_orchestrator_probe_gate`, event `orchestrator-probe-gate`; `runner_shared.evaluate_set_retirement` run at HEAD `73e370ae` | The coverage probe refused a 34-set launch naming `s0gnha` among five uncovered parents. Without this child, E-02 and E-03 are reported complete having never been performed. RE-VERIFIED IN CODE rather than from the run log, which is gitignored and absent from a lane: `evaluate_set_retirement(repo, 'reaskscore')` returns `eligible=False`, `reason=unfinished-children`, `detail="Set 'reaskscore' has 3 child(ren) that are not 'executed': dy9ymn (approved), svacmz (approved), p9j6c0 (to-review)"`. |
| F-02 | HIGH | `s0gnha` E-03, quoted; both items' front matter, re-read at HEAD `73e370ae` | E-03 is the release-gate-bearing half and the parent calls it "the one substantive act that belongs on this plan because it is a Set-level record change no child owns". VERIFIED EXACTLY: `yxfw4k` is `graduated` (`Work-Kind: bug`, `Priority: high`) and `x7wfyx` is `open` (`Work-Kind: bug`, `Priority: medium`), and BOTH carry `- Blocks-Release: next`. Retirement would leave both untransitioned while the Set claimed completion. |
| F-03 | MEDIUM | `svacmz`'s child-table row, quoted | This Set was already PARTLY aware of the hazard: `svacmz` exists expressly so the verifications are "performed and verified by an agent turn instead of being retired unperformed". The gap it missed is the backlog transition, which is exactly what F-02 names. |
| F-04 | MEDIUM | `s0gnha` E-01, quoted | The parent's E-01 is dispatch ordering, which a runner performs by construction. It is deliberately NOT lifted into this plan: an agent cannot meaningfully "perform" the queue order, and claiming to would be theatre. |
| F-05 | BLOCKER | `check_engine.evaluate_blocking_close(repo, yxfw4k, "done", evidence=None)` run at HEAD `73e370ae` -> `legitimate=True`, route `HANDOFF`, "gate 'next' handed off to a From-Backlog plan or spec"; `check_engine.find_from_backlog_artifacts(repo, "yxfw4k")` -> four plans (`skn8uk`, `ty7w6o`, `s0gnha`, `svacmz`), each `Blocks-Release: next` | E-02'S CENTRAL SAFETY CLAIM IS FALSE FOR THIS ITEM. It asserted that `aw backlog set done yxfw4k` "FAILS CLOSED unless the gate is provably preserved or released". It does not: the predicate checks HANDOFF before SATISFIED, four plans already carry `From-Backlog: yxfw4k` with the same gate, so the close is legitimate with NO evidence argument whatsoever. The plan therefore rested its most dangerous step on a tool refusal that will not arrive, and two of the four handoff carriers (`s0gnha`, `svacmz`) are themselves still `approved` in `pending/`, so the gate is preserved by plans that have not run. An executor trusting the stated fail-closed behavior could close a release-blocking bug on absent evidence and see exit 0. |
| F-06 | HIGH | `svacmz`'s `V-01` and `V-02` text at HEAD `73e370ae`; that plan's 2026-09-19 review history entry | THIS PLAN'S RECEIPT-CHECK BAR WAS WEAKER THAN THE BAR IT CHECKS, in the exact place `svacmz`'s own review closed a hole. E-01 asked for "the five shared constants' ACTUAL VALUES"; `svacmz`'s `V-01` demands EIGHT definition sites across three files and says in terms that "a paste covering only five sites" FAILS, because two names are multiply defined and the omitted third `TERMINAL_STATES` copy is the one `reconcile_disposition` reads. Accepting five here would launder that hole. Separately, E-01 demanded "the `git diff` for both pin files" while `svacmz`'s `V-02` was re-expressed at ASSERTION level after its review measured the empty-diff bar already unsatisfiable (3 insertions / 2 deletions from `eee6f427`, zero assertion lines), so this plan would have manufactured a failure its owner ruled out. A receipt check must quote the owner's current bar, not a paraphrase. |
| F-07 | HIGH | `oc_runipd.dependency_status_detailed` on `{'dependencies': ['executed:svacmz']}` at HEAD `73e370ae` -> unsatisfied, "external target svacmz is 'approved' (directory 'pending'), needs one of ['executed']" | THE PLAN IS NOT RUNNABLE AT REVIEW HEAD, and its own text did not say so. `svacmz` is `approved`, not `executed`, so a run marks this item `dependency-blocked`; and `dy9ymn` is also outstanding, so TWO siblings must execute first, not one. This is not a defect in the plan (the runner owns ordering and re-checks edges at dispatch) but it is decision-relevant in one way the plan missed: E-01 is a receipt check over evidence that does not exist yet, so executed today it can only take its failure path. Stated in the Concern so an executor is not surprised, and so a reader does not mistake the expected upstream failure for this plan malfunctioning. |
| F-08 | MEDIUM | This plan's front matter against `s0gnha`'s and `svacmz`'s (`From-Backlog: yxfw4k`, `Blocks-Release: next`); `AGENTS.md` release-gate contract | THE SET'S RELEASE GATE DIED AT ITS CLOSING CHILD. The parent and `svacmz` both carry `From-Backlog: yxfw4k` and `Blocks-Release: next`; this plan carried neither, so the ONE plan whose whole job is to discharge two release-blocking items honestly did not itself declare the gate, and `aw attention`'s release-blocker set could not see it. Worse here than in the ordinary case: this plan's own E-02/E-03 are the acts that decide whether those gates survive. |

## Proposed changes (ordered, validatable)

1. Receipt-check `svacmz`'s four validation items against that plan's CURRENT bars, and report any empty
   evidence block (E-01).
2. Close `yxfw4k` with `--evidence` citing `svacmz`, without clearing its gate, knowing the predicate will
   report HANDOFF and will not refuse on absent evidence (E-02).
3. Graduate `x7wfyx` with its release gate intact, naming both halves by content (E-03).

## Deferred / out of scope (with reason)

- `s0gnha` E-01, THE DISPATCH ORDERING. A runner enforces it by construction (dependency depth is the
  first sort key and edges are re-checked at dispatch), so there is no agent act to perform. See F-04.
  - Carrier-Declined: NOT AN OBLIGATION ANY RECORD CAN HOLD, because it is not work. Dispatch order is a
    property the runner computes at queue build and re-checks at dispatch; there is no artifact a carrier
    could point at and no future agent who should "do" it. Filing one would create an item whose only
    correct resolution is to close it unperformed.
- RE-PERFORMING `svacmz`'s VERIFICATIONS. It owns them; duplicating them here would place the same
  assertions in two files with no second observer, which is the parent's own stated reason for making
  E-02 a receipt check.
  - Carrier: svacmz
- ANY PRODUCT CODE CHANGE. The three children delivered the code; this plan closes the records.
  - Carrier-Declined: AN EXCLUSION, NOT A DEFERRAL. This plan's entire purpose is to transition records
    honestly, and a product change here would be the defect rather than the deliverable (the parent's own
    fence says the same). Nothing is outstanding: `skn8uk` and `ty7w6o` are executed, `dy9ymn` and `svacmz`
    are approved and carry the remaining code and proof, and `x7wfyx` item A remains gated on the item
    itself, which E-03 keeps live precisely so it is not lost.

## Scope check

- Over-scope: none. All four declared paths are used and necessary: the plan's own file under
  `plans/pending`, and three backlog directories because `aw backlog set` MOVES an item between them
  (`yxfw4k` leaves `graduated/` for `done/`, `x7wfyx` leaves `open/` for `graduated/`). Verified at review
  HEAD that each item is where the fence expects it.
- Under-scope: none, and the one apparent gap is deliberate: the parent carries three `E-*` items and this
  plan covers two. E-01 (dispatch order) is excluded with its reason stated in F-04 and in the deferral
  list, rather than silently dropped.

## Required tests / validation

No product code changes, so no new unit test, and no behavior-affecting test should move. V-01 requires a
bare `python3 -m pytest` on the merged result, which is one of the Set's own completion criteria and must be
pasted rather than asserted. BARE MEANS BARE: `pyproject.toml` `addopts` already supplies
`-q -n auto --dist=worksteal -m 'not slow'`, so do not add `-n0`, a second `-q`, or `-p no:randomly`.

BASELINE IS A MEASUREMENT, NOT A CONSTANT: take your own count at your own HEAD rather than comparing
against a number written in any plan. AND ONE PRE-EXISTING FAILURE IS NOT YOURS: at review HEAD `73e370ae`,
`tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`
fails, and it fails identically with this review's changes reverted (it asserts on the inherited process
environment). Re-check it against a clean HEAD before attributing it to your work, and report it as
pre-existing if still red rather than claiming a regression or a clean run you did not get.

## Spec / documentation sync

N/A. This plan changes no contract, and it changes no product code, so no spec text moves. The only
structural plan edit is the child-table row on `s0gnha`, which is what the coverage gate reads and which
already exists by the time this runs. The two backlog items' front matter changes are the plan's DELIVERABLE
rather than incidental record sync, and E-02/E-03 own them.

## Open questions

### OQ-01: If `svacmz`'s evidence is absent, may this plan close `yxfw4k` anyway on its own reading of the code?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO - REPORT THE UPSTREAM FAILURE AND LEAVE THE ITEM OPEN. Resolved from the parent's own wording rather than deferred: `s0gnha` E-03 makes the close CONDITIONAL ("only if its defect is fixed AND validated by `svacmz`'s evidence"), so absent evidence means the precondition is unmet, not that a substitute is needed. Closing a release-blocking item on the verifier's own re-reading would defeat the point of having an independent validator and would discharge a `Blocks-Release: next` gate on weaker grounds than the gate demands. E-01's expected outcome already requires naming which evidence block was empty, which makes the refusal auditable.
  THIS QUESTION IS NOW LOAD-BEARING RATHER THAN HYPOTHETICAL, and its answer is the only thing enforcing itself. Measured at review HEAD `73e370ae`: `svacmz` is `approved` in `pending/` with all four `Observed evidence` blocks EMPTY and all four `Result: pending`, so the absent-evidence case this question asks about is the CURRENT state of the world, not an edge case. And the tool will not back the answer up: `check_engine.evaluate_blocking_close(repo, yxfw4k, "done", evidence=None)` returns LEGITIMATE via route HANDOFF, because four plans already carry `From-Backlog: yxfw4k` with the same gate (F-05). So `aw backlog set done yxfw4k` will EXIT 0 on absent evidence. The refusal this question mandates is therefore entirely the executor's act, with no gate behind it, which is why E-01's failure path and V-02's cross-check both name it explicitly.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: for each of `svacmz`'s `V-01`..`V-04`, quote the evidence line that satisfies it, AGAINST THAT PLAN'S CURRENT BAR rather than a paraphrase: for `V-01` the EIGHT definition sites' actual values (not five - that plan's own text says a five-site paste FAILS) plus the three `TERMINAL_STATES` copies shown mutually equal and `EXECUTE_REPORTING_SUCCESS_STATES` shown still equal to `SUCCESS_STATES - {"reviewed"}` as a derivation; for `V-02` the pin output plus the ASSERTION-LEVEL attribution for each changed line in both pin files (a demand for a CLEAN `git diff` is wrong and that plan's review measured it unsatisfiable); for `V-03`/`V-04` the SHAPE A / SHAPE B output, the per-item retry counter values, and the collision case. A statement that they "carry evidence" without quoting it FAILS this item, and so does accepting a five-site `V-01` paste. Plus the bare `python3 -m pytest` summary line on the merged result.
    A REPORTED UPSTREAM FAILURE IS A PASS FOR THIS ITEM, not a failure to work around, and at review HEAD it is the expected outcome (all four blocks empty). Naming which blocks were empty, and leaving both backlog items untransitioned, SATISFIES this item. Quietly running `svacmz`'s checks yourself and reporting them as its evidence FAILS it.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `aw backlog set done yxfw4k ...` output showing it SUCCEEDED, plus the `--evidence` citation used, plus the item's resulting front matter, plus the ROUTE the close-legitimacy predicate reported. THREE FAILURE CONDITIONS. An execution that reached success by passing `--blocks-release -` FAILS this item even though the command exited 0, because that discharges a release blocker by deleting the gate. A close performed while E-01 reported absent evidence FAILS it, and the tool WILL NOT CATCH THIS: the predicate returns legitimate via HANDOFF with no evidence at all (F-05), so exit 0 is not proof of legitimacy here and must not be offered as such. And an evidence block asserting the SATISFIED route FAILS as a misreading: HANDOFF is checked first and is what this item will report, which is why the route must be stated rather than assumed.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `aw backlog set graduated x7wfyx ...` output, plus the item's front matter AFTER the transition showing `- Blocks-Release: next` STILL PRESENT, plus the history message quoted showing it names BOTH halves by content: item B delivered (a zero-work turn is now retryable, its trigger recorded as `attempt["host_truncation"]` by `ty7w6o` and consumed by `dy9ymn`) and item A outstanding (the agent is still not told its remaining turn budget). A transition to `done` FAILS this item. A transition that cleared the gate FAILS it, and note nothing will refuse that for you: the predicate gates only `done`, so `graduated` passes unexamined and the pasted front matter is the ONLY proof the gate survived. A history message naming the halves only by letter ("item B done, item A not") FAILS, because a later reader cannot check a letter.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY files this plan changed, path-scoped; never `git add -A`; never push.
When reporting tests passed, paste the ACTUAL runner output. Do NOT mark an `E-*` item performed for work
not done, and do NOT fill a `V-*` `Observed evidence` block with anything but observed output.

THE HONESTY RULE THAT MATTERS MOST HERE concerns the two backlog transitions, because both items carry
`Blocks-Release: next`, both are `Work-Kind: bug`, and both are therefore easy to "finish" dishonestly.
Three specific moves are forbidden: closing `yxfw4k` by clearing its gate with `--blocks-release -` (that
deletes a release blocker rather than discharging it), recording `x7wfyx` as `done` when only its item B was
implemented (that asserts delivery of work nobody did), and dropping `x7wfyx`'s gate on the `graduated`
route, which nothing checks. If `svacmz`'s evidence is absent, the correct outcome is a reported upstream
failure with both items left as they are.

AND THE CRITICAL CORRECTION TO THE ABOVE, added at review because the plan was relying on a refusal that
does not come: THERE IS NO TOOL GATE BEHIND THE FIRST OF THOSE RULES. The plan formerly said the setter
"stops refusing" once the gate is cleared, implying it refuses beforehand. Measured at HEAD `73e370ae`,
`check_engine.evaluate_blocking_close(repo, yxfw4k, "done", evidence=None)` returns LEGITIMATE via route
HANDOFF, because four plans carry `From-Backlog: yxfw4k` with the same gate - two of which (`s0gnha`,
`svacmz`) have not themselves executed. So `aw backlog set done yxfw4k` exits 0 on absent evidence, with no
flag passed and no warning printed. EXIT 0 IS NOT EVIDENCE OF LEGITIMACY FOR THIS ITEM, and the only
enforcement of OQ-01's answer is E-01's receipt check plus the executor's honesty. Treat a green command as
proving nothing here, and say in V-02 which route the predicate reported.

RUN ORDER, so nobody hand-runs this plan too early. Its `executed:svacmz` edge is UNSATISFIED at review HEAD
(`svacmz` is `approved`), and `dy9ymn` is outstanding too, so `runner_shared.evaluate_set_retirement` reports
three unfinished children. The runner handles this by construction - dependency depth is its first sort key
and edges are re-checked at dispatch, so an early dispatch marks this item `dependency-blocked` and continues
rather than failing the run - and there is nothing for a plan author to fix. The order is `dy9ymn` ->
`svacmz` -> this plan. A HAND-RUN executor, who has no such protection, must confirm `svacmz` reads
`Status: executed` before starting E-01; otherwise E-01 can only take its failure path.

SCOPE FENCE. Touch ONLY the paths in `- Scope-Paths:`. Change NO product code, and do not edit `s0gnha`
beyond the child-table row that already exists by the time this runs. If the work genuinely requires a path
outside the fence, make the edit and justify it, since `aw ipd finalize` refuses to complete until every
out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

POST-GATE LIFECYCLE. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` item
must carry observed evidence before the plan moves to `.aw/records/plans/executed/`. The runner owns the
terminal transition; a worker-role process is refused by `AW-LIFECYCLE-ROLE-001`.
