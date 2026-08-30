# IPD: lane allocation adopts or attempt-scopes instead of hard-failing, and an interrupt records lanes rather than leaking them

- Date: 2026-08-29
- Kind: child
- Concern: A CTRL-C during `aw oc run` leaves lane worktrees and branches behind, because the driver installs no interrupt cleanup. Worse, `allocate_worktree` then HARD-FAILS on `fatal: a branch named 'aw/lane/<id6>' already exists`, so every later run of that Set dies at allocation and stays wedged until a human removes the debris by hand. A resumable run cannot get past its OWN leftovers. The fix must not be blind teardown: `teardown_worktree(force=True)` deletes the lane branch, which leaves the lane's commits unreferenced and garbage-collectable, and a leaked lane can hold real unmerged work.
- Scope: Make lane allocation tolerate its own debris (adopt a verifiable existing lane, or allocate an attempt-scoped name) and make an interrupt PRESERVE-AND-RECORD rather than leak or destroy: register every allocated lane durably, leave any lane holding commits or dirty files intact and reported as recoverable, and tear down only provably-empty lanes. Excludes the general stop-level protocol (Set `runstop`, spec `c4gd2h`), excludes candidate-merge integration and `aw recover`/`aw doctor --lanes` (plan `2c122z`), and excludes relocating machine state (plan `58ha43`).
- Scope-Paths: agent_workflows/worktree_lease.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_lane_allocation_idempotent.py
- Item-Dependencies: none
- Status: to-review
- Set: laneorphan
- Order: 1
- Highest E allocated: 07
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: zwnjp3
- Blocks-Release: next
- From-Backlog: 17gydk

## Workflow history

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-08-30 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): graduated from backlog `17gydk` during the blocking-backlog graduation sweep. Every mechanism this plan relies on was MEASURED in throwaway repos at HEAD `28a5c7f`, not assumed: the reported error string reproduced verbatim, branch-only leftovers confirmed to wedge allocation just as badly as a full lane, emptiness confirmed detectable, adoption confirmed verifiable, attempt-scoping confirmed to work, and `git worktree list --porcelain` confirmed as the discovery surface. The plan also records a defect the item did NOT know about (F5): today's `teardown_worktree(force=True)` deletes the lane BRANCH, so the lane's commits survive only as unreferenced objects. That makes "tear down only empty lanes" a data-safety requirement rather than a nicety.

## Goal

A run must never be permanently wedged by its own leftovers, and no cleanup path may ever be able to destroy unmerged lane work. Allocation becomes idempotent for the same lane identity, and interrupt handling preserves anything that holds work while reclaiming only what is provably empty.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: classify a lane before touching it

