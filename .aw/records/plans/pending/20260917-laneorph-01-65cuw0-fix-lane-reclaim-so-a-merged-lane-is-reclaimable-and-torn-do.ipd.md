# IPD: Fix lane reclaim so a merged lane is reclaimable and torn down

- Date: 2026-09-17
- Kind: child
- Concern: `LaneState.reclaimable` refuses a lane whose work is fully merged, so the INTERRUPT-path reclaimer leaves it alone forever. `worktree_lease.inspect_lane` computes `commits_ahead` as `rev-list --count <the lane's OWN base>..<head>` (`worktree_lease.py:308-314`), then sets `LANE_HOLDS_WORK` whenever that is non-zero (`:321`), and `reclaimable` requires `state in (LANE_EMPTY, LANE_STALE)` AND `commits_ahead == 0` (`:193-199`). So a merged lane stays HOLDS-WORK and non-reclaimable permanently. MEASURED 2026-09-17: six lanes (`3dki3o`, `51vw4y`, `orziju`, `s16omw`, `ty3cj6`, `yrqyxb`) each reported `HOLDS-WORK` with 4-6 `commits_ahead` while `merge-base --is-ancestor <branch> main` returned 0; re-confirmed merged at review HEAD `f741596e`. TWO CORRECTIONS APPLIED AT REVIEW 2026-09-18, because the original Concern misattributed the leak. FIRST, `reclaimable` IS NOT WHAT LEAKS A SUCCESSFUL RUN'S WORKTREE: it is read at exactly two call sites (`oc_runipd.py:2337`, `agy_runipd.py:1292`), BOTH inside `reclaim_lanes_on_interrupt`, so its blast radius is the interrupt path ALONE. The end-of-run teardown is a different call, `lane_containment.teardown_lane_if_classified` (`oc_runipd.py:7881`, `agy_runipd.py:4430`, both inside the `fin_rc == 0` success branch), and it consults the spec R5.5 INVENTORY, never `reclaimable`. What actually refuses it is an unaccounted gitignored file, which is plan `5w8g8j`'s subject. SECOND, `aw attention` ALREADY EXCLUDES A MERGED LANE (see the deleted E-04 and the Findings table), so that half was already-shipped work.
- Scope: Make the INTERRUPT-path reclaim reading honor merged-ness: add a merged-ness reading to `LaneState` REUSING the existing `runner_shared.lane_work_has_landed` predicate, and make `reclaimable` accept a merged, non-dirty lane so `reclaim_lanes_on_interrupt` can reclaim it. Does NOT change what `commits_ahead` MEANS: that figure is still the correct input to the lane-REUSE question (`LANE_EMPTY`/`LANE_STALE`/`LANE_FOREIGN` decide whether a lane can be adopted for a fresh execution), so this adds a separate predicate rather than redefining an existing one. EXPLICITLY NOT IN SCOPE, both removed at review as already-shipped or as another plan's: the end-of-run teardown call site (already wired; refuses on the R5.5 inventory, which is `5w8g8j`'s) and the `aw attention` merged-lane exclusion (already implemented).
- Scope-Paths: agent_workflows/worktree_lease.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_worktree_lease_merged_reclaim.py
- Item-Dependencies: executed:5w8g8j
- Status: reviewed
- Blocks-Release: next
- Readiness: go-pending-approval
- From-Backlog: a58s04
- Set: laneorph
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 65cuw0

## Workflow history
- 2026-09-18 reviewed (aw set): status set to reviewed
- 2026-09-18 reviewed (aw set): plan-review round 3 complete: APPROVE WITH REVISIONS APPLIED. Maintainer resolved OQ-03, OQ-04, and OQ-05. PR-101 and PR-103 marked FIXED. Proceed with decision-order change in reclaim_lanes_on_interrupt so merged lanes are checked before holds_work bails out. Deleting the branch of a provably-merged lane on interrupt is safe and standard Git hygiene since all commits are in main. Readiness go-pending-approval.

