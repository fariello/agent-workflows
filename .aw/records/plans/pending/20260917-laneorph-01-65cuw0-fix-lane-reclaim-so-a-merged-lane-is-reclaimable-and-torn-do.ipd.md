# IPD: Fix lane reclaim so a merged lane is reclaimable and torn down

- Date: 2026-09-17
- Kind: child
- Concern: `LaneState.reclaimable` refuses a lane whose work is fully merged, so the INTERRUPT-path reclaimer leaves it alone forever. `worktree_lease.inspect_lane` computes `commits_ahead` as `rev-list --count <the lane's OWN base>..<head>` (`worktree_lease.py:308-314`), then sets `LANE_HOLDS_WORK` whenever that is non-zero (`:321`), and `reclaimable` requires `state in (LANE_EMPTY, LANE_STALE)` AND `commits_ahead == 0` (`:193-199`). So a merged lane stays HOLDS-WORK and non-reclaimable permanently. MEASURED 2026-09-17: six lanes (`3dki3o`, `51vw4y`, `orziju`, `s16omw`, `ty3cj6`, `yrqyxb`) each reported `HOLDS-WORK` with 4-6 `commits_ahead` while `merge-base --is-ancestor <branch> main` returned 0; re-confirmed merged at review HEAD `f741596e`. TWO CORRECTIONS APPLIED AT REVIEW 2026-09-18, because the original Concern misattributed the leak. FIRST, `reclaimable` IS NOT WHAT LEAKS A SUCCESSFUL RUN'S WORKTREE: it is read at exactly two call sites (`oc_runipd.py:2337`, `agy_runipd.py:1292`), BOTH inside `reclaim_lanes_on_interrupt`, so its blast radius is the interrupt path ALONE. The end-of-run teardown is a different call, `lane_containment.teardown_lane_if_classified` (`oc_runipd.py:7881`, `agy_runipd.py:4430`, both inside the `fin_rc == 0` success branch), and it consults the spec R5.5 INVENTORY, never `reclaimable`. What actually refuses it is an unaccounted gitignored file, which is plan `5w8g8j`'s subject. SECOND, `aw attention` ALREADY EXCLUDES A MERGED LANE (see the deleted E-04 and the Findings table), so that half was already-shipped work.
- Scope: Make the INTERRUPT-path reclaim reading honor merged-ness: add a merged-ness reading to `LaneState` REUSING the existing `runner_shared.lane_work_has_landed` predicate, and make `reclaimable` accept a merged, non-dirty lane so `reclaim_lanes_on_interrupt` can reclaim it. Does NOT change what `commits_ahead` MEANS: that figure is still the correct input to the lane-REUSE question (`LANE_EMPTY`/`LANE_STALE`/`LANE_FOREIGN` decide whether a lane can be adopted for a fresh execution), so this adds a separate predicate rather than redefining an existing one. EXPLICITLY NOT IN SCOPE, both removed at review as already-shipped or as another plan's: the end-of-run teardown call site (already wired; refuses on the R5.5 inventory, which is `5w8g8j`'s) and the `aw attention` merged-lane exclusion (already implemented).
- Scope-Paths: agent_workflows/worktree_lease.py, agent_workflows/runner_shared.py, tests/test_worktree_lease_merged_reclaim.py
- Item-Dependencies: executed:5w8g8j
- Status: reviewed
- Readiness: no-go
- From-Backlog: a58s04
- Set: laneorph
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 65cuw0