- [ ] E-01 Add a lane-state inspection function to `worktree_lease.py` that, for a given lane id, reports what actually exists WITHOUT mutating anything: whether the branch `aw/lane/<lane-dirname>` exists, whether the worktree directory is registered, its HEAD, whether it is ahead of a given base, and whether its tree is dirty. Derive the registered-worktree facts from `git worktree list --porcelain` (measured as the reliable discovery surface, see F4) rather than from directory existence alone, because a branch can survive with NO worktree and that case wedges allocation identically (F2). Classify the lane into exactly one of: ABSENT (nothing exists), EMPTY (exists, no commits beyond base, clean tree), HOLDS-WORK (commits beyond base or a dirty tree), or FOREIGN (exists but its base is not an ancestor of the requested base, so it is not this run's lane to reuse). This classifier is the shared substrate for E-02 and E-05; do not let either grow its own git probing.
  - Depends on: none
  - Expected outcome: for a fixture repo the classifier returns ABSENT before allocation, EMPTY immediately after, HOLDS-WORK after a lane commit, HOLDS-WORK for a clean-but-committed lane and for a dirty-but-uncommitted lane independently, and distinguishes a branch-only leftover from a fully-registered lane.
  - Execution state: pending

- [ ] E-02 Make `allocate_worktree` tolerate its own debris instead of raising. On ABSENT, behave exactly as today. On EMPTY whose base matches the requested base commit, ADOPT it: return a handle for the existing lane rather than failing, since a fresh lane at that commit is byte-identical to what allocation would have created (measured: `git merge-base` confirms the existing lane's ancestry, F3). On HOLDS-WORK or FOREIGN, do NOT adopt and do NOT destroy: allocate an ATTEMPT-SCOPED lane instead, so the run proceeds while the existing lane is left untouched and discoverable. Attempt scoping already works through the existing name sanitizer with no change to it (measured: a lane id containing a colon produces `aw/lane/<id>_<attempt>` and allocates cleanly alongside the original, F3), so this needs a naming convention and a caller-visible field, not a new mechanism. Keep the fail-closed contract: a genuinely failed `git worktree add` must still raise, and note that a FAILED add still CREATES the branch (F6), so the failure path must clean up the branch it just made or the next attempt inherits a branch-only leftover.
  - Depends on: E-01
  - Expected outcome: a second `allocate_worktree` for the same lane id no longer raises; an EMPTY same-base lane is adopted and the returned handle names the existing branch; a lane holding commits causes an attempt-scoped allocation and is left byte-identical; a genuinely broken add still raises AND leaves no stray branch behind.
  - Execution state: pending

- [ ] E-03 Surface WHICH outcome occurred to the caller, because the drivers must record it and a silent adoption is indistinguishable from a fresh allocation in the ledger. Extend the returned handle (or return an accompanying outcome value; the executor picks and records which) with the disposition: created, adopted, or attempt-scoped, plus the lane it was displaced from when attempt-scoped. Do NOT make `worktree_lease` emit ledger events itself. This constraint is inherited, not invented: plan `2c122z` E-06 records that `worktree_lease` imports only stdlib and is REUSED to allocate disposable candidate worktrees, so a blanket event hook there would both couple a low-level primitive to run context and misrecord candidates as lanes. Emit at the callers instead.
  - Depends on: E-02
  - Expected outcome: each of the three dispositions is observable from the allocation result; `worktree_lease` still imports only stdlib (assert this, since it is a constraint another plan depends on); no ledger call appears in the module.
  - Execution state: pending

### Task group 2: an interrupt records lanes and destroys nothing that holds work

- [ ] E-04 Register every allocated lane durably at the moment of allocation, in BOTH drivers, so an interrupt has something to report and a later run has something to find. The drivers already write lane facts into per-item state and an event stream on the happy path (locate `worktree-allocated` in `oc_runipd.py` and its agy counterpart by that event name), and they already record `preserved_worktree`/`preserved_branch` when a lane survives a non-executed item (locate `worktree-preserved`). Reuse those existing paths rather than adding a second store, and record the E-03 disposition alongside. Be aware of an important limitation, verified and recorded in plan `z2isfg` finding F8: `preserved_worktree`/`preserved_branch` are currently only ever WRITTEN and never READ anywhere in the package, so today they are a dead record. This plan makes them meaningful by having E-05 and E-02 actually consume the lane state, but do NOT claim the existing fields already provide recovery.
  - Depends on: E-03
  - Expected outcome: an allocation writes a durable record naming the lane, its branch, its worktree path, its base sha, and its disposition, in both drivers; the record is readable from a fresh process after the writing process exits.
  - Execution state: pending

- [ ] E-05 Install interrupt handling that PRESERVES AND RECORDS, and tears down ONLY provably-empty lanes. On `SIGINT` and `SIGTERM`, for each lane this run allocated: classify it with E-01; if EMPTY, tear it down so the next run is not wedged; if HOLDS-WORK, LEAVE IT ENTIRELY ALONE, record it as recoverable, and report it to the operator with its branch and path. This asymmetry is a HARD data-safety requirement, not a preference, and the reason is a defect this plan measured that the backlog item did not know about: `teardown_worktree(force=True)` deletes the lane BRANCH as well as the worktree, after which the lane's commits are unreferenced with no reflog entry and survive only until git garbage-collects them (F5). A blind cleanup on interrupt would therefore be capable of destroying exactly the work the item's real-world incident had to rescue by hand. Follow the repo's established policy for un-owned dirty state, which is REFUSE-AND-REPORT rather than relocate: do NOT stash, reset, or move anything. Land symmetrically in both drivers.
  - Depends on: E-01, E-04
  - Expected outcome: `SIGINT` and `SIGTERM` each leave every HOLDS-WORK lane byte-identical (branch present, tip unchanged, tree unchanged) and reported with its branch and path, while EMPTY lanes are gone; nothing is stashed, reset, or moved; both drivers behave identically.
  - Execution state: pending

- [ ] E-06 Make the interrupt report and the recorded state ACTIONABLE, since the item's incident required inspecting five lanes by hand to discover that four were empty and one held roughly 1180 lines of real work. Print, per preserved lane, the branch, the worktree path, whether it is ahead of base and by how many commits, and whether its tree is dirty, so the operator can tell at a glance which lane matters. Do NOT add a new discovery verb here: `aw doctor --lanes` and `aw recover <run-id>` are explicitly owned by plan `2c122z` (verified in its Scope), and adding a second lane-inspection surface would create exactly the duplicate mechanism the house rules forbid. If the reporting needs a shared helper, put it where `2c122z` can consume it and say so. Keep the text free of em and en dashes per the execution contract.
  - Depends on: E-05
  - Expected outcome: the interrupt report distinguishes an empty lane from a work-holding one without the operator running any git command; no new CLI verb or flag is added; the E-01 classifier is the single source of the reported facts.
  - Execution state: pending

### Task group 3: prove it, including the destructive case

- [ ] E-07 Add `tests/test_lane_allocation_idempotent.py` covering, on throwaway git repos: (a) the exact reported failure, so a second allocation for the same lane id no longer raises `a branch named 'aw/lane/<id>' already exists`, shown FAILING against pre-fix code; (b) a BRANCH-ONLY leftover (worktree removed, branch surviving) also allocates, since this was measured to wedge allocation identically and is the likelier residue; (c) an EMPTY same-base lane is ADOPTED and no second worktree appears; (d) a lane holding commits is NOT adopted, gets an attempt-scoped allocation, and is byte-identical afterward (assert the tip sha and `git status --porcelain` before and after); (e) THE DESTRUCTIVE-CASE GUARD, asserting that no code path reachable from interrupt handling deletes a branch whose lane holds commits, and that after an interrupt the work-holding lane's tip is still reachable BY REFERENCE and not merely as an unreferenced object (this is the assertion that would have caught F5, and it must fail if someone replaces the classifier with a blanket force teardown); (f) a subsequent run of the same Set allocates successfully after an interrupt, which is the end-to-end property the item actually asks for; (g) both drivers, via a symmetry assertion that fails if only one was changed. Every case must be built from its own fixture repo; do NOT reference live lanes or shas, because this repo currently has five live lanes owned by a running driver and that set churns hourly (F7).
  - Depends on: E-01, E-02, E-05
  - Expected outcome: the module passes; (a), (b), (e), and (f) each shown to FAIL against pre-fix code; (d) proves preservation by sha comparison rather than by assertion; (g) fails when only one driver is changed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The reported failure is REPRODUCIBLE and was reproduced verbatim. In a throwaway repo, a second `allocate_worktree(root, "abc123")` raises `WorktreeError: git worktree add failed for lane 'abc123': ... fatal: a branch named 'aw/lane/abc123' already exists`, matching the incident text in the backlog item exactly.
- `allocate_worktree` builds the branch as `aw/lane/<sanitized-lane-id>` and the directory as `.aw/worktrees/<sanitized-lane-id>`, via a name sanitizer that maps `:` and `/` to `_`. That sanitizer is what makes attempt-scoped naming free: no change to it is needed.
- `teardown_worktree` removes the worktree with `--force` and then deletes the per-lane branch, with a comment calling the branch deletion best-effort and "not a correctness hazard". That comment is WRONG once a lane holds commits; see F5. Correcting it is part of E-05's work since the file is in `Scope-Paths`.
- The drivers already have the hooks this plan needs. `allocate_isolation_worktree` and `teardown_isolation_worktree` wrap the lease module; the allocation path writes a `worktree-allocated` event and per-item `worktree`/`worktree_branch` state; the allocation FAILURE path already records `worktree-alloc-failed` and marks the item blocked, which is the exact hard-failure the item reports; and a non-executed item's lane is recorded via `worktree-preserved`. Extend these, do not add a parallel path.
- The drivers install NO interrupt handler for lane cleanup. The only `KeyboardInterrupt` handling around a turn records `ipd-interrupted` and re-raises, and the module-level signal use is inside the child-process terminator. So an interrupt genuinely cannot clean up or record lanes today, exactly as the item states.
- `preserved_worktree` and `preserved_branch` are WRITTEN but never READ anywhere in the package (verified independently and recorded in plan `z2isfg` finding F8). Treat them as a durable breadcrumb this plan finally consumes, not as existing recovery.
- Ownership boundaries are already drawn by three sibling plans and this plan must respect them. `2c122z` (wtiso Phase 5) owns candidate-merge integration, durable lane-lifecycle ledger events, lease reconstruction after a crash, `aw recover <run-id>`, and `aw doctor --lanes`. The `runstop` Set (spec `c4gd2h`) owns the four stop LEVELS, the durable stop-request flag, and the shared `clean_shutdown` routine. This plan owns only allocation idempotency and the preserve-or-reclaim decision, which no other plan covers (verified: no pending plan or spec mentions attempt-scoped naming or allocation idempotency).
- `runstop` Phase 0 (`2ouj70`) independently reached the same REFUSE-AND-REPORT conclusion for dirty trees at stop time, citing the same house policy and explicitly rejecting auto-stash. E-05 follows that precedent rather than inventing a different rule.
- The suite is invoked BARE. Note that the default addopts exclude `slow`, so tests spawning real subprocesses must be marked `slow` and validated with the full run, per the repo convention that `runstop` Phase 0 also records.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `allocate_worktree` in `worktree_lease.py` | Allocation is not idempotent: a second call for the same lane id hard-fails, so a run cannot survive its own leftovers. REPRODUCED verbatim, matching the incident string. | throwaway repo at `28a5c7f`: `2nd allocate RAISED WorktreeError: git worktree add failed for lane 'abc123': ... fatal: a branch named 'aw/lane/abc123' already exists` |
| F2 | HIGH | same site | A BRANCH-ONLY leftover wedges allocation just as hard as a full lane. After `git worktree remove --force`, the branch survives and the next allocation still fails with the identical message. This matters because it is the likelier residue and because a directory-existence check would MISS it, so E-01 must consult refs, not just the filesystem. | same probe: after removing the worktree, `git branch --list aw/lane/abc123` still prints the branch and `3rd allocate RAISED WorktreeError: ... already exists` |
| F3 | MED | same site | Both proposed remedies are mechanically available TODAY, so this plan needs no new primitive. ADOPTION is verifiable, since the existing lane's base can be confirmed as an ancestor of the requested base. ATTEMPT SCOPING works unchanged, since a colon-bearing lane id sanitizes into a distinct branch and directory that allocate cleanly ALONGSIDE the original. | `git merge-base <base> <lane_tip>` equals base exactly; `allocate_worktree(root, "abc123:attempt2")` returned `aw/lane/abc123_attempt2` in dir `abc123_attempt2` while `aw/lane/abc123` remained |
| F4 | MED | discovery surface | `git worktree list --porcelain` reports every registered lane with its HEAD and branch, which is the reliable substrate for the E-01 classifier and needs no new bookkeeping. | probe output lists the main tree plus each lane with `HEAD <sha>` and `branch refs/heads/aw/lane/<id>` |
| F5 | HIGH | `teardown_worktree` in `worktree_lease.py` | A DEFECT THE BACKLOG ITEM DID NOT KNOW ABOUT, and the reason E-05's asymmetry is mandatory rather than nice. Today's teardown deletes the lane BRANCH as well as the worktree. Measured: after `teardown_worktree(force=True)` on a lane holding a commit, the branch is gone, `git reflog show <branch>` is EMPTY, and the commit survives only as an unreferenced object, i.e. garbage-collectable with no ref and no reflog to recover it from. So a blind interrupt cleanup would be capable of destroying precisely the work the item's incident had to rescue by hand. The module's own comment calling the branch deletion "not a correctness hazard" is wrong for a lane with commits. | probe at `28a5c7f`: lane tip `ebc3866c` committed, then `teardown_worktree(force=True)`; `branch --list` empty, `reflog show` empty, `git cat-file -e <tip>` still succeeds (unreferenced) |
| F6 | MED | `allocate_worktree` failure path | A FAILED `git worktree add -b` still CREATES the branch, so today's fail-closed path leaves a branch-only leftover that (per F2) wedges the NEXT attempt. The function's docstring claims "no partial worktree left claimed", which is true of the directory and false of the ref. E-02 must clean up the branch on the failure path. | independently observed in this repo's history and recorded in plan `z2isfg` finding F8, whose probe left a stray `aw/lane/testdup` branch that had to be deleted with `git branch -D` |
| F7 | LOW | this repo, right now | FIVE live lanes exist (`2c122z`, `58ha43`, `7p9n2v`, `qcqhj7`, `rchpms`) and a LIVE driver owns them (`aw oc run wtiso`, pid observed running at authoring time). Do NOT test against them, do NOT clean them up, and do NOT hardcode their names or shas: the set churns hourly. Build fixture repos. This also means the executor should expect concurrent commits to both driver modules while executing. | `git worktree list` plus the observed live `aw oc run wtiso` process |
| F8 | LOW | `worktree_lease.py` imports | The module imports only stdlib today, and plan `2c122z` E-06 DEPENDS on that staying true (it reuses `allocate_worktree` for disposable candidate worktrees and forbids coupling the primitive to run context). E-03 therefore returns a disposition to the caller rather than emitting events inside the module. | module imports read at `28a5c7f`; constraint quoted from `2c122z` E-06 |

## Proposed changes (ordered, validatable)

1. Add a non-mutating lane-state classifier over refs plus `git worktree list --porcelain` (E-01).
2. Make allocation adopt an empty same-base lane, attempt-scope around a lane holding work, and clean up the branch it creates on failure (E-02).
3. Report the disposition to the caller without coupling the lease module to run context (E-03).
4. Register lanes durably at allocation in both drivers, reusing the existing event and state paths (E-04).
5. Preserve-and-record on interrupt, reclaiming only provably-empty lanes, with the branch-deletion hazard fixed (E-05).
6. Make the report tell the operator which lane matters, without adding a second discovery surface (E-06).
7. Prove all of it, including a guard that would have caught the branch-deletion hazard (E-07).

## Deferred / out of scope (with reason)

- The general stop protocol (levels, the durable stop-request flag, the shared `clean_shutdown`) belongs to the `runstop` Set and spec `c4gd2h`. The backlog item itself frames this work as the lane-specific acceptance test for `kjzlgw`'s graceful-quit invariant, so the split is agreed. If `runstop` Phase 0 lands first, E-05 should CALL its shutdown routine rather than duplicating one; if it has not, E-05's handler stands alone and Phase 0 absorbs it. State which situation held at execution time.
- `aw doctor --lanes` and `aw recover <run-id>` are owned by plan `2c122z` and are deliberately NOT added here (the item's fix sketch item 3 suggests them; this plan declines to duplicate them and E-06 says so).
- Durable lane-lifecycle ledger events and lease reconstruction after a crash are `2c122z` E-06's subject. E-04 reuses the drivers' EXISTING event path rather than pre-empting that design.
- Relocating run state out of the repo is plan `58ha43`. This plan writes lane records wherever the driver already writes them.

## Scope check

- Over-scope: none. `worktree_lease.py` carries F1/F2/F5/F6 and hosts E-01 through E-03; both driver modules host E-04 through E-06; the test module is new.
- BOTH DRIVERS ARE DECLARED DELIBERATELY, unlike sibling plan `z2isfg`, which fenced out `agy_runipd.py` and had to record the resulting asymmetry as a known defect. The lane allocation and interrupt paths are structurally mirrored in the two drivers, so a one-driver fix would leave `aw agy run` wedgeable by exactly the reported failure. E-07 case (g) enforces symmetry with a test rather than trusting it.
- Under-scope: NONE OUTSTANDING. One coordination point is named rather than left implicit: if `runstop` Phase 0's `clean_shutdown` exists at execution time, E-05 must call it instead of installing a competing handler, and the executor must record which case applied. That is a sequencing decision with a stated rule, not missing scope.
- Files that must stay green WITHOUT edits: any existing test asserting today's allocation failure behavior. Search for them before starting (grep the reported error substring and `allocate_worktree` across `tests/`); if one PINS the hard failure as correct, it is a characterization test of a defect and changing it is legitimate, but it must be called out in the record rather than quietly edited.

## Required tests / validation

- `tests/test_lane_allocation_idempotent.py` must pass with all seven cases in E-07. Falsifiability is MANDATORY and specific: (a), (b), (e), and (f) must be shown to FAIL against pre-fix code, with the actual failure output pasted.
- Case (e) is the most important assertion in this plan and must not be softened into a code-shape check. It must observe that after an interrupt, a work-holding lane's tip is reachable BY REFERENCE (a branch or an equivalent ref exists pointing at it), not merely that the object exists. F5 proves the object survives even when the branch is deleted, so an object-existence assertion would pass against the destructive behavior and prove nothing.
- Interrupt tests spawn real processes, so mark them `slow` per the repo convention and produce the full-suite evidence with the non-default invocation. Do NOT add `-n auto` or a second `-q`.
- BASELINE IS A MEASUREMENT, NOT A CONSTANT. Fast suite at `df731f1` during this sweep: `2880 passed, 3 skipped, 4 xfailed`. Take your own before/after readings with their HEAD and do not treat a mismatch as a regression you caused; concurrent agents are committing to both driver modules.
- End-to-end, the property the item actually asks for: start a run, interrupt it mid-lane, then run the SAME Set again and show it allocates successfully with no `already exists` failure. Paste both transcripts. Also paste `git worktree list` and `git branch --list 'aw/lane/*'` before and after, and confirm every lane you created was cleaned up and NO pre-existing lane was touched. This repo had five live lanes owned by another process at authoring time; removing one would break that run.
- `aw check-local-leaks . --agent` clean; `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- `teardown_worktree`'s comment calling the per-lane branch deletion "best-effort" and "not a correctness hazard" must be corrected as part of E-05, since F5 proves it is a data-safety hazard for a lane holding commits. That file is in `Scope-Paths`.
- `allocate_worktree`'s docstring claim that failure leaves "no partial worktree left claimed" must be corrected or made true by E-02, since a failed add leaves the branch (F6).
- Spec `c4gd2h`'s invariant that every stop leaves the system coherent with "partial worktree edits quarantined or restored" is the parent principle here. This plan implements the lane-specific case and needs no spec text change, but the executor should record that the interpretation chosen was preserve-and-report rather than relocate, consistent with `runstop` Phase 0.

## Open questions

### OQ-01: On an EMPTY same-base lane, adopt it or replace it?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ADOPT. Resolved from measurement, not preference. A lane created by `git worktree add -b <branch> <path> <base_sha>` is the base commit exactly, so an EMPTY lane at the requested base is byte-identical to what a fresh allocation would produce; replacing it would mean a delete plus a create that can only fail in more ways, and the delete path is the one F5 shows to be dangerous. Adoption also keeps the resumable-run case working, which is the item's stated requirement that `aw oc run resume` cannot get past its own debris. The safety condition is that adoption applies ONLY when the base matches, which E-01 verifies via ancestry; a FOREIGN lane is attempt-scoped instead.

### OQ-02: Attempt-scoped name, or reuse-with-a-suffix, and does the lane id need a run id?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ATTEMPT-SCOPED SUFFIX ON THE EXISTING SANITIZER, and do NOT introduce a run-id-keyed naming scheme in this plan. Research `x03wgn` Section 4 recommends the fuller `aw/lane/<run-id>/<lane-id>/<attempt-id>` shape, but adopting that here would change lane identity repo-wide and collide with `2c122z`, which is mid-flight in a LIVE run and already reasons about lane naming and lease reconstruction. The measured fact that decides it: the existing sanitizer already turns a suffixed lane id into a clean distinct branch and directory that coexist with the original (F3), so a suffix delivers the needed property with no identity change. If the fuller scheme is wanted, it is `2c122z`'s or a follow-up's call; say so in the record rather than half-adopting it.

### OQ-03: Should this plan wait for `runstop` Phase 0's shared `clean_shutdown`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, do not wait, but do not duplicate either. The item is a release blocker and its failure wedges runs today, whereas the `runstop` Set is a six-child sequence gated on a spec. The rule stated in Deferred applies: if `clean_shutdown` exists when this executes, E-05 CALLS it and adds only the lane-classification step; if it does not, E-05 installs its own handler and Phase 0 later absorbs it. Either way there must be exactly ONE lane-preservation decision in the codebase, and the executor must record which case applied so a reviewer can check that no second cleanup path appeared.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the classifier and a transcript showing all four classifications on a fixture repo: ABSENT before allocation, EMPTY after, HOLDS-WORK after a commit, and HOLDS-WORK for a clean-but-committed lane and a dirty-but-uncommitted lane as SEPARATE cases. Then paste the branch-only case from F2 being classified correctly, which proves the classifier consults refs and not merely directory existence.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the pre-fix failure (the verbatim `already exists` error) and then the post-fix success for the SAME sequence. Paste the adoption case showing no second worktree was created (`git worktree list` before and after). Paste the attempt-scoped case showing the original lane's tip sha and `git status --porcelain` are IDENTICAL before and after. Finally paste the failure-path proof from F6: induce a failing `git worktree add` and show `git branch --list 'aw/lane/*'` has no stray branch afterward.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste each of the three dispositions being observable from a real allocation. Paste the import list of `worktree_lease.py` proving it is still stdlib-only, and a grep showing no ledger or run-context import in that module, since plan `2c122z` E-06 depends on this property.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the durable record from a real allocation in BOTH drivers, read back from a FRESH process after the writer exited, showing lane id, branch, worktree path, base sha, and disposition. Name the existing event/state path reused and show no second store was introduced.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: FIRST state whether `runstop` Phase 0's `clean_shutdown` existed at execution time and which branch of OQ-03 you took. Then, for `SIGINT` AND `SIGTERM` separately, paste evidence that a HOLDS-WORK lane is byte-identical after the signal (tip sha and porcelain before and after) and that its branch STILL EXISTS, while an EMPTY lane is gone. Paste the corrected `teardown_worktree` comment. Paste proof that nothing was stashed, reset, or moved (a `git stash list` and the unchanged porcelain). Show both drivers, not one.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the interrupt report for a run with one empty and one work-holding lane, showing the operator can tell them apart without running git. Confirm no em or en dash. Confirm by grep that no new CLI verb or flag was added and that the reported facts come from the E-01 classifier rather than a second git probe.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste all seven cases passing. Paste the FALSIFIABILITY output for (a), (b), (e), (f) against pre-fix code as actual failures, not claims. For (e) specifically, paste the assertion text showing it checks REFERENCE reachability and not object existence, and show it FAILING when teardown is replaced with a blanket force teardown, since that is the F5 behavior it exists to catch. Paste (g) failing when only one driver is changed. Finally paste `git worktree list` and `git branch --list 'aw/lane/*'` showing only pre-existing lanes remain.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 7 E-leaves across 3 task groups, under the thresholds. Right-sizing checked per leaf: E-01 the classifier, E-02 the allocation policy, E-03 the caller-visible disposition, E-04 durable registration, E-05 the interrupt decision, E-06 the report, E-07 the tests. Each has its own falsifiable surface.

Open questions: ALL RESOLVED from measurement and from sibling-plan ownership boundaries. The maintainer should be aware of TWO judgment calls rather than hidden assumptions. First, OQ-02 declines research `x03wgn`'s fuller run-id-keyed lane naming in favor of a suffix, because adopting the full scheme would change lane identity while `2c122z` is mid-flight in a live run; if you want the full scheme, this plan should be re-scoped or the change assigned to `2c122z`. Second, OQ-03 does not wait for `runstop` Phase 0 and instead states a rule for either sequencing; if you would rather this land strictly after Phase 0, that is a scheduling decision only you can make, and the cost of waiting is that runs stay wedgeable in the meantime.

Scope fence: touch ONLY `agent_workflows/worktree_lease.py`, `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, and the new test module. Do NOT add `aw doctor --lanes` or `aw recover` (owned by `2c122z`), do NOT implement any stop LEVEL or the stop-request flag (owned by the `runstop` Set), do NOT change `ipd_lifecycle.py` (owned by `z2isfg` and `lbgzxg`), and do NOT introduce run-id-keyed lane naming (OQ-02). If it seems to need more, STOP and report.

CRITICAL SAFETY RULE FOR THE EXECUTOR, not optional: this repo had FIVE LIVE LANES owned by a RUNNING driver at authoring time (`2c122z`, `58ha43`, `7p9n2v`, `qcqhj7`, `rchpms`). Never remove, reset, or check out another party's lane worktree or branch, and never run a repo-wide `git worktree prune` or a wildcard branch delete. Create your own fixture repos for every test. If you create a lane while probing, remember that a failed `git worktree add` still creates the branch, so clean up branches as well as worktrees, and only the ones YOU made.

Honesty rule (HARD MUST): when you report tests or validation passed, paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Never claim a pass you did not run, and never reuse this plan's recorded baseline as if freshly measured.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, and never push. Before every commit run `git diff --cached --name-only` and unstage anything not modified by this plan. This is a SHARED CHECKOUT and both driver modules are under active concurrent edit by other sessions, so re-read them immediately before editing and locate code by SYMBOL. Line numbers are deliberately omitted from this plan for that reason.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand. Do not create or push a git tag or release.