- 2026-09-18 /plan-review round 2 (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-101..PR-107; readiness `no-go` on TWO new blocking findings. Reviewed at HEAD `2046a27a`, the commit that merged round 1's revisions, with the plan byte-identical to the lane input. THIS ROUND REVIEWED ROUND 1's OWN REVISION AND FOUND THREE DEFECTS IN IT, each measured by RUNNING the prescribed design rather than reading it. PR-101 BLOCKER, THE RETARGETED PLAN IS INERT: the interrupt loop tests `if lane["holds_work"]:` and `continue`s (`oc_runipd.py:2287`, `agy_runipd.py:1242`) BEFORE it reads `reclaimable` (`:2337`, `:1292`), and a merged lane is STILL `holds_work` because `commits_ahead > 0` (`worktree_lease.py:189-190`); measured on a real merged lane, `state HOLDS-WORK, commits_ahead 1, holds_work True, reclaimable False, is-ancestor(->main) rc=0`, so E-01+E-02 change a reading nothing consults and an executor would ship a green unit suite that reclaims nothing. E-03 now owns a DECISION-ORDER change, which is a behavior change to a shared control path. PR-102 BLOCKER, FIXED: round 1 told the executor to gate `reclaimable` on `lane_containment.inventory_lane(...).classified`, but `submission_retention` returns `uncollected=True` when `run_dir`/`item` is None (`lane_containment.py:3075-3080`) and `classified` requires `not uncollected_submission` (`:3104-3107`), so measured on a PERFECTLY CLEAN lane the result is `classified FALSE, reason_codes ('uncollected-submission',)`; since `inspect_lane` has no such parameter (`worktree_lease.py:258-263`), the prescribed call would have made EVERY lane non-reclaimable and regressed today's `LANE_EMPTY`/`LANE_STALE` reclaim. The inventory moves to the CALL SITE, which already holds `run_dir` and the item records (`oc_runipd.py:2226-2260`) and which also respects `worktree_lease`'s documented no-package-imports rule (`:49-52`). PR-103 BLOCKER, round 1's V-03 WAS UNSATISFIABLE: it required the lane branch to survive, but the gate's default remover is `teardown_isolation_worktree` -> `teardown_worktree(force=True)` -> `git branch -D` (`lane_containment.py:3329`, `runner_shared.py:1004-1012`, `worktree_lease.py:701`); measured, `torn_down True` then `rev-parse --verify` **rc=128** with reflog "unknown revision". Also fixed: E-05 asked for zero force-teardown callers when there are FOUR, two legitimate and one the gate's own remover (PR-104); `Scope-Paths` omitted `oc_runipd.py` and `agy_runipd.py` although E-03 edits both, which would have made finalize refuse (PR-105); `reclaimable`'s "safe to tear down" docstring becomes false once it admits a merged lane (PR-106); and the `worktree_lease` layering rule was quoted with the measurement that a function-local import resolves in both orders (PR-107). E-04 split into a reading layer and a BEHAVIOR layer, and V-04 now requires a failure demonstration against an E-01+E-02-only build, because that is the false green this round measured. Findings recorded under this plan's own id6 in `.aw/records/reviews/20260917-laneorph-01-65cuw0-...review.md`, since `subject_gating_blocks(repo, "65cuw0")` returned `()` before it and round 1's blockers therefore gated nothing here. OQ-04 (accept the enlarged scope) and OQ-05 (how to keep the ref) raised `Blocking: yes` carrying PR-101 and PR-103.

- 2026-09-18 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; reviewed as part of orchestrator `tb63qv`'s Set (findings PR-001..PR-009 recorded there and in `.aw/records/reviews/20260917-laneorph-00-tb63qv-...review.md`); readiness `no-go`. RETARGETED, because BOTH authored deliverables dissolved on measurement. The authored E-03 (tear the lane down at the end of a successful integration) asks for a call site that ALREADY EXISTS on both hosts, `lane_containment.teardown_lane_if_classified` (`oc_runipd.py:7881`, `agy_runipd.py:4430`, AST-confirmed inside the `fin_rc == 0` success branch), which gates on the spec R5.5 INVENTORY and never on `reclaimable`; and the authored E-04 (stop `aw attention` calling a merged lane stranded) asks for behavior that ALREADY SHIPS (`runner_shared.py:1063-1068`, `:1110-1180`; measured 12/12 reported lanes not ancestors of `main`, and 0/6 merged lanes reported). `reclaimable`'s only two readers are inside `reclaim_lanes_on_interrupt`, so this plan's real blast radius is the INTERRUPT path; `attention.py` was dropped from `Scope-Paths` and `executed:5w8g8j` declared, since the leak this plan's Concern describes belongs to `5w8g8j`. THE MOST SERIOUS FINDING (PR-003) IS FIXED IN PLACE: the authored E-02 would have CAUSED DATA LOSS. `dirty` is a plain `git status --porcelain` blind to IGNORED files (`worktree_lease.py:316-319` vs `lane_containment.py:2814-2819`); `reclaimable` gates `teardown_worktree(force=True)`, which DELETES THE LANE BRANCH and empties its reflog; and git's refusal, which the plan named as its second backstop, does NOT fire for an ignored file. MEASURED, git 2.43.0, real worktree whose only unexplained content was one ignored file: plain porcelain `''`, `--ignored=traditional` `!! ig/precious.txt`, `git worktree remove` with NO `--force` exit **0**, file DELETED; the same probe with an UNTRACKED file exit 128, file preserved. So E-02 now requires `lane_containment.inventory_lane(...).classified` (fail-toward-preservation when unreadable), E-03 routes the interrupt teardown through `teardown_lane_if_classified` (removing a pre-existing force-delete hazard), E-04 makes the merged-plus-IGNORED-only case the discriminating assertion, and new E-05 pins the no-force-teardown invariant by AST. PR-004 fixed by DELEGATING E-01 to the existing `lane_work_has_landed` rather than adding a second `--is-ancestor` call (R6.1), handling its three-valued return honestly and noting the circular-import trap; OQ-01 now adopts the repository's existing `LANE_INTEGRATION_TARGET_FALLBACK = "HEAD"` (`:1074`) instead of inventing a default. Spec-sync rewritten: `7ckptx` (approved) R5.5/R6.1 DO govern, no amendment is declared because the corrected plan complies, and narrowing R5.5 is a stop-and-ask since `5w8g8j` is already blocked on exactly that. OQ-03 raised `Blocking: yes` carrying PR-001.

- 2026-09-18 reviewed (aw set): plan-review complete (reviewed as part of orchestrator tb63qv's Set): REVIEWED - OPEN QUESTIONS; retargeted to the interrupt path after PR-001 refuted both authored deliverables (E-03's end-of-run teardown already exists and gates on the R5.5 inventory; E-04's attention exclusion already ships); PR-003 FIXED, the authored E-02 would have force-deleted a merged lane holding only an unaccounted IGNORED file since dirty cannot see one and git worktree remove does not refuse for one (measured, exit 0, file deleted); E-02 now consumes inventory_lane().classified and E-03 routes teardown through teardown_lane_if_classified; PR-004 FIXED by delegating to lane_work_has_landed; executed:5w8g8j declared; readiness no-go
- 2026-09-17 to-review (aw set): Authored 2026-09-17 from a measured sweep of .aw/worktrees/ (38 worktrees/4.7G, 28 provably merged and clean) and of the 13 lane branches holding 76 unmerged commits; complete enough to critique

- 2026-09-17 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Make an INTERRUPTED run reclaim a lane whose work is already merged, instead of preserving it forever, and
do so through the one teardown gate so nothing unaccounted is destroyed.

THE GOAL AS AUTHORED CLAIMED TWO THINGS THIS PLAN DOES NOT DELIVER, both struck at review 2026-09-18 with
the evidence in the Concern and Findings. It does NOT stop `.aw/worktrees/` growing on SUCCESSFUL runs
(that path is already wired and gated on the R5.5 inventory; the leak is plan `5w8g8j`'s), and there is NO
stranded-lane signal loss to repair: `aw attention` already excludes a merged lane, measured at review as
12 reported lanes of which 12 were provably unmerged, zero false positives, and the six lanes this plan
names as merged reported zero times (F-5). The 4.7G figure is real but is not this plan's to recover.

WHAT THIS PLAN IS ACTUALLY WORTH, stated plainly so an approver is not buying the paragraph above: on the
interrupt path a merged lane is preserved forever, and when a lane IS reclaimed there its branch is
force-deleted with an emptied reflog. The second is a data-safety defect that the authored plan did not
notice and that round 2 measured; it is arguably the more valuable half.

NON-GOAL, stated because it is the tempting shortcut and it destroys work: teardown must NOT be keyed
on merged-ness alone. UNTRACKED files are invisible to every merged-ness test. Measured in the same
sweep, lane `wfamig` was fully merged and held an untracked 89-line plan
(`.aw/records/plans/pending/20260917-revladder-01-i4ak5n-...ipd.md`) that existed NOWHERE in `main`; a
merged-ness-only teardown would have deleted the only copy. (The plan `i4ak5n` is now committed in
`main`'s `pending/`, verified at review HEAD, so the specific file is no longer at risk; the HAZARD CLASS
is unchanged and is what the rule protects.)

THE `dirty` FIELD DOES NOT CLOSE THAT HAZARD, AND THE GOAL AS AUTHORED WAS WRONG TO ASSUME IT DOES. This
is the single most important correction from review, because the original E-02/E-03 pairing would have
caused data loss. THREE MEASURED FACTS, each independently verifiable:

1. `LaneState.dirty` comes from a PLAIN `git status --porcelain` (`worktree_lease.py:316-319`), which
   reports untracked files but is BLIND TO IGNORED ONES. Spec `7ckptx` R5.5 requires the enumeration to
   include ignored files and names "ignored means disposable" as the reasoning that previously destroyed
   lane content silently; `lane_containment.LANE_INVENTORY_STATUS_ARGS` therefore passes
   `--ignored=traditional`, and `inspect_lane` does not.
2. `reclaimable` GATES A `force=True` TEARDOWN THAT DELETES THE BRANCH. Both call sites read
   `if not lane["reclaimable"]: continue` and then call
   `worktree_lease.teardown_worktree(repo, handle, force=True)` (`oc_runipd.py:2337-2345`,
   `agy_runipd.py:1292-1300`). That function's own docstring records the measurement: the branch is gone,
   its reflog is EMPTY, the commits survive only as unreferenced objects, and `--force` destroys
   uncommitted files from git AND disk. `--force` is passed by the CALLER, so Order 01 cannot make it
   safe by choosing a flag; widening the predicate widens what gets force-deleted.
3. GIT'S REFUSAL IS NOT THE BACKSTOP THE PLAN CLAIMED. Measured at review with git 2.43.0, on a real
   worktree whose only unexplained content was ONE IGNORED file: plain `git status --porcelain` printed
   nothing, `--ignored=traditional` printed `!! ig/precious.txt`, and `git worktree remove` WITHOUT
   `--force` exited **0** and DELETED the file. The refusal fires for an UNTRACKED file (exit 128,
   "contains modified or untracked files") but NOT for an ignored one.

Taken together: a merged lane holding only an unaccounted IGNORED file reads `dirty=False`, would become
`reclaimable=True` under the authored E-02, and would be force-deleted branch-and-all on the next
interrupt. That is the exact failure spec R5.5 exists to prevent. E-02 is therefore rewritten to consume
the R5.5 inventory rather than `dirty`, and E-03 is replaced by a wiring item that routes the interrupt
teardown through the one shared gate so no second teardown path exists (R6.1).

THREE FURTHER DEFECTS FOUND IN ROUND 2 (2026-09-18), EACH IN THE ROUND-1 REVISION ITSELF, and each
MEASURED by running the prescribed design rather than reading it. They are recorded here because two of
them made the plan inert or unsatisfiable, which no amount of careful execution would have fixed.

4. WIDENING `reclaimable` ALONE IS INERT: `holds_work` INTERCEPTS A MERGED LANE FIRST. The interrupt loop
   tests `if lane["holds_work"]:` and `continue`s (`oc_runipd.py:2287`, `agy_runipd.py:1242`) BEFORE it
   ever reads `reclaimable` (`:2337`, `:1292`). `holds_work` is `state == LANE_HOLDS_WORK`
   (`worktree_lease.py:189-190`) and a merged lane still has `commits_ahead > 0`, so it is HOLDS-WORK.
   Measured on a real lane cut from an older base, committed, then `--no-ff` merged to `main`:

   ```text
                         BEFORE MERGE        AFTER MERGE
   state              : HOLDS-WORK          HOLDS-WORK
   commits_ahead      : 1                   1
   holds_work         : True                True
   reclaimable        : False               False
   is-ancestor(->main): no (rc=1)           YES MERGED (rc=0)
   ```

   So the merged lane takes the `holds_work` branch, is PRESERVED, and `reclaimable` is never consulted.
   E-03 must therefore change the DECISION ORDER (consult merged-ness before the `holds_work` bail-out),
   not merely the predicate; E-02 alone changes nothing observable, which is why V-02 is now explicitly
   an internal-reading check and V-03 owns the behavior claim.
5. `inventory_lane` WITHOUT A RUN DIRECTORY AND ITEM REPORTS EVERY LANE UNCLASSIFIABLE, so the round-1
   E-02 (calling it from `inspect_lane`) would have made EVERY lane permanently non-reclaimable, breaking
   the existing `LANE_EMPTY`/`LANE_STALE` reclaim too. `submission_retention` returns `uncollected=True`
   with detail "no run directory or item was supplied" when either is None (`lane_containment.py:3075-3080`),
   and `classified` requires `not uncollected_submission` (`:3104-3107`). Measured on a PERFECTLY CLEAN
   lane (empty porcelain, empty `--ignored=traditional`):

   ```text
   inventory_lane(lane_root=<clean lane>, run_dir=None, item=None)
     readable True   dirty_tracked ()   unknown_untracked ()   unknown_ignored ()
     uncollected_submission True   classified FALSE   reason_codes ('uncollected-submission',)
   ```

   And `inspect_lane(repo_root, lane_id, *, base_commit)` has NO `run_dir`/`item` parameter and no way to
   obtain one (`worktree_lease.py:258-263`). THE FIX IS A LAYERING ONE: the inventory check belongs at the
   CALL SITE, `reclaim_lanes_on_interrupt`, which already holds `run_dir` and the per-item records
   (`oc_runipd.py:2226-2260`), not inside `LaneState`. E-02 is rescoped accordingly.
6. THE SHARED TEARDOWN GATE DELETES THE BRANCH TOO, so round-1's V-03 was unsatisfiable as written.
   `teardown_lane_if_classified`'s default remover is `runner_shared.teardown_isolation_worktree`
   (`lane_containment.py:3329`), which calls `worktree_lease.teardown_worktree(force=True)`
   (`runner_shared.py:1004-1012`), which ends with `git branch -D` (`worktree_lease.py:701`). Measured,
   driving the gate to authorize a teardown:

   ```text
   torn_down True   worktree exists after False
   BRANCH SURVIVES after: False (rc=128)
   reflog after: "fatal: ambiguous argument 'aw/lane/demo02': unknown revision"
   ```

   So routing through the gate makes teardown SAFE (it refuses on unclassifiable content) but does NOT by
   itself preserve the ref. Keeping the branch is a SEPARATE requirement, and OQ-02's answer ("never delete
   the ref") needs its own mechanism: the gate must be given a non-deleting remover, or the ref must be
   re-created, or OQ-02's answer must be revised. That choice is OQ-05, blocking.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Make merged-ness a first-class reading

- [ ] E-01 Add a `merged_into_target` boolean to `worktree_lease.LaneState`, computed by DELEGATING to the existing `runner_shared.lane_work_has_landed(repo, branch, target=...)` rather than issuing a second `merge-base --is-ancestor` call, so the repository keeps ONE definition of "merged" (spec `7ckptx` R6.1). Record it ALONGSIDE `commits_ahead`; do not alter how `commits_ahead` is computed, since `LANE_STALE`/`LANE_FOREIGN` adoption logic reads it and changing its meaning would silently change which lanes are reused. HANDLE THE THREE-VALUED RESULT HONESTLY: `lane_work_has_landed` returns `True`/`False`/`None`, `None` meaning the question could not be answered; map `None` to NOT-merged (`False`) so an unanswerable lane is never treated as recovered, and state that choice in the field's docstring. CHECK THE IMPORT DIRECTION BEFORE WRITING: `runner_shared` imports `worktree_lease` (`runner_shared.py:810`) and not the reverse, so a module-level import back would be circular; use a function-local import, which is the pattern `runner_shared` itself uses, and say so.
  - Depends on: none
  - Expected outcome: `inspect_lane` on a merged lane returns `merged_into_target=True` while still reporting its real `commits_ahead`; on an unmerged lane and on an unanswerable one it returns False. No existing field changes value. No second `--is-ancestor` call is introduced anywhere.
  - Execution state: pending

- [ ] E-02 Make `LaneState.reclaimable` accept a MERGED lane in addition to today's `LANE_EMPTY`/`LANE_STALE` cases, keyed on E-01's `merged_into_target` AND on `dirty` being False. DO NOT call `lane_containment.inventory_lane` from here: round 2 measured that it reports EVERY lane unclassifiable when given no `run_dir`/`item` (Goal item 5), and `inspect_lane` has no such parameter, so doing it here would make even today's reclaimable lanes non-reclaimable. THE IGNORED-FILE HAZARD IS REAL AND IS NOT SOLVED BY THIS ITEM: it is solved at the CALL SITE by E-03's inventory gate, which is the only layer holding the run context the inventory needs. State that division of labour in the `reclaimable` docstring, and state plainly there that `reclaimable` is NECESSARY BUT NOT SUFFICIENT for teardown, so a future caller cannot read it as an authorization. Keep the `LANE_EMPTY`/`LANE_STALE` branch exactly as it is.
  - Depends on: E-01
  - Expected outcome: a merged, non-dirty lane reports `reclaimable=True`; a merged DIRTY lane stays False; an unmerged lane is unaffected; every lane that is reclaimable today still is. THIS ITEM CHANGES NO OBSERVABLE BEHAVIOR ON ITS OWN (see E-03): it changes a reading, and the docstring says so.
  - Execution state: pending

### Task group 2: Reclaim the merged lane through the one teardown gate

- [ ] E-03 Change the interrupt-path DECISION ORDER so a merged lane is reclaimed at all, and route that reclaim through `lane_containment.teardown_lane_if_classified`. THE ORDER IS THE LOAD-BEARING HALF, measured in round 2 (Goal item 4): the loop tests `if lane["holds_work"]:` and `continue`s (`oc_runipd.py:2287`, `agy_runipd.py:1242`) BEFORE it reads `reclaimable` (`:2337`, `:1292`), and a merged lane is STILL `holds_work` because `commits_ahead > 0`, so E-01 and E-02 alone are INERT. Consult merged-ness before the `holds_work` bail-out, so a merged lane reaches the reclaim branch. Then replace the direct `worktree_lease.teardown_worktree(repo, handle, force=True)` call with the shared gate, passing `run_dir` and the per-item record the function already holds (`oc_runipd.py:2226-2260`) so the inventory can actually read a receipt; on refusal, record it on the existing preservation event and leave the lane. PRESERVE the snapshot-then-preserve behavior for a lane that is NOT merged, and the operator `keep` prompt and `left-alone` disposition. Both hosts identically; no per-host rule.
  - Depends on: E-02
  - Expected outcome: an interrupted run whose lane is merged AND whose inventory is classified reclaims that lane; a merged lane holding unexplained content (including an IGNORED file) is preserved with its reason recorded; an UNMERGED lane still takes today's snapshot-and-preserve path unchanged; no code path reachable from `reclaim_lanes_on_interrupt` calls `teardown_worktree` with `force=True` directly.
  - Execution state: pending

### Task group 3: Guard the invariant

- [ ] E-04 Add `tests/test_worktree_lease_merged_reclaim.py` covering BOTH layers, since round 2 measured that the reading and the behavior are separable and that only the second is observable. LAYER 1 (the reading, E-01/E-02): build a real lane in a temp repo cut from an OLDER base, commit on it, merge it to the target, and assert `merged_into_target=True`, `reclaimable=True`, and `commits_ahead` still non-zero (proving the fix did not corrupt that figure); plus `merged_into_target=False` for an unmerged lane and for an UNANSWERABLE one (deleted branch), and `reclaimable=False` for a merged DIRTY lane; plus a regression assertion that a lane reclaimable TODAY still is. LAYER 2 (the behavior, E-03): drive `reclaim_lanes_on_interrupt` itself and assert the merged lane is RECLAIMED rather than preserved. THAT SECOND LAYER IS THE ONE THAT WOULD HAVE CAUGHT THE INERT FIX: a test of `reclaimable` alone passes while the interrupt path still preserves the lane via `holds_work`, which is exactly the false green round 2 measured. Add the IGNORED-file case at layer 2 (not layer 1, where the inventory is not consulted): an interrupted merged lane whose only unexplained content is a gitignored file must be PRESERVED, with its reason code recorded.
  - Depends on: E-03
  - Expected outcome: a test file whose layer-2 merged case FAILS against today's code and against an E-01+E-02-only implementation, and passes after E-03; with the ignored-file preservation pinned so a later change cannot reintroduce the destruction hazard.
  - Execution state: pending

- [ ] E-05 Assert the NO-DIRECT-FORCE-TEARDOWN invariant structurally, not by reading the diff: prove by AST or import-graph inspection that no call to `worktree_lease.teardown_worktree(..., force=True)` is reachable from `reclaim_lanes_on_interrupt` on either host, and that both hosts reach the shared gate. SCOPE THE ASSERTION HONESTLY, because round 2 found the repository holds FOUR force-teardown callers, not two: `oc_runipd.py:2345` and `agy_runipd.py:1300` (this plan's), `runner_shared.py:1012` (`teardown_isolation_worktree`, which the shared GATE itself calls and which must keep working), and `runner_shared.py:3934` (a no-files-changed cleanup this plan does not touch). So the assertion must be REACHABILITY-FROM-THE-INTERRUPT-PATH, never a repo-wide count of the string, or it will either fail against untouched code or forbid the gate its own remover. Follow the existing precedent for this style of proof (`lanectn` `4fodkt` established shared-rule assertions by AST rather than grep).
  - Depends on: E-03
  - Expected outcome: a pinned assertion that a future edit reintroducing a direct force-teardown ON THE INTERRUPT PATH fails a test, which does NOT fire for the three legitimate callers elsewhere, rather than relying on a reviewer noticing.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `worktree_lease.py` owns lane state as a NON-MUTATING reading (`inspect_lane`'s docstring); a fix
  belongs in that reading plus its consumers, not in a new parallel notion of lane health.
- `LaneState.reclaimable`'s docstring already states the safety rule this plan must preserve verbatim:
  "Provably empty: safe to tear down. NEVER true for a lane holding commits or dirty files." E-02
  widens "provably empty" to "provably recovered", and must not weaken the dirty half. NOTE the docstring
  says "safe to tear down", which round 2 showed is no longer true once the predicate admits a merged lane:
  the inventory, not this reading, is what makes teardown safe. E-02 must correct that sentence rather than
  leave a stale authorization claim in the codebase.
- Two drivers consume `lane["reclaimable"]` (`oc_runipd.py:2337`, `agy_runipd.py:1292`) through the
  shared `runner_shared` lane dict, so fixing the reading fixes both hosts at once. Do not add a
  per-host reclaim rule.
- `git worktree remove` refuses an UNTRACKED-dirty worktree unless `--force` is passed. CORRECTED AT
  REVIEW: it does NOT refuse for an IGNORED file (measured, F-11), so this refusal is a partial backstop
  and must not be presented as the safety mechanism. The R5.5 inventory is the mechanism.
- SPEC `7ckptx` R5.5 AND R6.1 BIND THIS PLAN. Teardown must be refused while a lane holds unclassifiable
  content (including an ignored file), and a multi-surface rule must live in one predicate. Both are
  reasons this plan CONSUMES `lane_containment.inventory_lane` / `teardown_lane_if_classified` and
  `runner_shared.lane_work_has_landed` rather than adding parallel logic.
- `reclaim_lanes_on_interrupt` is the ONLY consumer of `reclaimable`, so this plan's blast radius is the
  interrupt path. The successful-run teardown is a different, already-wired call (F-8, F-9).
- THAT CONSUMER GUARDS ON `holds_work` FIRST, and a merged lane satisfies it, so the predicate is not even
  reached for the case this plan is about (F-13). A reading change without a decision-order change is
  unobservable here: this is why E-02 is explicitly labelled behavior-neutral and V-03 owns the proof.
- `inspect_lane` IS A NON-MUTATING, RUN-CONTEXT-FREE READING and must stay that way. It has no `run_dir`
  or `item` and no way to get one, so the R5.5 inventory cannot live inside `LaneState` (F-14). Retention
  classification belongs where the run context is: the driver call site.
- `worktree_lease` DELIBERATELY IMPORTS NO OTHER PACKAGE MODULE, stated in its own comment at
  `worktree_lease.py:49-52` ("THE DEPENDENCY DIRECTION PERMITS ONLY THIS HOME. This module imports neither
  runner and no other package module"). Round 2 verified a function-local import back into
  `lane_containment`/`runner_shared` does not raise in either import order, so E-01's delegation is
  workable; but adding a module-level edge would contradict that documented layering, and adding the
  inventory here would contradict it more deeply. Prefer the call site.
- Lane branches are cheap and are the durable record of a lane's work: the manual sweep removed 28
  WORKTREES and deleted ZERO branches. Teardown means the directory, never the ref.

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | `commits_ahead` is measured against the lane's OWN base, never the integration target | `worktree_lease.py:308-314`, `rev-list --count {base_sha}..{head}` where `base_sha` comes from `_lane_base_sha` (the branch-creation reflog entry) |
| F-2 | Any non-zero `commits_ahead` forces `LANE_HOLDS_WORK`, and `reclaimable` is False for that state | `worktree_lease.py:321` (`if commits_ahead > 0 or dirty`), `:193-199` (`reclaimable`) |
| F-3 | The defect is systematic, not incidental: 28 of 38 worktrees were merged AND clean | measured 2026-09-17; 4.7G total, 1.1G after removing exactly those 28 |
| F-4 | Six sampled merged lanes each reported HOLDS-WORK with a non-zero count | `3dki3o` 5, `s16omw` 6, `yrqyxb` 5, `51vw4y` 4, `orziju` 4, `ty3cj6` 4; all with `ahead_of_main=0` and `--is-ancestor` exit 0 |
| F-5 | ~~The real cost is signal loss: merged lanes are indistinguishable from stranded ones in `aw attention`~~ **REFUTED AT REVIEW 2026-09-18** | `aw attention --check` at HEAD `f741596e` emitted 19 rows over 12 DISTINCT lanes; `merge-base --is-ancestor <branch> main` said NOT-ancestor for ALL 12, so ZERO false positives; the six merged lanes named in F-4 appear ZERO times. `classify_lane_integration` already classifies a merged lane `LANDED` and `LANE_ATTENTION_STATES` omits it (`runner_shared.py:1063-1068`, `:1110-1180`) |
| F-6 | An untracked file makes a merged lane unsafe to remove, so merged-ness alone must never authorize teardown | lane `wfamig` was merged and held the ONLY copy of an 89-line plan `i4ak5n` (now present in `main`'s `pending/`, verified at review; the hazard class stands) |
| F-7 | Both hosts already share the reclaim decision through one dict key, so one fix covers both | `oc_runipd.py:2337` and `agy_runipd.py:1292` both read `lane["reclaimable"]` from `runner_shared`'s lane dict (`runner_shared.py:825`) |
| F-8 | **`reclaimable` HAS NOTHING TO DO WITH THE END-OF-RUN LEAK.** Its only two readers are on the INTERRUPT path | `oc_runipd.py:2337` and `agy_runipd.py:1292` are both inside `reclaim_lanes_on_interrupt` (`oc_runipd.py:2226`, `agy_runipd.py:1181`); a repo-wide search finds no third reader |
| F-9 | The end-of-run teardown ALREADY EXISTS on both hosts and is gated on the R5.5 INVENTORY, not on `reclaimable` | `lane_containment.teardown_lane_if_classified` called at `oc_runipd.py:7881` and `agy_runipd.py:4430`, each inside the `fin_rc == 0` success branch (AST-confirmed guard chain); the leak's real cause is an unaccounted gitignored file, which is plan `5w8g8j`'s subject |
| F-10 | **`dirty` CANNOT SEE AN IGNORED FILE, so the authored E-02 would have authorized destroying one** | `inspect_lane` uses a plain `git status --porcelain` (`worktree_lease.py:316-319`); the R5.5 inventory deliberately adds `--ignored=traditional` (`lane_containment.py:2814-2819`) because "ignored means disposable" already destroyed lane content once (spec `7ckptx` R5.5) |
| F-11 | **GIT'S OWN REFUSAL IS NOT A BACKSTOP FOR AN IGNORED FILE.** The authored plan's safety argument rested on it | MEASURED at review, git 2.43.0, real worktree, only unexplained content one IGNORED file: plain porcelain empty, `--ignored=traditional` showed `!! ig/precious.txt`, and `git worktree remove` with NO `--force` exited **0** and DELETED it. The same probe with an UNTRACKED file exited 128 and preserved it |
| F-13 | **WIDENING `reclaimable` IS INERT: `holds_work` INTERCEPTS A MERGED LANE FIRST.** Round 2 | the interrupt loop tests `if lane["holds_work"]:` and `continue`s at `oc_runipd.py:2287` / `agy_runipd.py:1242`, BEFORE reading `reclaimable` at `:2337` / `:1292`; `holds_work` is `state == LANE_HOLDS_WORK` (`worktree_lease.py:189-190`) and a merged lane keeps `commits_ahead > 0`. MEASURED on a real merged lane: `state HOLDS-WORK`, `commits_ahead 1`, `holds_work True`, `reclaimable False`, `is-ancestor(->main) rc=0`. So E-01+E-02 alone change nothing observable; E-03 must change the DECISION ORDER |
| F-14 | **`inventory_lane` WITH NO `run_dir`/`item` CALLS EVERY LANE UNCLASSIFIABLE**, so calling it from `inspect_lane` (round-1 E-02) would have broken today's reclaim too | `submission_retention` returns `uncollected=True` ("no run directory or item was supplied") when either is None (`lane_containment.py:3075-3080`) and `classified` requires `not uncollected_submission` (`:3104-3107`). MEASURED on a PERFECTLY CLEAN lane: `unknown_* ()` yet `classified FALSE`, `reason_codes ('uncollected-submission',)`. `inspect_lane` has no such parameter (`worktree_lease.py:258-263`); `reclaim_lanes_on_interrupt` DOES hold both (`oc_runipd.py:2226-2260`), so the check belongs at the call site |
| F-15 | **THE SHARED GATE ALSO DELETES THE BRANCH**, so round-1's "route through the gate and the ref survives" was unsatisfiable | `teardown_lane_if_classified` defaults to `runner_shared.teardown_isolation_worktree` (`lane_containment.py:3329`) -> `teardown_worktree(force=True)` (`runner_shared.py:1004-1012`) -> `git branch -D` (`worktree_lease.py:701`). MEASURED driving the gate to authorize teardown: `torn_down True`, worktree gone, `rev-parse --verify <branch>` **rc=128**, reflog "unknown revision". Keeping the ref needs its own mechanism (OQ-05) |
| F-16 | The repository has FOUR direct force-teardown callers, not two, so a repo-wide assertion would be wrong in both directions | `oc_runipd.py:2345`, `agy_runipd.py:1300` (this plan's), `runner_shared.py:1012` (the GATE's own remover, must keep working), `runner_shared.py:3934` (a no-files-changed cleanup this plan does not touch). E-05 must assert REACHABILITY from the interrupt path, never a string count |
| F-12 | The predicate `reclaimable` gates a `force=True` teardown that DELETES THE LANE BRANCH, so widening it widens what is destroyed | `if not lane["reclaimable"]: continue` then `teardown_worktree(repo, handle, force=True)` (`oc_runipd.py:2337-2345`, `agy_runipd.py:1292-1300`); that function's docstring records branch gone, reflog EMPTY, commits unreferenced, uncommitted files erased. `oc_runipd.py:2163-2165` states the invariant: "reclaim only provably-empty lanes ... is a DATA-SAFETY requirement, not a preference" |

## Proposed changes (ordered, validatable)

1. `worktree_lease.py`: add `merged_into_target` to `LaneState`, computed by delegating to
   `runner_shared.lane_work_has_landed` (function-local import; `runner_shared` already imports
   `worktree_lease`, so a module-level import would be circular). `None` maps to False. Additive; every
   existing field keeps its current value.
2. `worktree_lease.py`: widen `reclaimable` to accept a merged, non-dirty lane, with a docstring saying the
   reading is necessary but NOT sufficient for teardown. NOT calling `inventory_lane` from here, which
   would report every lane unclassifiable for lack of run context (F-14); the ignored-file hazard is closed
   at the call site in step 3 instead.
3. `oc_runipd.py` / `agy_runipd.py`: consult merged-ness BEFORE the `holds_work` bail-out so a merged lane
   reaches the reclaim branch at all (F-13; without this, steps 1 and 2 are inert), and route that reclaim
   through `lane_containment.teardown_lane_if_classified` (passing the `run_dir` and item the function
   already holds, so the inventory can read a receipt) instead of `teardown_worktree(force=True)`,
   recording a refusal on the existing preservation event.
4. `tests/test_worktree_lease_merged_reclaim.py`: the merged case, plus the unmerged,
   merged-plus-untracked, merged-plus-IGNORED-only, inventory-unreadable, and unanswerable-merged-ness
   cases as separate assertions, plus an assertion that `commits_ahead` is still non-zero for a merged
   lane.
5. A structural (AST or import-graph) assertion that no force-teardown remains reachable from
   `reclaim_lanes_on_interrupt` on either host.

REMOVED FROM THIS LIST AT REVIEW: the authored item 3 (end-of-run teardown) because that call site
already exists and is gated by the R5.5 inventory (F-9), and the authored item 4 (`attention.py`
exclusion) because it is already implemented (F-5). `attention.py` is no longer in `Scope-Paths`.

## Deferred / out of scope (with reason)

- TRIAGING the lanes that genuinely hold unmerged work is Order 02 (`ut0vzr`), not this plan. (The clause
  "this plan makes the report trustworthy" was removed at review: the report is ALREADY trustworthy, F-5.)
- MAKING A SUCCESSFUL RUN TEAR ITS LANE DOWN is plan `5w8g8j`'s, not this plan's. Added at review with the
  call-site evidence (F-9). Declared as `executed:5w8g8j` rather than left as prose, because this plan's
  own V-03 cannot pass while the inventory gate still preserves every lane.
- CHANGING WHAT `dirty` MEANS, or teaching `inspect_lane` to see ignored files, is out of scope. E-02
  consumes the R5.5 inventory instead. Widening `dirty` would change the `LANE_EMPTY`/`LANE_STALE`
  adoption path, which is a different question with its own regression surface.
- Deleting merged lane BRANCHES is out of scope. A ref is a few bytes and is the durable record of what
  a lane did; the disk was consumed by worktrees, and no evidence says the refs are a problem.
- A general `aw lane` operator verb (list/reclaim/recover) is a plausible follow-on but is not needed to
  stop the leak, and bundling a new public surface into a defect fix would widen the blast radius.
- The seven branch-only stranded lanes have NO worktree, so nothing this plan does affects them.

## Scope check

- Over-scope AS AUTHORED, both removed at review: the authored E-04 asked for an `aw attention` exclusion
  that ALREADY SHIPS (F-5), and the authored E-03 asked for an end-of-run teardown call site that ALREADY
  EXISTS and is gated on a rule this plan does not touch (F-9). `attention.py` was dropped from
  `Scope-Paths` accordingly. Keeping either would have let the plan claim credit for shipped work and, in
  E-03's case, add a SECOND teardown path in violation of R5.5/R6.1.
- Over-scope now: none. Every change is on the path from "an interrupted run holds a merged lane" to "that
  lane is reclaimed through the one teardown gate".
- SCOPE GREW IN ROUND 2, and the growth is forced rather than chosen. E-03 must now change the interrupt
  loop's DECISION ORDER, not just its teardown call, because the predicate this plan widens is never
  reached for a merged lane (F-13). That is a behavior change to a control path both hosts share, so it
  carries a real regression surface: the `holds_work` branch also snapshots dirty work, and reordering must
  not let a merged-but-dirty lane skip that snapshot. E-03's expected outcome and V-03 both pin the unmerged
  path as unchanged for exactly this reason.
- `Scope-Paths` WAS MISSING THE TWO DRIVER FILES and was corrected in round 2. E-03 edits `oc_runipd.py`
  and `agy_runipd.py`; the authored E-03 did too, and round 1 dropped `attention.py` without adding these,
  so the declaration would have made `aw ipd finalize` refuse on two out-of-scope paths. Both are now
  declared, which also means the runner announces them before the run.
- Under-scope, and stated plainly because the Concern originally overclaimed: this plan does NOT recover
  the measured 4.7G and does NOT stop a SUCCESSFUL run leaking its worktree. That is `5w8g8j`'s, declared
  as `executed:5w8g8j` in `Item-Dependencies`. What this plan fixes is real but narrow: the interrupt-path
  reclaimer leaving an already-merged lane behind, and (newly) that path force-deleting lane branches.
- Under-scope: this plan does not dispose of the worktrees currently on disk whose lanes hold unmerged
  work; those are Order 02's.

## Required tests / validation

- `python3 -m pytest tests/test_worktree_lease_merged_reclaim.py` passes, and each new assertion is
  shown to FAIL against pre-fix code (a test that passes both before and after proves nothing here).
- `python3 -m pytest` bare, green, with the actual summary line pasted. RUN IT BARE: `pyproject.toml`
  `addopts` already supplies the quiet/parallel/fast-subset flags, and a second `-q` suppresses the very
  summary line this item requires. A managed worker lane also fails a set of lifecycle tests BY DESIGN
  (backlog `770fkp`), so the gate is NO NEW failures against a baseline taken in the SAME tree, not an
  absolute count; take and paste that baseline before changing anything.
- `tests/test_lane_retention.py` still green, since E-02 and E-03 both now consume the R5.5 retention
  machinery this file pins. Paste its summary line; a regression here means the fix widened teardown.
- A REAL end-to-end check on the INTERRUPT path, since this defect survived unit-level correctness for
  weeks: interrupt a driver run holding a merged lane, then show `git worktree list` no longer contains it,
  and state the branch outcome explicitly (whichever OQ-05 authorized) rather than assuming the ref
  survives, which round 2 measured that it does not by default (F-15).
- A NEGATIVE CONTROL PROVING THE FIX IS NOT INERT, which is this plan's single highest-value test after
  round 2: apply E-01 and E-02 WITHOUT E-03's reordering and show the interrupt path still reports the
  merged lane `preserved`. Round 2 measured exactly that state (`holds_work True`, `reclaimable False`,
  merged rc=0), so a validation set that cannot distinguish it from success would have passed a plan that
  changed nothing.
- A REGRESSION CHECK ON TODAY'S RECLAIM: a lane that is reclaimable now must still be, and an UNMERGED
  dirty lane must still be snapshotted before preservation. E-03 reorders a shared control path, and the
  `holds_work` branch is where snapshotting lives, so this is the likeliest accidental casualty.
- NOT REQUIRED, and removed at review: an end-to-end check of the SUCCESSFUL integration path, and an
  `aw attention --check` assertion that merged lanes are absent. Both test behavior this plan no longer
  changes (F-5, F-9). Keeping them would let the plan claim credit for shipped work.
- ANY `aw attention` OR `git worktree list` FIGURE MUST NAME THE TREE IT WAS MEASURED IN. `.aw/records/runs/`
  is gitignored and absent inside a lane, and `stranded_lane_drift` returns `[]` when it finds no run
  records (`attention.py:1141-1145`), so an in-lane run reports a FALSE clean.

## Spec / documentation sync

SPEC `7ckptx` (`worker-lane-containment`, `Status: approved`) GOVERNS THIS CHANGE, correcting the authored
claim that no spec applies. R5.5 requires teardown to be REFUSED while a lane holds content the driver
cannot classify, explicitly including an IGNORED file, and R6.1 requires a rule consumed by more than one
surface to live in ONE predicate. E-02 and E-03 are written to COMPLY with both rather than to amend
either: E-02 consumes the existing inventory instead of inventing a second classification, and E-03 routes
the interrupt path through the existing shared gate instead of adding a second teardown path.

NO AMENDMENT IS DECLARED AND NO `.spec.md` IS IN `Scope-Paths`, deliberately. This plan NARROWS what gets
destroyed and widens nothing, so it needs no relaxation of R5.5. If an executor finds it cannot satisfy
E-02 or E-03 without narrowing R5.5, that is a STOP-AND-ASK condition, not a licence to edit the spec:
plan `5w8g8j` is already blocked on exactly that question, and two plans narrowing one approved MUST from
different Sets is how a shipped contract gets weakened twice.

## Open questions

### OQ-01: Which ref is the merge target on a repo that does not use `main`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM THE CODE, not by asking. The drivers already record
  the branch they integrate into per run (`ending_branch` was `main` for every attempt in the runs
  inspected), and the integration path merges into the checkout's current branch rather than a hardcoded
  name. E-01 therefore takes the target as a PARAMETER defaulting to the repo's integration branch, so a
  fork using `master` or `trunk` is correct without configuration. Hardcoding `"main"` would be the one
  wrong answer. CONFIRMED AND SHARPENED AT REVIEW: the repository has already made this exact decision
  and named the answer `LANE_INTEGRATION_TARGET_FALLBACK = "HEAD"` (`runner_shared.py:1074`), whose comment
  explains that both drivers merge into whatever the shared checkout has checked out, so `HEAD` is "the
  branch the merge would actually land on". E-01 must adopt THAT default by delegating to
  `lane_work_has_landed`, not invent a second default.

### OQ-02: Should teardown also delete the merged lane's branch?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, and this is deliberate rather than unexamined. The 2026-09-17
  manual sweep removed 28 worktrees and kept all 28 branches, which reclaimed 3.6G, so the disk problem
  is entirely worktrees. A branch is the durable record of what a lane did and is nearly free; deleting
  refs automatically would destroy audit history to save bytes. Recorded as a resolved question rather
  than omitted, so a later reader does not assume it was forgotten. REVIEW NOTE, because the answer turned
  out to be load-bearing rather than academic: today's interrupt path ALREADY deletes the branch, via
  `teardown_worktree(force=True)` (F-12). ROUND-2 CORRECTION, and it reopens the HOW rather than the
  WHETHER: routing through the shared gate does NOT preserve the ref either, because the gate's default
  remover is `teardown_isolation_worktree` -> `teardown_worktree(force=True)` -> `git branch -D`
  (`lane_containment.py:3329`, `runner_shared.py:1004-1012`, `worktree_lease.py:701`), measured deleting the
  branch with rc=128 on a subsequent `rev-parse` and an empty reflog (F-13). So "keep the ref" needs a
  mechanism this plan does not yet have, and choosing it is OQ-05. The ANSWER to OQ-02 stands; its
  IMPLEMENTATION is no longer assumed to be free.

### OQ-04: The retarget is INERT without a decision-order change. Accept the enlarged scope?

- Blocking: no
- Finding: PR-101
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-18 by maintainer decision: Accept the decision-order change in `reclaim_lanes_on_interrupt` so that merged lanes are checked before `holds_work` bails out.

### OQ-05: Keeping the lane ref requires a mechanism the shared gate does not provide. Which one?

- Blocking: no
- Finding: PR-103
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-18 by maintainer decision: Option (c) chosen. Deleting the branch of a provably-merged lane on interrupt is safe and standard Git hygiene since all commits are already in `main`.

### OQ-03: Given that `reclaimable` governs only the interrupt path and the real leak is `5w8g8j`'s, is the remaining defect worth its own plan?

- Blocking: no
- Finding: PR-001
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-18 by maintainer decision: Option (a) chosen. Proceed with Order 01 retargeted to the interrupt path.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of `inspect_lane` for a MERGED lane and an UNMERGED lane in a temp
    repo, showing `merged_into_target` True and False respectively, AND showing `commits_ahead` retains
    its pre-fix value for both (proving the field was added, not substituted). PLUS proof of DELEGATION
    rather than duplication: paste the added code (or an AST/grep count) showing the repository still has
    exactly ONE `merge-base --is-ancestor <branch> <target>` landing predicate and that `inspect_lane`
    calls it. PLUS the unanswerable case: a deleted branch yields `merged_into_target=False`, never True.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `reclaimable` and `merged_into_target` for FOUR lanes, each shown separately
    and none argued: merged+clean (True), merged+dirty-tracked (False), unmerged (False), and a lane that
    is reclaimable TODAY (still True, proving no regression to the `LANE_EMPTY`/`LANE_STALE` path). Plus
    the pasted `reclaimable` docstring showing it states that the reading is NECESSARY BUT NOT SUFFICIENT
    for teardown. DO NOT PRESENT THIS ITEM AS EVIDENCE THAT A MERGED LANE IS RECLAIMED: round 2 measured
    that the interrupt path never reaches `reclaimable` for a merged lane, so a green V-02 beside an
    unchanged V-03 means the fix is INERT. The IGNORED-file case belongs to V-03, not here.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: DRIVE `reclaim_lanes_on_interrupt` (or a real interrupted run) and paste, for the
    merged lane, `lane["action"]` showing it was RECLAIMED rather than `preserved` or `left-alone`, with
    `git worktree list` before and after. THIS IS THE ITEM THAT PROVES THE FIX IS NOT INERT: an
    implementation with E-01 and E-02 but not E-03's reordering yields `action = "preserved"` here while
    V-02 is fully green, which round 2 measured directly. Plus the REFUSAL path: an interrupted merged lane
    whose only unexplained content is a GITIGNORED file must be preserved, with its `reason_codes` pasted
    (`unknown-ignored-file`). Plus an UNMERGED lane shown still taking the snapshot-and-preserve path. Plus
    the same three results for the OTHER host, since the fix must not be per-host. STATE THE BRANCH
    OUTCOME EXPLICITLY, whichever OQ-05 authorized: paste `git rev-parse --verify <lane branch>` after the
    reclaim and say whether the ref survived, because round 2 measured that the shared gate's default
    remover DELETES it (rc=128, empty reflog), so a claim that the branch is kept requires the mechanism
    OQ-05 chose and is not free.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `python3 -m pytest tests/test_worktree_lease_merged_reclaim.py` summary line, PLUS
    TWO separate failure demonstrations, because one is not enough to prove the test is load-bearing:
    (a) the layer-2 merged case failing against PRE-FIX code, and (b) the layer-2 merged case failing
    against an E-01+E-02-ONLY implementation (apply E-01/E-02 without E-03's reordering and paste the
    failure). Demonstration (b) is what proves the suite would have caught the inert fix round 2 measured;
    a test file that passes with (b) applied is not acceptable evidence for this item.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the pasted structural check showing zero `teardown_worktree(..., force=True)` call
    sites REACHABLE FROM `reclaim_lanes_on_interrupt` on either host, and that both reach
    `teardown_lane_if_classified`. State the METHOD (AST or import graph); a grep over the diff does not
    satisfy this item, since it cannot prove reachability. ALSO paste the assertion NOT firing for the
    three legitimate force-teardown callers round 2 identified (`runner_shared.py:1012` the gate's own
    remover, `runner_shared.py:3934` the no-files-changed cleanup, and any test double), since an
    over-broad assertion that reds on untouched code would be reverted by the next executor.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. The executor MUST follow the repository
execution contract: work in an isolated worktree, commit only the declared `Scope-Paths`, path-scoped,
never `git add -A`, and never push. Paste ACTUAL runner output for every V-item; a claim of success
without pasted evidence does not satisfy this gate.

THIS PLAN WIDENS A PREDICATE THAT AUTHORIZES BRANCH DELETION, so it carries a higher bar than its size
suggests. `reclaimable` gates `teardown_worktree(force=True)`, which deletes the lane branch and erases
uncommitted files unrecoverably (F-12, and the invariant is stated in the code at `oc_runipd.py:2163-2165`).
The executor MUST NOT let a merged lane reach teardown without the R5.5 inventory having accounted for it:
`dirty` reads False for a lane holding an unaccounted IGNORED file, git's own refusal does not fire for one
(measured, F-11), and the result is silent destruction of the only copy of something. That gate lives at
the CALL SITE (E-03), not in `reclaimable` (F-14), so an implementation that ships E-01 and E-02 without
E-03 is not merely incomplete, it is the dangerous half without the safe half. If E-02 or E-03 appears to
require narrowing spec `7ckptx` R5.5, STOP AND ASK; do not edit the spec.

DO NOT ACCEPT A GREEN V-02 AS EVIDENCE THE DEFECT IS FIXED. Round 2 measured that the interrupt path never
reads `reclaimable` for a merged lane (`holds_work` intercepts it first, F-13), so the reading can be fully
correct while the behavior is unchanged. V-03 and V-04(b) exist to catch precisely that false green, and
neither may be satisfied by unit assertions on `LaneState` alone.

Post-gate lifecycle: on completion, `aw ipd finalize` moves this plan to `.aw/records/plans/executed/`
only after `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries observed
evidence. Do NOT mark this executed on the strength of the unit tests alone: V-03 requires a real
INTERRUPTED run to have reclaimed a real worktree while keeping its branch, because unit-level
correctness is exactly what this family of defect already passed for weeks.