## Workflow history
- 2026-09-18 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; reviewed as part of orchestrator `tb63qv`'s Set (findings PR-001..PR-009 recorded there and in `.aw/records/reviews/20260917-laneorph-00-tb63qv-...review.md`); readiness `no-go`. RETARGETED, because BOTH authored deliverables dissolved on measurement. The authored E-03 (tear the lane down at the end of a successful integration) asks for a call site that ALREADY EXISTS on both hosts, `lane_containment.teardown_lane_if_classified` (`oc_runipd.py:7881`, `agy_runipd.py:4430`, AST-confirmed inside the `fin_rc == 0` success branch), which gates on the spec R5.5 INVENTORY and never on `reclaimable`; and the authored E-04 (stop `aw attention` calling a merged lane stranded) asks for behavior that ALREADY SHIPS (`runner_shared.py:1063-1068`, `:1110-1180`; measured 12/12 reported lanes not ancestors of `main`, and 0/6 merged lanes reported). `reclaimable`'s only two readers are inside `reclaim_lanes_on_interrupt`, so this plan's real blast radius is the INTERRUPT path; `attention.py` was dropped from `Scope-Paths` and `executed:5w8g8j` declared, since the leak this plan's Concern describes belongs to `5w8g8j`. THE MOST SERIOUS FINDING (PR-003) IS FIXED IN PLACE: the authored E-02 would have CAUSED DATA LOSS. `dirty` is a plain `git status --porcelain` blind to IGNORED files (`worktree_lease.py:316-319` vs `lane_containment.py:2814-2819`); `reclaimable` gates `teardown_worktree(force=True)`, which DELETES THE LANE BRANCH and empties its reflog; and git's refusal, which the plan named as its second backstop, does NOT fire for an ignored file. MEASURED, git 2.43.0, real worktree whose only unexplained content was one ignored file: plain porcelain `''`, `--ignored=traditional` `!! ig/precious.txt`, `git worktree remove` with NO `--force` exit **0**, file DELETED; the same probe with an UNTRACKED file exit 128, file preserved. So E-02 now requires `lane_containment.inventory_lane(...).classified` (fail-toward-preservation when unreadable), E-03 routes the interrupt teardown through `teardown_lane_if_classified` (removing a pre-existing force-delete hazard), E-04 makes the merged-plus-IGNORED-only case the discriminating assertion, and new E-05 pins the no-force-teardown invariant by AST. PR-004 fixed by DELEGATING E-01 to the existing `lane_work_has_landed` rather than adding a second `--is-ancestor` call (R6.1), handling its three-valued return honestly and noting the circular-import trap; OQ-01 now adopts the repository's existing `LANE_INTEGRATION_TARGET_FALLBACK = "HEAD"` (`:1074`) instead of inventing a default. Spec-sync rewritten: `7ckptx` (approved) R5.5/R6.1 DO govern, no amendment is declared because the corrected plan complies, and narrowing R5.5 is a stop-and-ask since `5w8g8j` is already blocked on exactly that. OQ-03 raised `Blocking: yes` carrying PR-001.

- 2026-09-18 reviewed (aw set): plan-review complete (reviewed as part of orchestrator tb63qv's Set): REVIEWED - OPEN QUESTIONS; retargeted to the interrupt path after PR-001 refuted both authored deliverables (E-03's end-of-run teardown already exists and gates on the R5.5 inventory; E-04's attention exclusion already ships); PR-003 FIXED, the authored E-02 would have force-deleted a merged lane holding only an unaccounted IGNORED file since dirty cannot see one and git worktree remove does not refuse for one (measured, exit 0, file deleted); E-02 now consumes inventory_lane().classified and E-03 routes teardown through teardown_lane_if_classified; PR-004 FIXED by delegating to lane_work_has_landed; executed:5w8g8j declared; readiness no-go
- 2026-09-17 to-review (aw set): Authored 2026-09-17 from a measured sweep of .aw/worktrees/ (38 worktrees/4.7G, 28 provably merged and clean) and of the 13 lane branches holding 76 unmerged commits; complete enough to critique

- 2026-09-17 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Make a merged lane reclaimable, and reclaim it at the moment its work lands, so `.aw/worktrees/` stops
growing without bound. The user-visible symptom was 4.7G of worktrees, but the load-bearing harm is to
the STRANDED-LANE SIGNAL: `aw attention` currently cannot distinguish a merged lane from a genuinely
stranded one, so roughly 28 merged lanes buried the roughly 12 that really do hold unmerged work. A
report that cries wolf on two thirds of its rows is a report an operator learns to ignore, which is
exactly how the seven branch-only stranded lanes (`2c122z` at 26 commits, `58ha43` at 22, `7p9n2v` at
16, `rchpms` at 10) went unnoticed for weeks.

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
the R5.5 inventory (`lane_containment.inventory_lane(...).classified`) rather than `dirty`, and E-03 is
replaced by a wiring item that routes the interrupt teardown through
`lane_containment.teardown_lane_if_classified` so no second teardown path exists (R6.1).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Make merged-ness a first-class reading

- [ ] E-01 Add a `merged_into_target` boolean to `worktree_lease.LaneState`, computed by DELEGATING to the existing `runner_shared.lane_work_has_landed(repo, branch, target=...)` rather than issuing a second `merge-base --is-ancestor` call, so the repository keeps ONE definition of "merged" (spec `7ckptx` R6.1). Record it ALONGSIDE `commits_ahead`; do not alter how `commits_ahead` is computed, since `LANE_STALE`/`LANE_FOREIGN` adoption logic reads it and changing its meaning would silently change which lanes are reused. HANDLE THE THREE-VALUED RESULT HONESTLY: `lane_work_has_landed` returns `True`/`False`/`None`, `None` meaning the question could not be answered; map `None` to NOT-merged (`False`) so an unanswerable lane is never treated as recovered, and state that choice in the field's docstring. CHECK THE IMPORT DIRECTION BEFORE WRITING: `runner_shared` imports `worktree_lease` (`runner_shared.py:810`) and not the reverse, so a module-level import back would be circular; use a function-local import, which is the pattern `runner_shared` itself uses, and say so.
  - Depends on: none
  - Expected outcome: `inspect_lane` on a merged lane returns `merged_into_target=True` while still reporting its real `commits_ahead`; on an unmerged lane and on an unanswerable one it returns False. No existing field changes value. No second `--is-ancestor` call is introduced anywhere.
  - Execution state: pending

- [ ] E-02 Make `LaneState.reclaimable` return True for a merged lane ONLY when the spec R5.5 inventory accounts for everything the lane holds, in addition to today's `LANE_EMPTY`/`LANE_STALE` cases. USE `lane_containment.inventory_lane(lane_root=...).classified`, NOT the existing `dirty` field. THE REASON IS MEASURED AND IS IN THE GOAL: `dirty` comes from a plain `git status --porcelain` that cannot see IGNORED files, and a merged lane whose only unexplained content is one ignored file would read `dirty=False`, become reclaimable, and be force-deleted branch-and-all by the caller. Keep today's `LANE_EMPTY`/`LANE_STALE` branch reading `dirty` exactly as it does now, so no existing lane changes classification; the inventory requirement applies to the NEW merged branch only. If the inventory cannot run, treat the lane as NOT reclaimable (fail toward preservation, matching `inventory_lane`'s own rule).
  - Depends on: E-01
  - Expected outcome: a merged lane whose inventory is `classified` is `reclaimable=True`; a merged lane holding an unaccounted DIRTY TRACKED, UNTRACKED, or IGNORED file stays `reclaimable=False`; a merged lane whose inventory could not run stays False; an unmerged lane is unaffected.
  - Execution state: pending

### Task group 2: Route the interrupt reclaim through the one teardown gate

- [ ] E-03 Route the INTERRUPT-path reclaim through `lane_containment.teardown_lane_if_classified` instead of calling `worktree_lease.teardown_worktree(repo, handle, force=True)` directly, at both call sites (`oc_runipd.py:2337-2345`, `agy_runipd.py:1292-1300`). WHY THIS REPLACED THE AUTHORED E-03 (which asked for an end-of-run teardown that already exists): the direct `force=True` call is the mechanism that makes a widened `reclaimable` dangerous, since it deletes the lane BRANCH and erases uncommitted files, and spec R5.5 requires teardown to go through the shared gate. Record a refusal on the existing preservation event rather than force-deleting. Preserve the existing operator `keep` prompt and the `left-alone` disposition for a non-reclaimable lane.
  - Depends on: E-02
  - Expected outcome: no code path reachable from `reclaim_lanes_on_interrupt` calls `teardown_worktree` with `force=True`; an interrupted merged-and-classified lane is reclaimed; an interrupted merged lane holding unexplained content is preserved with its reason recorded. Both hosts changed identically; no per-host rule.
  - Execution state: pending

### Task group 3: Guard the invariant

- [ ] E-04 Add `tests/test_worktree_lease_merged_reclaim.py`: build a real lane in a temp repo, cut from an OLDER base, commit on it, merge it to the target, and assert `merged_into_target=True`, `reclaimable=True`, and that `commits_ahead` is still non-zero (proving the fix did not achieve its result by corrupting that figure). Add the negative cases, each of which must be a SEPARATE assertion: an unmerged lane stays non-reclaimable; a merged lane with an UNTRACKED file stays non-reclaimable; a merged lane whose ONLY unexplained content is an IGNORED file stays non-reclaimable (this is the case a `dirty`-based implementation would get wrong, so it is the test that distinguishes a correct fix from a plausible one); a merged lane whose inventory cannot run stays non-reclaimable; and an unanswerable merged-ness reading yields False rather than True.
  - Depends on: E-03
  - Expected outcome: a test file that fails against today's code for the merged case and passes after E-01..E-03, with the ignored-file and untracked-file cases pinned so a later change cannot reintroduce the hazard the Goal measures.
  - Execution state: pending

- [ ] E-05 Assert the NO-SECOND-TEARDOWN-PATH invariant structurally, not by reading the diff: prove by AST or import-graph inspection that `teardown_worktree(..., force=True)` has no remaining caller reachable from `reclaim_lanes_on_interrupt` on either host, and that both hosts reach the shared gate. Follow the existing precedent for this style of proof (`lanectn` `4fodkt` established shared-rule assertions by AST rather than grep) rather than inventing a new one.
  - Depends on: E-03
  - Expected outcome: a pinned assertion that a future edit reintroducing a direct force-teardown on the interrupt path fails a test, rather than relying on a reviewer noticing.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `worktree_lease.py` owns lane state as a NON-MUTATING reading (`inspect_lane`'s docstring); a fix
  belongs in that reading plus its consumers, not in a new parallel notion of lane health.
- `LaneState.reclaimable`'s docstring already states the safety rule this plan must preserve verbatim:
  "Provably empty: safe to tear down. NEVER true for a lane holding commits or dirty files." E-02
  widens "provably empty" to "provably recovered", and must not weaken the dirty half.
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
| F-12 | The predicate `reclaimable` gates a `force=True` teardown that DELETES THE LANE BRANCH, so widening it widens what is destroyed | `if not lane["reclaimable"]: continue` then `teardown_worktree(repo, handle, force=True)` (`oc_runipd.py:2337-2345`, `agy_runipd.py:1292-1300`); that function's docstring records branch gone, reflog EMPTY, commits unreferenced, uncommitted files erased. `oc_runipd.py:2163-2165` states the invariant: "reclaim only provably-empty lanes ... is a DATA-SAFETY requirement, not a preference" |

## Proposed changes (ordered, validatable)

1. `worktree_lease.py`: add `merged_into_target` to `LaneState`, computed by delegating to
   `runner_shared.lane_work_has_landed` (function-local import; `runner_shared` already imports
   `worktree_lease`, so a module-level import would be circular). `None` maps to False. Additive; every
   existing field keeps its current value.
2. `worktree_lease.py`: widen `reclaimable` to accept a merged lane whose R5.5 inventory is `classified`.
   NOT keyed on `dirty`, which cannot see an ignored file (F-10, F-11). The existing
   `LANE_EMPTY`/`LANE_STALE` branch is untouched.
3. `oc_runipd.py` / `agy_runipd.py`: route the interrupt-path reclaim through
   `lane_containment.teardown_lane_if_classified` instead of `teardown_worktree(force=True)`, recording a
   refusal on the existing preservation event.
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
  lane is reclaimed through the one teardown gate, with its branch kept".
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
  weeks: interrupt a driver run holding a merged lane, then show `git worktree list` no longer contains it
  AND `git rev-parse --verify <branch>` still succeeds.
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
  `teardown_worktree(force=True)` (F-12). So this question's answer is not merely preserved by this plan,
  it is ENFORCED by E-03, and V-03 asserts `git rev-parse --verify <branch>` succeeds after a reclaim.

### OQ-03: Given that `reclaimable` governs only the interrupt path and the real leak is `5w8g8j`'s, is the remaining defect worth its own plan?

- Blocking: yes
- Finding: PR-001
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT DECIDED BY THE REVIEWER: it is a scope and priority call, and the
  honest answer changes what this plan IS. Review established (F-8, F-9) that this plan cannot deliver the
  4.7G recovery its authored Concern promised, because the successful-run teardown is a different call site
  gated on the R5.5 inventory. What remains genuinely unfixed and is this plan's alone: an interrupted run
  leaves an already-merged lane behind, and worse, when it DOES reclaim, it force-deletes the lane branch.
  The second half is arguably the more valuable fix and was not in the authored plan at all. THE QUESTION:
  (a) execute as retargeted, accepting the narrower value; (b) reduce it to the E-03 safety fix only
  (route the interrupt teardown through the gate) and drop the merged-ness widening, which is the smallest
  change that removes a data-safety hazard; or (c) retire this plan and fold both items into the `laneign`
  Set beside `5w8g8j`, since they share the retention machinery. The reviewer notes (b) is executable TODAY
  with no dependency on `5w8g8j`, whereas (a) cannot validate V-03 until `5w8g8j` lands.

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
  - Required evidence: pasted `reclaimable` for FIVE lanes, each shown separately and none argued:
    merged+fully-accounted (True), merged+dirty-tracked (False), merged+UNTRACKED-file-only (False),
    merged+IGNORED-file-only (False), merged+inventory-unreadable (False). THE IGNORED CASE IS THE ONE
    THAT DISTINGUISHES A CORRECT FIX FROM A PLAUSIBLE ONE and must be pasted: an implementation keyed on
    `dirty` returns True here, because plain `git status --porcelain` cannot see the file (F-10). Also
    paste the pre-existing `LANE_EMPTY`/`LANE_STALE` behavior unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: for an INTERRUPTED run (not a successful one; the successful path was never
    `reclaimable`'s, per F-8/F-9), `git worktree list` before and after showing the merged lane's worktree
    gone, plus `git rev-parse --verify <lane branch>` SUCCEEDING after, so the branch is provably kept
    (today's `force=True` path would delete it, so this assertion is the behavior change). Plus the
    refusal path: an interrupted merged lane holding an unaccounted file, its worktree still present, with
    the recorded reason and reason codes pasted. Plus the same evidence for the OTHER host, since the fix
    must not be per-host.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `python3 -m pytest tests/test_worktree_lease_merged_reclaim.py` summary line,
    PLUS evidence the merged-case assertion fails against pre-fix code (stash the fix or check out the
    prior revision and paste the failure). A test that passes both before and after proves nothing here.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the pasted structural check showing zero `teardown_worktree(..., force=True)` call
    sites reachable from `reclaim_lanes_on_interrupt` on either host, and that both reach
    `teardown_lane_if_classified`. State the METHOD (AST or import graph); a grep over the diff does not
    satisfy this item, since it cannot prove reachability.
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
The executor MUST NOT satisfy E-02 by keying on `dirty`: that reads False for a lane holding an
unaccounted IGNORED file, git's own refusal does not fire for one (measured, F-11), and the result is
silent destruction of the only copy of something. If E-02 or E-03 appears to require narrowing spec
`7ckptx` R5.5, STOP AND ASK; do not edit the spec.

Post-gate lifecycle: on completion, `aw ipd finalize` moves this plan to `.aw/records/plans/executed/`
only after `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries observed
evidence. Do NOT mark this executed on the strength of the unit tests alone: V-03 requires a real
INTERRUPTED run to have reclaimed a real worktree while keeping its branch, because unit-level
correctness is exactly what this family of defect already passed for weeks.
