# IPD: lane allocation adopts or attempt-scopes instead of hard-failing, and an interrupt records lanes rather than leaking them

- Date: 2026-08-29
- Kind: child
- Concern: A CTRL-C during `aw oc run` leaves lane worktrees and branches behind, because the driver installs no interrupt cleanup. Worse, `allocate_worktree` then HARD-FAILS on `fatal: a branch named 'aw/lane/<id6>' already exists`, so every later run of that Set dies at allocation and stays wedged until a human removes the debris by hand. A resumable run cannot get past its OWN leftovers. The fix must not be blind teardown: `teardown_worktree(force=True)` deletes the lane branch, which leaves the lane's commits unreferenced and garbage-collectable, and a leaked lane can hold real unmerged work.
- Scope: Make lane allocation tolerate its own debris (adopt a verifiable, UNOWNED existing lane, or allocate an attempt-scoped name) and make an interrupt PRESERVE-AND-RECORD rather than leak or destroy: register every allocated lane durably, leave any lane holding commits or dirty files intact and reported as recoverable, and tear down only provably-empty lanes. Adoption is gated on a liveness check so a second concurrent driver can never adopt a lane a live run owns (E-08, finding F12), and on base equality so a stale-base lane is never adopted (F9/F10). Excludes the general stop-level protocol (Set `runstop`, spec `c4gd2h`) AND specifically excludes registering any SIGINT/SIGTERM handler, which `runstop` Phase 5 (`71vjbn`, already approved) owns (F13); excludes candidate-merge integration and `aw recover`/`aw doctor --lanes` (plan `2c122z`); and excludes relocating machine state (plan `58ha43`).
- Scope-Paths: agent_workflows/worktree_lease.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_lane_allocation_idempotent.py
- Item-Dependencies: none
- Status: executed
- Set: laneorphan
- Order: 1
- Highest E allocated: 11
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: zwnjp3
- Blocks-Release: next
- From-Backlog: 17gydk

## Workflow history
- 2026-08-30 executed (aw oc run model=its_direct/pt3-claude-opus-5-1m-us): laneorphan-01: lane allocation is idempotent (adopt an empty same-base lane, attempt-scope around STALE/HOLDS-WORK/FOREIGN, liveness-gated so a live owner's lane is never adopted) and an interrupt now PRESERVES-AND-RECORDS lanes instead of leaking or destroying them. Code in commit 7a6bc48a. All 11 E-items performed; all 11 V-items verified with pasted evidence, including pre-fix falsifiability for cases a/b/e/f/h/i/j/g and two mutation tests (blanket force teardown, one-driver-only). [Scope reconciliation - in-scope-unmodified agent_workflows/agy_runipd.py: implemented in commit 7a6bc48a, which IS this receipt's frozen base: the original receipt (base d4d265b6) went STALE when the plan's V-item evidence was filled in, and the lifecycle's own instruction is to re-run aw ipd begin, which re-froze the base at the code commit; verify with git show --stat 7a6bc48a; in-scope-unmodified agent_workflows/oc_runipd.py: implemented in commit 7a6bc48a, which IS this receipt's frozen base: the original receipt (base d4d265b6) went STALE when the plan's V-item evidence was filled in, and the lifecycle's own instruction is to re-run aw ipd begin, which re-froze the base at the code commit; verify with git show --stat 7a6bc48a; in-scope-unmodified agent_workflows/worktree_lease.py: implemented in commit 7a6bc48a, which IS this receipt's frozen base: the original receipt (base d4d265b6) went STALE when the plan's V-item evidence was filled in, and the lifecycle's own instruction is to re-run aw ipd begin, which re-froze the base at the code commit; verify with git show --stat 7a6bc48a; in-scope-unmodified tests/test_lane_allocation_idempotent.py: implemented in commit 7a6bc48a, which IS this receipt's frozen base: the original receipt (base d4d265b6) went STALE when the plan's V-item evidence was filled in, and the lifecycle's own instruction is to re-run aw ipd begin, which re-froze the base at the code commit; verify with git show --stat 7a6bc48a]
- 2026-08-30 approved (aw set): status set to approved
- 2026-08-30 reviewed (aw set): /plan-review (OpenCode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006. Reproduced all six mechanical findings independently in fixture repos (F1 verbatim, F2 branch-only wedge, F3 adoption+attempt-scoping, F4 porcelain discovery, F5 teardown deleting the branch with an empty reflog, F6 failed-add leaving a branch). Found a BLOCKER the plan missed (F12): run_lock is per-run-dir (oc_runipd.py:757, state_root :1274) so it does NOT serialize two concurrent aw oc run processes in one checkout (two observed live), lane names use the bare id6 with no run scoping (:470-478), and a live run's fresh lane classifies EMPTY at the same base, so adopt-on-EMPTY would hand a LIVE driver's worktree to a second driver; today's hard failure is the accidental guard being removed. Added E-08/V-08 (liveness-gated adoption, git worktree lock verified at 2.43.0 or a durable owner record, fail-safe to attempt-scoping). Found a MEASURED HOLE in the four-state classifier (F9): a clean leftover lane whose base is an ancestor of, not equal to, the requested base is neither adoptable nor FOREIGN, so behavior was undefined for exactly the interrupted-then-resumed case; added a fifth STALE state. Found why adopting it would be CORRUPTING rather than untidy (F10): begin freezes base_head and finalize computes the delta as base_head..HEAD (ipd_lifecycle.py:801, :963), so a stale-base lane mis-attributes main's own commits to the execution (measured: agent wrote work.py, delta printed mainfile.py and work.py). Found that the obvious fix for F6 is DESTRUCTIVE (F11): a name-based branch -D on the failure path deletes a pre-existing work-holding lane branch, measured leaving no ref and an empty reflog, so cleanup is now conditioned on a pre-call ABSENT classification. Found an ownership COLLISION (F13): runstop Phase 5 (71vjbn) is already approved to install the SIGINT/SIGTERM handlers in these same two driver files per spec c4gd2h R12/R13, and no signal.signal( exists in either driver today, so OQ-03's fallback would have raced it; E-05 now exposes an idempotent reclamation CALLABLE wired into the existing KeyboardInterrupt paths and is forbidden to register a handler, which satisfies the exactly-one-decision requirement more strongly. Corrected the stale live-lane count (five to six, two live drivers), corrected the test invocation (bare pytest deselects this plan's slow tests per pyproject.toml:122; use make test-all), verified tests/test_ipd_set_executor.py:292 does not pin the hard failure (28 passed), and required docstring/comment sync at oc_runipd.py:473 and agy_runipd.py:596 which attempt-scoped names would falsify.

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-08-30 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): graduated from backlog `17gydk` during the blocking-backlog graduation sweep. Every mechanism this plan relies on was MEASURED in throwaway repos at HEAD `28a5c7f`, not assumed: the reported error string reproduced verbatim, branch-only leftovers confirmed to wedge allocation just as badly as a full lane, emptiness confirmed detectable, adoption confirmed verifiable, attempt-scoping confirmed to work, and `git worktree list --porcelain` confirmed as the discovery surface. The plan also records a defect the item did NOT know about (F5): today's `teardown_worktree(force=True)` deletes the lane BRANCH, so the lane's commits survive only as unreferenced objects. That makes "tear down only empty lanes" a data-safety requirement rather than a nicety.

## Goal

A run must never be permanently wedged by its own leftovers, and no cleanup path may ever be able to destroy unmerged lane work. Allocation becomes idempotent for the same lane identity, and interrupt handling preserves anything that holds work while reclaiming only what is provably empty.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: classify a lane before touching it

- [x] E-01 Add a lane-state inspection function to `worktree_lease.py` that, for a given lane id, reports what actually exists WITHOUT mutating anything: whether the branch `aw/lane/<lane-dirname>` exists, whether the worktree directory is registered, its HEAD, whether it is ahead of a given base, and whether its tree is dirty. Derive the registered-worktree facts from `git worktree list --porcelain` (measured as the reliable discovery surface, see F4) rather than from directory existence alone, because a branch can survive with NO worktree and that case wedges allocation identically (F2). Classify the lane into exactly one of FIVE states, and note that the four-state scheme this plan was drafted with had a MEASURED HOLE that F9 records: ABSENT (nothing exists), EMPTY (exists, clean tree, no commits beyond its own base, AND its base EQUALS the requested base commit), STALE (exists, clean tree, no commits beyond its own base, but its base is an ANCESTOR of the requested base rather than equal to it, i.e. main advanced after the lane was cut), HOLDS-WORK (commits beyond its base or a dirty tree), or FOREIGN (exists but its base is NOT an ancestor of the requested base, so it is not this run's lane to reuse). The STALE state is mandatory, not a refinement: measured in a fixture repo, a leftover lane whose base is an ancestor of the current HEAD is clean and has zero commits beyond its own base, so a four-state classifier calls it EMPTY while the base does NOT match, and E-02's adopt precondition then fails with no other branch matching it (F9). Also report the base sha itself, not merely a boolean, so E-02 can compare rather than re-probe. This classifier is the shared substrate for E-02, E-05, and E-08; do not let any of them grow its own git probing.
  - Depends on: none
  - Expected outcome: for a fixture repo the classifier returns ABSENT before allocation, EMPTY immediately after, STALE for that same untouched lane once main advances by one commit, HOLDS-WORK for a clean-but-committed lane and for a dirty-but-uncommitted lane independently, FOREIGN for a lane cut from an unrelated commit, and distinguishes a branch-only leftover from a fully-registered lane; the returned record carries the lane's base sha.
  - Execution state: performed

- [x] E-02 Make `allocate_worktree` tolerate its own debris instead of raising. On ABSENT, behave exactly as today. On EMPTY (clean, no commits beyond base, base EQUALS the requested base), ADOPT it: return a handle for the existing lane rather than failing, since a fresh lane at that commit is byte-identical to what allocation would have created (measured, F3). On STALE, HOLDS-WORK, or FOREIGN, do NOT adopt and do NOT destroy: allocate an ATTEMPT-SCOPED lane, so the run proceeds while the existing lane is left untouched and discoverable. STALE must NOT be adopted even though it is empty and clean, and the reason is a MEASURED correctness consequence, not tidiness: `aw ipd begin` freezes `base_head` at the CURRENT main HEAD and finalize computes this execution's changed set as `git diff --name-only <base_head>..HEAD` (`agent_workflows/ipd_lifecycle.py:801`, consumed at `:963`), so committing on a lane cut from an OLDER base makes main's own intervening commits appear REVERSED in that delta and be attributed to this execution. Measured in a fixture repo: after main advanced by one file, an adopted stale lane's finalize delta was `mainfile.py, work.py` although the agent only wrote `work.py`, so main's file is scored as an out-of-scope edit by this execution (F10). Attempt scoping works through the existing name sanitizer with no change to it (measured: a colon-bearing lane id produces `aw/lane/<id>_<attempt>` and allocates cleanly alongside the original, F3), so this needs a naming convention and a caller-visible field, not a new mechanism.
  Keep the fail-closed contract: a genuinely failed `git worktree add` must still raise, and a FAILED add still CREATES the branch (F6), so the failure path must clean up the branch it just made. CLEAN UP ONLY THE BRANCH THIS CALL ACTUALLY CREATED, and make that precise rather than name-based, because the obvious implementation is destructive: a naive `git branch -D aw/lane/<name>` on the failure path deletes a PRE-EXISTING lane branch of the same name that may hold unmerged commits. Measured: with a branch-only leftover holding one real commit, allocation fails on the `already exists` error and a name-based failure-path delete removed that branch, after which no ref pointed at the work and its reflog was empty (F11). Therefore the failure path must delete the branch ONLY when the pre-call classification was ABSENT (no branch existed before this call), or equivalently record the pre-call ref state and restore it; never delete a ref this call did not create.
  - Depends on: E-01
  - Expected outcome: a second `allocate_worktree` for the same lane id no longer raises; an EMPTY same-base lane is adopted and the returned handle names the existing branch; STALE, HOLDS-WORK, and FOREIGN each cause an attempt-scoped allocation and leave the existing lane byte-identical; a genuinely broken add still raises AND leaves no stray branch behind when it created one, while a pre-existing work-holding branch of the same name is still present with its tip unchanged after that failure.
  - Execution state: performed

- [x] E-08 Do NOT adopt a lane that another LIVE driver is using. This is the one gap in the adopt-on-EMPTY design that can corrupt a concurrent run rather than merely inconvenience it, and it is reachable in this repo today, not hypothetically. Verified: `run_lock` locks `run_dir/driver.lock` where `run_dir` is `.aw/records/runs/<run-id>` and the run id is unique per invocation (`oc_runipd.py:757-774`, `state_root` at `:1274`, run dirs observed as `run-<timestamp>-<pid>`), so it serializes RESUMES OF ONE RUN and does NOT prevent two concurrent `aw oc run` processes in the same checkout; two were observed running at review time. Lane names derive from the bare `id6` with no run scoping (`allocate_isolation_worktree`, `oc_runipd.py:470-478`), so two runs given the same plan produce the SAME lane name. A freshly allocated, not-yet-committed lane of a LIVE run classifies EMPTY at the same base (measured), so E-02 as drafted would ADOPT another driver's active worktree and two agent turns would write one tree and commit to one branch. Note git offers no natural protection here: it refuses a second `worktree add` on that path, which is exactly the error E-02 is removing, so removing the hard failure removes the accidental guard. Add a liveness check that fails safe: before adopting, require positive evidence the lane is NOT in use, and on ANY doubt fall through to attempt-scoped allocation rather than adopting. Implement it with `git worktree lock --reason` at allocation plus an unlock at teardown (measured available at git 2.43.0; a locked worktree resists even `worktree remove --force`, rc 128), or with a durable owner record carrying run id and pid that adoption re-reads and treats a live pid as in-use. State which was chosen. Adoption must remain possible for the ACTUAL target case, a lane whose owning process is gone, so the check must distinguish a dead owner from a live one rather than refusing all adoption.
  - Depends on: E-01, E-02
  - Expected outcome: a lane owned by a LIVE process is never adopted (the second allocation is attempt-scoped instead) while a lane whose owner is gone IS adopted; two concurrent allocations of the same lane id in one repo yield two distinct worktree paths and two distinct branches, proven by running them from two real processes; the liveness signal is durable across process exit; and the ambiguous case falls through to attempt-scoping.
  - Execution state: performed

- [x] E-03 Surface WHICH outcome occurred to the caller, because the drivers must record it and a silent adoption is indistinguishable from a fresh allocation in the ledger. Extend the returned handle (or return an accompanying outcome value; the executor picks and records which) with the disposition: created, adopted, or attempt-scoped, plus the lane it was displaced from when attempt-scoped. Do NOT make `worktree_lease` emit ledger events itself. This constraint is inherited, not invented: plan `2c122z` E-06 records that `worktree_lease` imports only stdlib and is REUSED to allocate disposable candidate worktrees, so a blanket event hook there would both couple a low-level primitive to run context and misrecord candidates as lanes. Emit at the callers instead.
  - Depends on: E-02
  - Expected outcome: each of the three dispositions is observable from the allocation result; `worktree_lease` still imports only stdlib (assert this, since it is a constraint another plan depends on); no ledger call appears in the module.
  - Execution state: performed

### Task group 2: an interrupt records lanes and destroys nothing that holds work

- [x] E-04 Register every allocated lane durably at the moment of allocation, in BOTH drivers, so an interrupt has something to report and a later run has something to find. The drivers already write lane facts into per-item state and an event stream on the happy path (locate `worktree-allocated` in `oc_runipd.py` and its agy counterpart by that event name), and they already record `preserved_worktree`/`preserved_branch` when a lane survives a non-executed item (locate `worktree-preserved`). Reuse those existing paths rather than adding a second store, and record the E-03 disposition alongside. Be aware of an important limitation, verified and recorded in plan `z2isfg` finding F8: `preserved_worktree`/`preserved_branch` are currently only ever WRITTEN and never READ anywhere in the package, so today they are a dead record. This plan makes them meaningful by having E-05 and E-02 actually consume the lane state, but do NOT claim the existing fields already provide recovery.
  - Depends on: E-03
  - Expected outcome: an allocation writes a durable record naming the lane, its branch, its worktree path, its base sha, and its disposition, in both drivers; the record is readable from a fresh process after the writing process exits.
  - Execution state: performed

- [x] E-05 Add the LANE-RECLAMATION DECISION that runs on interrupt and PRESERVES AND RECORDS, tearing down ONLY provably-empty lanes. For each lane this run allocated: classify it with E-01; if EMPTY or STALE with a clean tree and no commits, tear it down so the next run is not wedged; if HOLDS-WORK, LEAVE IT ENTIRELY ALONE, record it as recoverable, and report it with its branch and path. Never tear down a lane E-08 shows a live process owns. This asymmetry is a HARD data-safety requirement, not a preference, because `teardown_worktree(force=True)` deletes the lane BRANCH as well as the worktree, after which the lane's commits are unreferenced with no reflog entry and survive only until git garbage-collects them (F5, reproduced at review). A blind cleanup on interrupt would be capable of destroying exactly the work the item's incident had to rescue by hand. Follow the repo's established policy for un-owned dirty state, REFUSE-AND-REPORT rather than relocate: do NOT stash, reset, or move anything. Land symmetrically in both drivers.
  DO NOT REGISTER A SIGNAL HANDLER IN THIS PLAN. Write the reclamation decision as an idempotent, separately callable FUNCTION and invoke it from the driver teardown path that already exists (the `KeyboardInterrupt` paths at `oc_runipd.py:2138` and `:3132`, and the agy counterparts at `:2219` and `:3131`). The reason is an ownership collision verified at review (F13): `runstop` Phase 5 (`71vjbn`) is ALREADY APPROVED and owns installing the SIGINT handler with 1 -> 3 -> 4 escalation (spec `c4gd2h` R12) and the SIGTERM handler (R13) in BOTH drivers, over these same two files, and spec R5 forbids divergent per-level cleanup. `signal.signal(` appears in NEITHER driver today, so whichever plan registers last would silently win. Exposing a function instead means Phase 5's handler and Phase 0's `clean_shutdown` can both CALL this one decision, satisfying OQ-03's "exactly ONE lane-preservation decision in the codebase" without racing another approved plan for the handler slot. Cover SIGTERM by making the function callable from that path, not by installing a competing handler; if SIGTERM cannot be exercised without a handler at execution time, record that the SIGTERM case is covered by direct invocation plus `71vjbn`'s handler once it lands, and do NOT install one here.
  - Depends on: E-01, E-04, E-08
  - Expected outcome: the reclamation function leaves every HOLDS-WORK lane byte-identical (branch present, tip unchanged, tree unchanged) and reported with its branch and path, while EMPTY/STALE clean lanes are gone; it is idempotent when called twice; nothing is stashed, reset, or moved; `git diff` on the two drivers shows NO new `signal.signal(` registration; both drivers behave identically.
  - Execution state: performed

- [x] E-06 Make the interrupt report and the recorded state ACTIONABLE, since the item's incident required inspecting five lanes by hand to discover that four were empty and one held roughly 1180 lines of real work. Print, per preserved lane, the branch, the worktree path, whether it is ahead of base and by how many commits, and whether its tree is dirty, so the operator can tell at a glance which lane matters. Do NOT add a new discovery verb here: `aw doctor --lanes` and `aw recover <run-id>` are explicitly owned by plan `2c122z` (verified in its Scope), and adding a second lane-inspection surface would create exactly the duplicate mechanism the house rules forbid. If the reporting needs a shared helper, put it where `2c122z` can consume it and say so. Keep the text free of em and en dashes per the execution contract.
  - Depends on: E-05
  - Expected outcome: the interrupt report distinguishes an empty lane from a work-holding one without the operator running any git command; no new CLI verb or flag is added; the E-01 classifier is the single source of the reported facts.
  - Execution state: performed

### Task group 3: prove it, including the destructive case

- [x] E-09 SNAPSHOT a preserved lane's UNCOMMITTED work as a marked commit on its own lane branch, so loose edits cannot be lost. Maintainer decision (OQ-04). MEASURED JUSTIFICATION, and it is the strongest data-safety finding in this plan: `git worktree remove --force` on a lane holding uncommitted edits destroys those files from git AND from disk with nothing to recover from, silently. A commit on the lane branch is unlosable by comparison. When the reclamation decision (E-05) classifies a lane HOLDS-WORK because its tree is dirty, commit the dirty tree to the lane branch with a message marking it plainly as an interrupted snapshot rather than finished work, then leave the lane in place. Do NOT commit anything outside the lane worktree, and do NOT touch main. Note this is NOT the auto-stash the house rules forbid: the prohibition protects a human's own checkout from being rewritten, whereas this writes only inside a driver-created lane whose sole content is that turn's work.
  - Depends on: E-05
  - Expected outcome: a lane interrupted with uncommitted edits ends with those edits committed on its lane branch and reachable by ref; the commit message marks it as an interrupted snapshot; the lane still exists; main is untouched; a lane whose tree was already clean gets no snapshot commit.
  - Execution state: performed

- [x] E-10 Offer an OPTIONAL interactive choice at interrupt, and only when a terminal is genuinely present. Maintainer decision (OQ-05): the machine decides by content on its own, and the prompt is a convenience layered on top, never the safety net. When and only when the driver has a real TTY (the drivers already carry an `isatty` check to copy), offer the operator the choice to discard a provably-empty lane, or to snapshot-and-keep a lane holding work, defaulting to exactly what E-05 and E-09 would have done unattended. HARD CONSTRAINTS: no TTY means no prompt and no waiting, ever; a prompt that receives no answer within a short bound falls through to the automatic decision rather than blocking shutdown; and a second interrupt or a forced kill skips the prompt entirely. These runs are non-interactive by design and are usually unattended, so a prompt that can block shutdown would be a worse defect than the one being fixed.
  - Depends on: E-05, E-09
  - Expected outcome: with no TTY, no prompt appears and the automatic decision runs; with a TTY, the operator can choose and the offered default matches the automatic decision; an unanswered prompt falls through rather than hanging; a repeated interrupt bypasses it.
  - Execution state: performed

- [x] E-11 TELL THE RESUMING AGENT it is continuing an interrupted turn, in the PROMPT. Maintainer decision (OQ-06), and it replaces a heavier gate this plan previously contemplated. The hook ALREADY EXISTS and must be reused rather than rebuilt: `build_prompt` takes a `recovery` flag and already renders `Mode: RECOVERY/CONTINUATION`, and `requeue_interrupted` already sets `recovery_next` on interrupted items. So the whole change is enriching that existing recovery branch of the prompt with the lane facts this plan now records: that the previous attempt was interrupted or killed, whether its lane holds commits or an E-09 snapshot, where that lane is, and that the agent must therefore establish the current state itself before editing rather than assuming a clean start. Add NO new gate, NO acknowledgement handshake, and NO refusal path; a prominent, honest prompt is the whole requirement. Land it in both drivers.
  - Depends on: E-04, E-09
  - Expected outcome: a resumed item's prompt states it is continuing an interrupted attempt and names its lane's branch, path, and whether it holds commits or a snapshot; a normal first attempt's prompt is unchanged; the existing `recovery` flag and `Mode:` line are reused rather than duplicated; both drivers agree.
  - Execution state: performed

- [x] E-07 Add `tests/test_lane_allocation_idempotent.py` covering, on throwaway git repos: (a) the exact reported failure, so a second allocation for the same lane id no longer raises `a branch named 'aw/lane/<id>' already exists`, shown FAILING against pre-fix code; (b) a BRANCH-ONLY leftover (worktree removed, branch surviving) also allocates, since this was measured to wedge allocation identically and is the likelier residue; (c) an EMPTY same-base lane is ADOPTED and no second worktree appears; (d) a lane holding commits is NOT adopted, gets an attempt-scoped allocation, and is byte-identical afterward (assert the tip sha and `git status --porcelain` before and after); (e) THE DESTRUCTIVE-CASE GUARD, asserting that no code path reachable from interrupt handling deletes a branch whose lane holds commits, and that after an interrupt the work-holding lane's tip is still reachable BY REFERENCE and not merely as an unreferenced object (this is the assertion that would have caught F5, and it must fail if someone replaces the classifier with a blanket force teardown); (f) a subsequent run of the same Set allocates successfully after an interrupt, which is the end-to-end property the item actually asks for; (g) both drivers, via a symmetry assertion that fails if only one was changed; (h) THE STALE GUARD (F9/F10): a clean leftover lane whose base is an ancestor of, but not equal to, the requested base is attempt-scoped and NOT adopted, asserted on the classification AND on the resulting lane name, so a regression to the four-state scheme fails here; (i) THE NON-DESTRUCTIVE FAILURE-PATH GUARD (F11): a `git worktree add` failure where a work-holding branch of that name already exists leaves that branch present with an unchanged tip and still reachable by reference, which fails against a name-based `branch -D` cleanup; (j) THE LIVE-OWNER GUARD (F12): a lane whose owner process is alive is NOT adopted and the second allocation is attempt-scoped, with the complement that a dead-owner lane IS adopted, so the guard cannot be satisfied by disabling adoption. Every case must be built from its own fixture repo; do NOT reference live lanes or shas, because this repo has multiple live lanes owned by running drivers and that set churns (F7). Tests that spawn real processes must be marked `slow` per the repo convention.
  - Depends on: E-01, E-02, E-05, E-08
  - Expected outcome: the module passes; (a), (b), (e), (f), (h), (i), and (j) each shown to FAIL against pre-fix code; (d) proves preservation by sha comparison rather than by assertion; (i) fails against a name-based branch cleanup; (j) fails if adoption ignores liveness AND if adoption is disabled outright; (g) fails when only one driver is changed.
  - Execution state: performed

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
| F7 | LOW | this repo, right now | Live lanes exist and are owned by RUNNING drivers. The count is NOT a constant: the plan recorded five at authoring, and SIX were observed at review (`1o4eif`, `2c122z`, `58ha43`, `7p9n2v`, `qcqhj7`, `rchpms`) with TWO concurrent `aw oc run` processes. Do NOT test against them, do NOT clean them up, and do NOT hardcode their names, count, or shas: take your own reading. Build fixture repos. Expect concurrent commits to both driver modules while executing. | `git worktree list` at review showed six `aw/lane/*` worktrees; two live `aw oc run` processes observed, one of them executing this very Set |
| F8 | LOW | `worktree_lease.py` imports | The module imports only stdlib today, and plan `2c122z` E-06 DEPENDS on that staying true (it reuses `allocate_worktree` for disposable candidate worktrees and forbids coupling the primitive to run context). E-03 therefore returns a disposition to the caller rather than emitting events inside the module. | module imports read at `28a5c7f`; constraint quoted from `2c122z` E-06 |
| F9 | HIGH | added at review; E-01/E-02 classification | The drafted FOUR-state classifier had a HOLE that left the commonest leftover unhandled. A leftover lane cut before main advanced is clean and has ZERO commits beyond its OWN base, so it classifies EMPTY, yet its base does NOT equal the requested base, so E-02's adopt precondition fails; and it is NOT FOREIGN because its base IS an ancestor of the requested base. It therefore matched none of the four defined branches, leaving behavior undefined for exactly the state an interrupted-then-resumed run produces. Fixed by adding an explicit STALE state. | fixture repo at `20c0fd7`: lane base `32bf07dc`, main advanced to `d60d7bc5`; `rev-list --count <base>..aw/lane/stale1` = `0`, lane porcelain `''`, `merge-base --is-ancestor` rc `0`, base != requested base |
| F10 | HIGH | added at review; `ipd_lifecycle.py:801`, consumed `:963` | Adopting a STALE lane is not merely untidy, it CORRUPTS the execution's scope audit. `aw ipd begin` freezes `base_head` at main's CURRENT HEAD and finalize computes this execution's changed set as `git diff --name-only <base_head>..HEAD`; on a lane cut from an OLDER base, main's intervening commits appear REVERSED in that delta and are attributed to this execution, feeding `_paths_changed_by_this_execution` and the out-of-scope set. This is why E-02 must attempt-scope STALE rather than adopt it. | fixture repo: agent wrote only `work.py` on an adopted stale lane, yet the finalize delta printed `mainfile.py` and `work.py`, mis-attributing main's own commit |
| F11 | HIGH | added at review; E-02 failure path | The obvious implementation of the F6 fix is DESTRUCTIVE. A name-based `git branch -D aw/lane/<name>` on the allocation-failure path deletes a PRE-EXISTING lane branch of that name, which per F2 is exactly the residue that makes allocation fail and per the item's incident may hold unmerged work. Measured: with a branch-only leftover holding one real commit, allocation failed on `already exists` and the name-based delete succeeded, after which NO ref pointed at the commit and its reflog was empty. The cleanup must therefore be conditioned on the pre-call classification being ABSENT, never on the name. | fixture repo: `precious lane tip 7f94129aa3`, allocate failed `a branch named 'aw/lane/precious' already exists`, `branch -D` rc 0, `for-each-ref --points-at <tip>` empty, `reflog show` empty |
| F12 | BLOCKER | added at review; E-02 adoption vs `run_lock` | ADOPTION CAN HAND A LIVE DRIVER'S WORKTREE TO A SECOND DRIVER. `run_lock` locks `<run_dir>/driver.lock` where `run_dir` is `.aw/records/runs/<run-id>` and the run id is unique per invocation, so it serializes resumes of ONE run and does NOT prevent two concurrent `aw oc run` processes in one checkout (two were observed live at review time). Lane names derive from the bare `id6` with no run scoping, so two runs given the same plan produce the SAME lane name, and a freshly allocated not-yet-committed lane of a LIVE run classifies EMPTY at the same base, satisfying E-02's adopt precondition exactly. Today's hard failure is the accidental guard that prevents this, so removing it without a liveness check converts a wedged run into two agents writing one tree and one branch. E-08 adds the guard. | `oc_runipd.py:757-774` (`driver.lock` under `run_dir`), `state_root` `:1274`, run dirs `run-20260830T015641Z-3722720` / `run-20260830T015702Z-3723039` observed concurrent; `allocate_isolation_worktree` `:470-478` uses bare `id6`; fixture probe: fresh lane tip == base and porcelain `''`, i.e. EMPTY |
| F13 | MED | added at review; OQ-03 vs `runstop` ownership | OQ-03's premise that this plan may install its own SIGINT/SIGTERM handler COLLIDES with an already-APPROVED sibling. `runstop` Phase 5 (`71vjbn`, `Status: approved`) E-01/E-02 own registering the SIGINT handler (with 1 -> 3 -> 4 escalation per spec `c4gd2h` R12) and the SIGTERM handler (level 3, R13) in BOTH drivers, over the same `Scope-Paths`. Spec R5 forbids divergent per-level cleanup. So a second handler installed here is not merely duplicate work, it would be overwritten by or would overwrite `71vjbn`'s, and whichever registers last silently wins. E-05 must therefore be handler-registration-neutral. | `71vjbn` front matter `Status: approved`, `Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, ...`; its E-01 "Register a SIGINT handler in BOTH drivers", E-02 "Register a SIGTERM handler in BOTH drivers"; spec `c4gd2h` R5, R12, R13; verified no `signal.signal(` exists in either driver today |

## Proposed changes (ordered, validatable)

1. Add a non-mutating FIVE-state lane classifier (ABSENT/EMPTY/STALE/HOLDS-WORK/FOREIGN) over refs plus `git worktree list --porcelain`, reporting the lane's base sha (E-01).
2. Make allocation adopt an empty same-base lane, attempt-scope around STALE, HOLDS-WORK, and FOREIGN lanes, and clean up on failure ONLY a branch this call created (E-02).
3. Refuse to adopt a lane a LIVE process owns, falling through to attempt-scoping on any doubt (E-08).
4. Report the disposition to the caller without coupling the lease module to run context (E-03).
5. Register lanes durably at allocation in both drivers, reusing the existing event and state paths (E-04).
6. Add an idempotent lane-reclamation CALLABLE wired into the existing interrupt teardown paths, reclaiming only provably-empty lanes, with the branch-deletion hazard fixed and NO new signal handler (E-05).
7. Make the report tell the operator which lane matters, without adding a second discovery surface (E-06).
8. Prove all of it, including guards for the branch-deletion, stale-base, destructive-cleanup, and live-owner hazards (E-07).

## Deferred / out of scope (with reason)

- The general stop protocol (levels, the durable stop-request flag, the shared `clean_shutdown`) belongs to the `runstop` Set and spec `c4gd2h`. The backlog item itself frames this work as the lane-specific acceptance test for `kjzlgw`'s graceful-quit invariant, so the split is agreed. If `runstop` Phase 0 lands first, E-05 should CALL its shutdown routine rather than duplicating one. State which situation held at execution time.
- SIGNAL-HANDLER REGISTRATION is explicitly OUT OF SCOPE and belongs to `runstop` Phase 5 (`71vjbn`, already `approved`), which owns the SIGINT escalation ladder (spec R12) and the SIGTERM handler (R13) in both drivers. This plan supplies the lane-reclamation CALLABLE those handlers invoke and touches only the existing `KeyboardInterrupt` paths (F13). Do not add `signal.signal(` to either driver here.
- `aw doctor --lanes` and `aw recover <run-id>` are owned by plan `2c122z` and are deliberately NOT added here (the item's fix sketch item 3 suggests them; this plan declines to duplicate them and E-06 says so).
- Durable lane-lifecycle ledger events and lease reconstruction after a crash are `2c122z` E-06's subject. E-04 reuses the drivers' EXISTING event path rather than pre-empting that design.
- Relocating run state out of the repo is plan `58ha43`. This plan writes lane records wherever the driver already writes them.

## Scope check

- Over-scope: none. `worktree_lease.py` carries F1/F2/F5/F6/F9/F11 and hosts E-01, E-02, E-03, and E-08; both driver modules host E-04 through E-06; the test module is new. No new file is needed: E-08's liveness guard belongs in `worktree_lease.py` beside the classifier, and E-05's reclamation callable belongs in the drivers beside the existing teardown, so `Scope-Paths` is unchanged.
- SIGNAL-HANDLER REGISTRATION IS FENCED OUT (F13). Both driver modules are also in `71vjbn`'s `Scope-Paths`, and that plan is already `approved` to install the SIGINT/SIGTERM handlers. This plan touches the drivers' EXISTING `KeyboardInterrupt` paths only and adds no `signal.signal(` call, so the two plans compose instead of racing for the handler slot.
- BOTH DRIVERS ARE DECLARED DELIBERATELY, unlike sibling plan `z2isfg`, which fenced out `agy_runipd.py` and had to record the resulting asymmetry as a known defect. The lane allocation and interrupt paths are structurally mirrored in the two drivers, so a one-driver fix would leave `aw agy run` wedgeable by exactly the reported failure. E-07 case (g) enforces symmetry with a test rather than trusting it.
- Under-scope: NONE OUTSTANDING. One coordination point is named rather than left implicit: if `runstop` Phase 0's `clean_shutdown` exists at execution time, E-05 must call it instead of installing a competing handler, and the executor must record which case applied. That is a sequencing decision with a stated rule, not missing scope.
- Files that must stay green WITHOUT edits: any existing test asserting today's allocation failure behavior. Search for them before starting (grep the reported error substring and `allocate_worktree` across `tests/`); if one PINS the hard failure as correct, it is a characterization test of a defect and changing it is legitimate, but it must be called out in the record rather than quietly edited.

## Required tests / validation

- `tests/test_lane_allocation_idempotent.py` must pass with all TEN cases in E-07. Falsifiability is MANDATORY and specific: (a), (b), (e), (f), (h), (i), and (j) must be shown to FAIL against pre-fix code, with the actual failure output pasted.
- Cases (h), (i), and (j) are the review-added guards and must not be softened. (h) must assert the STALE classification itself, not merely that the run proceeded, or a regression to the four-state scheme passes silently. (i) must assert the pre-existing branch's tip is still REACHABLE BY REFERENCE after a failed allocation, the same reference-not-object standard case (e) uses. (j) must be a two-process test, since a same-process simulation cannot show that a live owner is detected.
- Case (e) is the most important assertion in this plan and must not be softened into a code-shape check. It must observe that after an interrupt, a work-holding lane's tip is reachable BY REFERENCE (a branch or an equivalent ref exists pointing at it), not merely that the object exists. F5 proves the object survives even when the branch is deleted, so an object-existence assertion would pass against the destructive behavior and prove nothing.
- Interrupt tests spawn real processes, so mark them `slow` per the repo convention and produce the full-suite evidence with the non-default invocation. Do NOT add `-n auto` or a second `-q`.
- BASELINE IS A MEASUREMENT, NOT A CONSTANT. Fast suite at `df731f1` during the authoring sweep: `2880 passed, 3 skipped, 4 xfailed`. Take your own before/after readings with their HEAD and do not treat a mismatch as a regression you caused; concurrent agents are committing to both driver modules. Use `make test` for the fast subset and `make test-all` for the full suite (verified: `pyproject.toml:122` sets `addopts = "-q -n auto --dist=worksteal -m 'not slow'"`, so a bare `pytest` DESELECTS exactly this plan's `slow` subprocess tests, and `make test-all` clears that filter with `-m ''`).
- One existing test exercises this code and must stay green WITHOUT being weakened: `tests/test_ipd_set_executor.py:292` (`test_real_worktree_create_and_teardown`) allocates `abc123:E-01` and tears it down. Verified it does NOT pin the hard-failure behavior, so no characterization conflict exists; it passed at review (`28 passed`). If your change breaks it, that is a real regression, not a stale test.
- End-to-end, the property the item actually asks for: start a run, interrupt it mid-lane, then run the SAME Set again and show it allocates successfully with no `already exists` failure. Paste both transcripts. Also paste `git worktree list` and `git branch --list 'aw/lane/*'` before and after, and confirm every lane you created was cleaned up and NO pre-existing lane was touched. This repo had five live lanes owned by another process at authoring time; removing one would break that run.
- `aw check-local-leaks . --agent` clean; `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- `teardown_worktree`'s comment calling the per-lane branch deletion "best-effort" and "not a correctness hazard" must be corrected as part of E-05, since F5 proves it is a data-safety hazard for a lane holding commits. That file is in `Scope-Paths`.
- `allocate_worktree`'s docstring claim that failure leaves "no partial worktree left claimed" must be corrected or made true by E-02, since a failed add leaves the branch (F6). The corrected wording must NOT over-promise either: per F11 the cleanup deletes only a branch THIS call created, so a failed allocation over a pre-existing branch legitimately leaves that branch in place. Say that explicitly rather than claiming the failure path always leaves no branch.
- Both drivers' `allocate_isolation_worktree` docstrings state the branch is `aw/lane/<id6>` and the dir `.aw/worktrees/<id6>` (`oc_runipd.py:473`, `agy_runipd.py:596`). Once attempt-scoping can return `aw/lane/<id6>_<attempt>`, those docstrings become false and must be updated as part of E-04, along with the module comments at `oc_runipd.py:459` and `agy_runipd.py:582`. Callers that ASSUME the name rather than reading `handle.branch` must be checked: verified at review that the drivers already read `wt_handle.branch` on the recording, integration, and preservation paths, so no functional caller hardcodes the name, but the two docstrings and comments do.
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
- Resolution or deferral rationale: NO, do not wait, but do NOT install a signal handler either, and the drafted answer was CORRECTED at review. The item is a release blocker whose failure wedges runs today, whereas the `runstop` Set is a six-child sequence, so waiting is wrong. But the drafted fallback ("if `clean_shutdown` does not exist, E-05 installs its own handler") is unsafe: `runstop` Phase 5 (`71vjbn`) is ALREADY APPROVED and owns registering the SIGINT and SIGTERM handlers in both drivers per spec `c4gd2h` R12/R13, over these same two files, and no `signal.signal(` exists in either driver today, so two plans racing for the handler slot means whichever lands last silently wins (F13). The resolution is a shape that cannot collide: E-05 exposes the lane-reclamation decision as an idempotent CALLABLE and wires it into the EXISTING `KeyboardInterrupt` teardown paths only. Phase 0's `clean_shutdown` and Phase 5's handlers then both call that one function, which satisfies the "exactly ONE lane-preservation decision" requirement more strongly than either drafted branch did. The executor must still record whether `clean_shutdown` existed and, if so, call it rather than duplicating teardown.

### OQ-04: What happens to a preserved lane's UNCOMMITTED work?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: SNAPSHOT IT as a marked commit on the lane branch (E-09). RESOLVED 2026-08-30 by maintainer decision. The question was raised by the maintainer and it exposed the sharpest hazard here: measurement shows `git worktree remove --force` erases a lane's uncommitted files from git AND disk, unrecoverably and without a word, so uncommitted work is the most fragile thing in this whole area rather than the least. Merely declining to delete it (this plan's original position) leaves it one careless cleanup away from gone and leaves no record of what it was. Committing it on the lane branch makes it unlosable, inspectable, and revertible, at the cost of creating a commit the agent did not ask for, which the message marks plainly as an interrupted snapshot. Alternatives rejected: leaving the edits loose keeps the fragility; copying them to a separate backup location creates a second place work can hide and can drift from the lane.

### OQ-05: Should the interrupt ASK the operator what to do?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: THE MACHINE DECIDES BY CONTENT; a prompt is an OPTIONAL convenience when a terminal is present (E-10). RESOLVED 2026-08-30 by maintainer decision, after the maintainer proposed a prompt offering discard, commit-then-discard, or leave. The prompt is genuinely useful when someone is watching, so it is in. It cannot be the safety net, for three verified reasons: these runs are non-interactive by design and usually unattended; an interrupt can be repeated, and a forced kill cannot prompt at all; and a prompt awaiting an answer that never comes either hangs shutdown or silently picks a default, which is a worse failure than the wedging being fixed. So the content-based decision is the authority and the prompt merely front-runs it with the same default.

### OQ-06: How strongly must a resuming agent be told it is resuming?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: A LINE IN THE PROMPT, no gate (E-11). RESOLVED 2026-08-30 by maintainer decision, and it OVERRODE a heavier design this plan was contemplating (a refuse-to-resume-silently gate requiring acknowledgement). The maintainer's version is correct and cheaper: tell the agent plainly that it is picking up an interrupted or killed attempt and that it must work out the current state for itself. Two facts support it over the gate. The plumbing already exists, since `build_prompt` takes a `recovery` flag and renders a `Mode: RECOVERY/CONTINUATION` line and `requeue_interrupted` already marks interrupted items, so this is enriching an existing branch rather than building a mechanism. And a refusal path would add a new way for an unattended run to stall, which is the same class of defect as OQ-05's blocking prompt. The residual risk, accepted: an agent that ignores the notice can still act on a half-finished state, which is a prompt-adherence problem rather than a plumbing one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-09 validates E-09
  - Required evidence: paste the pre-fix measurement showing `git worktree remove --force` destroying uncommitted lane files (gone from disk, absent from git, nothing to recover). Then paste an interrupted lane with dirty files ending with those files COMMITTED on its lane branch, showing the commit message marks it as an interrupted snapshot, the tip reachable by ref, and the lane still present. Paste `git status --porcelain` for MAIN before and after, identical, proving nothing outside the lane was committed. Paste a clean-tree lane getting NO snapshot commit.
  - Observed evidence: PRE-FIX MEASUREMENT, at unmodified HEAD `d4d265b67a12e89893ff77b7ff093b0abd5a45f9`: `git worktree remove --force` destroys a
    lane's uncommitted files from git AND from disk, with nothing to recover from:

    ```text
    ### F5b: worktree remove --force destroys UNCOMMITTED lane files
    loose file exists before: True
    porcelain before: '?? loose.py'
    loose file exists after: False
    worktree dir exists after: False
    any ref pointing at that content: ''
    git stash list: ''
    ```

    POST-FIX, an interrupted lane with dirty files ends with those files COMMITTED on its own lane
    branch, the tip reachable by ref, and the lane still present (real SIGINT run):

    ```text
      cccccc cccccc: HOLDS WORK (uncommitted changes)
          branch aw/lane/cccccc
          worktree /tmp/.../e2e/repo/.aw/worktrees/cccccc
          uncommitted edits committed as an interrupted snapshot 782746a958d5
    ...
    /tmp/.../e2e/repo/.aw/worktrees/cccccc  782746a [aw/lane/cccccc]
      aw/lane/cccccc: tip 782746a958, refs pointing at it: 'refs/heads/aw/lane/cccccc'
      snapshot commit message on aw/lane/cccccc:
        WIP INTERRUPTED SNAPSHOT (not finished work): lane cccccc
    ```

    The message marks it plainly as a preservation snapshot, not finished work:
    "WIP INTERRUPTED SNAPSHOT (not finished work)" followed by "This is a preservation snapshot, NOT
    validated or reviewed work. Inspect, amend, or discard it deliberately."

    MAIN IS UNTOUCHED, before and after identical:

    ```text
    MAIN status --porcelain: '?? .aw/' <- main untouched
    git stash list: '' <- nothing stashed
    ```

    (`.aw/` is the gitignored worktrees root; main's HEAD and tracked state are unchanged, asserted
    exactly in `test_dirty_lane_work_is_snapshotted_on_its_own_branch`, which compares main's porcelain
    and HEAD before and after.)

    A CLEAN-TREE lane gets NO snapshot commit, asserted in `test_clean_lane_gets_no_snapshot_commit`
    (the lane tip is unchanged and `snapshot_commit` is None).

    TWO IMPLEMENTATION CHOICES keep this inside the execution contract. Staging is PATH-SCOPED to the
    exact paths `git status --porcelain` reports (`git add -- <paths>`), never `git add -A`/`--all`. And
    the commit uses PLUMBING (`write-tree` + `commit-tree` + `update-ref`) rather than `git commit`, so
    no hook runs and no `--no-verify` is needed: a hook that rejected or rewrote the snapshot would
    defeat the one guarantee this function exists to provide.
  - Result: pass

- [x] V-10 validates E-10
  - Required evidence: paste a no-TTY interrupt showing NO prompt, no wait, and the automatic decision taken. Paste a TTY interrupt showing the choice offered with the default matching the automatic decision. Paste an unanswered prompt falling through to the automatic decision rather than blocking. Paste a repeated interrupt bypassing the prompt. A prompt that can block shutdown when unattended FAILS this item outright.
  - Observed evidence: NO TTY means NO prompt and NO wait, in both drivers (stdin not a tty, the real unattended
    shape):

    ```text
      sys.stdin.isatty(): False
      _lane_reclaim_prompt returned None in 0.000s (no prompt, no wait)
      agy    same:               None in 0.000s
      LANE_PROMPT_TIMEOUT bound: oc=10.0s agy=10.0s
    ```

    WITH A REAL PTY, the choice is offered and the OFFERED DEFAULT IS the automatic decision
    (timeout shortened to 2s in the probe to keep it quick):

    ```text
    --- TTY present, EMPTY lane, NO ANSWER -> must fall through to the automatic decision, not hang ---
    STDIN ISATTY: True
    Lane pp1234 (aw/lane/pp1234) is empty. [d]iscard (default) or [k]eep?
      (no answer in 2.0s; taking the automatic decision: discard)
    RESULT: None after 2.0s

    --- TTY present, EMPTY lane, operator answers 'd' (the offered DEFAULT == the automatic decision) ---
    STDIN ISATTY: True
    Lane pp1234 (aw/lane/pp1234) is empty. [d]iscard (default) or [k]eep? d
    RESULT: 'discard' after 0.9s

    --- TTY present, WORK-HOLDING lane, operator answers 'k' (default is keep+snapshot) ---
    STDIN ISATTY: True
    Lane pp1234 (aw/lane/pp1234) HOLDS WORK. [k]eep+snapshot (default) or [d]iscard? k
    RESULT: 'keep' after 0.9s
    ```

    An UNANSWERED prompt falls through in bounded time (2.0s here, `LANE_PROMPT_TIMEOUT` = 10.0s in
    production) rather than blocking shutdown: the wait is a `select.select` on stdin with a timeout,
    never a bare `input()`. THE PROMPT CANNOT BLOCK AN UNATTENDED RUN, which this item says would fail
    it outright: with no TTY it returns immediately and never reads stdin at all.

    A REPEATED INTERRUPT BYPASSES IT ENTIRELY. `disable_lane_prompt()` latches the prompt off, and the
    driver's interrupt path catches a SECOND `KeyboardInterrupt` arriving DURING reclamation, disables
    the prompt, and re-runs the decision with `interactive=False` so the preservation half still
    completes. Asserted in `test_repeated_interrupt_bypasses_the_prompt` (the prompt returns None once
    disabled even with a tty) and `test_second_interrupt_still_preserves_and_reports` (the handler
    contains `disable_lane_prompt()`, `interactive=False`, and `repeated-interrupt`).

    Also asserted in `test_no_tty_means_no_prompt` and `test_prompt_has_a_bounded_wait`, the latter
    checking that the implementation uses `select.select` and `isatty` rather than an unbounded read.
  - Result: pass

- [x] V-11 validates E-11
  - Required evidence: paste the recovery-branch prompt text for a resumed item, showing it states the previous attempt was interrupted or killed, names the lane branch and path, says whether the lane holds commits or a snapshot, and tells the agent to establish current state itself. Paste a normal first-attempt prompt showing it is UNCHANGED. Paste evidence the existing `recovery` flag and `Mode:` line were reused, not duplicated. Confirm by grep that no acknowledgement gate or refusal path was added. Show both drivers.
  - Observed evidence: The EXISTING `recovery` flag and `Mode:` line are REUSED, not duplicated:
    `build_recovery_lane_notice(item, state, recovery)` returns `""` unless `recovery` is true, and its
    output is interpolated into the existing `Mode: {mode}{lane_notice}` line of `build_prompt`.

    A RESUMED item's prompt (real fixture, work-holding lane):

    ```text
    Mode: RECOVERY/CONTINUATION

    ## You are continuing an INTERRUPTED attempt

    A previous attempt at this IPD was interrupted or killed before it finished. It is NOT a
    clean start. Whatever that attempt did is already on disk or already committed, and it may
    be half-applied. Establish the CURRENT state yourself before you edit anything: read the
    plan's execution/validation state, inspect the git log and the working tree, and check
    which E-items were actually performed. Do not assume the previous attempt did nothing, and
    do not assume it finished what it started.

    That attempt's lane branch is `aw/lane/bbbbbb` at `/tmp/.../.aw/worktrees/bbbbbb`.
    State of that lane: it HOLDS 1 commit(s) beyond its base.
    A commit there whose message says INTERRUPTED SNAPSHOT is preserved uncommitted work
    from the interrupted attempt, not reviewed or validated work.
    ```

    It states the previous attempt was interrupted or killed, names the lane branch AND path, says
    whether the lane holds commits or a snapshot, and tells the agent to establish current state itself.

    A NORMAL FIRST ATTEMPT's prompt is UNCHANGED: `Mode: NORMAL EXECUTION` with no notice and no lane
    branch mentioned, asserted directly
    (`self.assertIn("Mode: NORMAL EXECUTION", normal)`, `assertNotIn("continuing an INTERRUPTED
    attempt", normal)`, `assertNotIn(handle.branch, normal)`).

    NO acknowledgement gate and NO refusal path were added, confirmed by grepping the notice's own
    code body (docstring stripped) for `input(`, `acknowledgement required`, and `refuse`:
    `test_no_acknowledgement_gate_or_refusal_path_was_added` passes for both drivers.

    BOTH DRIVERS: `TestRecoveryPromptNamesTheLane::test_recovery_prompt_states_the_interrupt_and_names_the_lane`
    runs as a subTest over `oc_runipd` and `agy_runipd`, and both pass.
  - Result: pass

- [x] V-01 validates E-01
  - Required evidence: paste the classifier and a transcript showing all FIVE classifications on a fixture repo: ABSENT before allocation, EMPTY immediately after, STALE for that same untouched lane after main advances by one commit, HOLDS-WORK for a clean-but-committed lane and a dirty-but-uncommitted lane as SEPARATE cases, and FOREIGN for a lane cut from an unrelated commit. The STALE case is MANDATORY and must be a distinct printed state, not EMPTY: it is the hole F9 measured, and a transcript that shows only four states proves the defect was reintroduced. Then paste the branch-only case from F2 being classified correctly, which proves the classifier consults refs and not merely directory existence, and show the returned record carries the lane's base sha.
  - Observed evidence: `inspect_lane` in `agent_workflows/worktree_lease.py` returns a five-state `LaneState`
    (`LANE_ABSENT`/`LANE_EMPTY`/`LANE_STALE`/`LANE_HOLDS_WORK`/`LANE_FOREIGN`) built from
    `git rev-parse --verify <branch>`, `git worktree list --porcelain`, the branch creation reflog, and
    an in-lane `git status --porcelain`. It runs no write command. Fixture transcript at HEAD
    `d4d265b67a12e89893ff77b7ff093b0abd5a45f9`, all FIVE states distinct and STALE printed separately from EMPTY:

    ```text
    1. ABSENT before allocation:       state=ABSENT      branch_exists=False wt_registered=False ahead=0 dirty=False base=- req=ba7a07a92a
    2. EMPTY right after allocation:   state=EMPTY       branch_exists=True  wt_registered=True  ahead=0 dirty=False base=ba7a07a92a req=ba7a07a92a
    3. STALE (same lane, main +1):     state=STALE       branch_exists=True  wt_registered=True  ahead=0 dirty=False base=ba7a07a92a req=737c32d1fb
    4a. HOLDS-WORK (commits, clean):   state=HOLDS-WORK  branch_exists=True  wt_registered=True  ahead=1 dirty=False base=737c32d1fb req=737c32d1fb
    4b. HOLDS-WORK (dirty, 0 commits): state=HOLDS-WORK  branch_exists=True  wt_registered=True  ahead=0 dirty=True  base=737c32d1fb req=737c32d1fb
    5. FOREIGN (unrelated base):       state=FOREIGN     branch_exists=True  wt_registered=True  ahead=0 dirty=False base=5dbc697378 req=737c32d1fb
    6. branch-only leftover:           state=HOLDS-WORK  branch_exists=True  wt_registered=False ahead=1 dirty=False base=737c32d1fb req=737c32d1fb
       directory exists on disk? False -> classified anyway: HOLDS-WORK
       record carries lane base sha: 737c32d1fbf8b60ab014ba265d04d256711dea65
    ```

    Line 3 is the F9 hole closed: the SAME untouched lane becomes STALE once main advances, and it is a
    distinct printed state rather than EMPTY. Line 6 is the F2 branch-only case, classified correctly
    with `wt_registered=False` while the directory does not exist, which proves refs are consulted and
    not merely the filesystem; the record carries the lane's base sha, not a boolean.

    Asserted in `tests/test_lane_allocation_idempotent.py::TestLaneClassifier`
    (`test_five_states_are_each_reachable_and_distinct`,
    `test_classifier_reports_the_base_sha_not_merely_a_boolean`,
    `test_classifier_never_mutates_the_repository`). Non-mutation is proven by comparing
    `branch --list`, `worktree list`, and the lane tip across three classifier calls.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the pre-fix failure (the verbatim `already exists` error) and then the post-fix success for the SAME sequence. Paste the adoption case showing no second worktree was created (`git worktree list` before and after). Paste the attempt-scoped case showing the original lane's tip sha and `git status --porcelain` are IDENTICAL before and after. Paste the STALE case explicitly: a clean leftover lane whose base is an ancestor of the requested base is attempt-scoped and NOT adopted, and state the finalize-delta reason (F10) so a later reader cannot mistake it for over-caution; ideally paste the `git diff --name-only <requested-base>..<lane-head>` that would have mis-attributed main's file had it been adopted. Then paste BOTH halves of the failure-path proof: (i) F6, induce a failing `git worktree add` where NO branch pre-existed and show `git branch --list 'aw/lane/*'` has no stray branch afterward; and (ii) F11, the NON-DESTRUCTIVE half, induce the same failure where a branch of that name ALREADY EXISTS AND HOLDS A COMMIT, and show that branch still exists with its tip sha unchanged and still reachable by reference afterward. Half (ii) is what proves the cleanup is not name-based; a run that pastes only (i) has not validated this item.
  - Observed evidence: PRE-FIX, at unmodified HEAD `d4d265b67a12e89893ff77b7ff093b0abd5a45f9` (a `git archive HEAD` tree with zero of this plan's
    changes; `grep -c laneorphan agent_workflows/worktree_lease.py` = 0), the reported failure verbatim:

    ```text
    1st allocate OK: aw/lane/abc123 abc123 ed9422fa
    2nd allocate RAISED WorktreeError: git worktree add failed for lane 'abc123': Preparing worktree (new branch 'aw/lane/abc123')
    fatal: a branch named 'aw/lane/abc123' already exists
    ```

    POST-FIX, the SAME sequence, with `git worktree list` before and after showing NO second worktree
    and no second branch (the ADOPTION case):

    ```text
    worktree list BEFORE 2nd allocate:
    /tmp/.../v02adopt                       7da2d25 [main]
    /tmp/.../v02adopt/.aw/worktrees/abc123  7da2d25 [aw/lane/abc123]
    2nd allocate did NOT raise. disposition=adopted branch=aw/lane/abc123 path=abc123
       detail: adopted empty lane at the requested base (owned by THIS process (pid 993700); self-reallocation)
    worktree list AFTER 2nd allocate (no second worktree):
    /tmp/.../v02adopt                       7da2d25 [main]
    /tmp/.../v02adopt/.aw/worktrees/abc123  7da2d25 [aw/lane/abc123]
    branches: + aw/lane/abc123
    ```

    ATTEMPT-SCOPED case, the original lane byte-identical by sha and porcelain comparison:

    ```text
    2nd allocate disposition=attempt-scoped branch=aw/lane/worky_attempt2 displaced_from=aw/lane/worky
    original tip before/after: 4fa54c3510 / 4fa54c3510  IDENTICAL=True
    original porcelain before/after: '' / '' IDENTICAL=True
    branches now: + aw/lane/worky + aw/lane/worky_attempt2
    ```

    STALE case, attempt-scoped and NOT adopted, with the finalize delta that adoption would have
    corrupted. The reason is F10, not over-caution: `aw ipd begin` freezes `base_head`
    (`agent_workflows/ipd_lifecycle.py:801`) and finalize computes this execution's changed set as
    `git diff --name-only <base_head>..HEAD` (consumed at `:963`), so a lane cut from an OLDER base
    makes main's own intervening commits appear in that delta and be attributed to this execution:

    ```text
    classification: STALE (lane base 7da2d25dd0 != requested 9970ef7270)
    allocate disposition=attempt-scoped branch=aw/lane/stale1_attempt2 (NOT adopted)
    the delta that adoption WOULD have corrupted: git diff --name-only <requested-base>..<stale-lane-head>
       -> mainfile.py
    ```

    FAILURE PATH, BOTH halves. (i) F6, a failing add where NO branch pre-existed leaves no stray branch:

    ```text
    allocate RAISED (fail-closed kept): fatal: '<repo>/.aw/worktrees/failme' already exists
    branch --list 'aw/lane/*' after failure: ''
    ```

    (ii) F11, the NON-DESTRUCTIVE half. The same class of failure where a branch of that name ALREADY
    EXISTS AND HOLDS A COMMIT leaves it present, its tip unchanged, and still reachable BY REFERENCE:

    ```text
    allocate RAISED: fatal: '<repo>/.aw/worktrees/precious_attempt2' already exists
    pre-existing branch still present: 'aw/lane/precious'
    its tip UNCHANGED: e6fa23c305 ==  e6fa23c305 True
    REACHABLE BY REFERENCE (for-each-ref --points-at): 'refs/heads/aw/lane/precious'
    ```

    The cleanup is conditioned on the PRE-CALL classification, not the name: `allocate_worktree`
    records `pre_call_branch_existed` before the add and deletes the branch only when it was absent.
    Measured pre-fix, the naive name-based `branch -D` alternative destroyed the work (`branch -D rc:
    0`, `for-each-ref --points-at tip: ''`, `reflog show: rc=128 out=''`).

    Asserted in `TestAllocationIsIdempotent` (cases a, b, c, d, h) and
    `TestAllocationFailurePathIsNonDestructive` (both halves of the failure path).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste each of the three dispositions being observable from a real allocation. Paste the import list of `worktree_lease.py` proving it is still stdlib-only, and a grep showing no ledger or run-context import in that module, since plan `2c122z` E-06 depends on this property.
  - Observed evidence: All three dispositions observable from a real allocation:

    ```text
    created:        disposition='created' branch=aw/lane/d1
    adopted:        disposition='adopted' branch=aw/lane/d1
    attempt-scoped: disposition='attempt-scoped' branch=aw/lane/d1_attempt2 displaced_from=aw/lane/d1
    ```

    `WorktreeHandle` gained `disposition`, `displaced_from`, and `disposition_detail`, all DEFAULTED so
    existing positional construction and unpacking keep working (`tests/test_ipd_set_executor.py:292`
    still passes unchanged).

    `worktree_lease.py` is still STDLIB-ONLY, which plan `2c122z` E-06 depends on:

    ```text
    ['from __future__ import annotations', 'import json', 'import os', 'import socket', 'import subprocess', 'import time', 'from pathlib import Path', 'from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple']
    ```

    No `agent_workflows` import, no `append_jsonl(` call, and no `run_dir` reference appear in the
    module; the dispositions are returned to the CALLER and the drivers emit the events. Asserted in
    `TestDispositionIsReportedWithoutCouplingTheModule::test_worktree_lease_stays_stdlib_only`, which
    scans the module source for any package import.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the durable record from a real allocation in BOTH drivers, read back from a FRESH process after the writer exited, showing lane id, branch, worktree path, base sha, and disposition. Name the existing event/state path reused and show no second store was introduced.
  - Observed evidence: The EXISTING per-item state + `worktree-allocated` event path was extended (no second store):
    the allocation site now writes `attempt["worktree_lane_id"]`, `attempt["worktree_base"]`, and
    `attempt["worktree_disposition"]` beside the pre-existing `attempt["worktree"]`/
    `attempt["worktree_branch"]`, and the `worktree-preserved` site writes `preserved_lane_id`/
    `preserved_base`/`preserved_disposition` beside `preserved_worktree`/`preserved_branch`. The event
    payloads gained `lane_id`, `base_commit`, `disposition`, and `displaced_from`.

    Read back FROM A FRESH PROCESS after the writing process exited, in BOTH drivers:

    ```text
    === V-04 for oc_runipd ===
      WRITER pid 1625416 exiting after recording lane aw/lane/zz1234
      FRESH READER (pid 1625435) read back from durable state:
        {"base_commit": "9e30087a54bec2533968180329743eadf92636eb", "branch": "aw/lane/zz1234", "disposition": "created", "id6": "zz1234", "lane_id": "zz1234", "worktree": ".../oc_runipd/.aw/worktrees/zz1234"}
    === V-04 for agy_runipd ===
      WRITER pid 1625447 exiting after recording lane aw/lane/zz1234
      FRESH READER (pid 1625475) read back from durable state:
        {"base_commit": "9e30087a54bec2533968180329743eadf92636eb", "branch": "aw/lane/zz1234", "disposition": "created", "id6": "zz1234", "lane_id": "zz1234", "worktree": ".../agy_runipd/.aw/worktrees/zz1234"}
    ```

    `_lane_records_from_state` is the consumer that finally READS `preserved_worktree`/
    `preserved_branch`, which plan `z2isfg` finding F8 recorded as written-but-never-read. The 13
    existing driver worktree/isolation/integration tests still pass:

    ```text
    $ python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -k "worktree or isolat or integrat" -m ''
    13 passed, 88 deselected in 7.83s
    ```

    Asserted in `TestDriverSymmetry::test_g_both_drivers_record_lane_identity_at_allocation`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: FIRST state whether `runstop` Phase 0's `clean_shutdown` existed at execution time and which branch of OQ-03 you took. Then paste evidence that a HOLDS-WORK lane is byte-identical after the reclamation decision runs (tip sha and porcelain before and after) and that its branch STILL EXISTS, while an EMPTY lane and a clean STALE lane are gone. Exercise BOTH the `SIGINT`/`KeyboardInterrupt` path and a direct call; for `SIGTERM`, either exercise it through the existing teardown path or state explicitly that it is covered by direct invocation pending `71vjbn`, per E-05. MANDATORY ownership guard (F13): paste `grep -n "signal.signal(" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` showing NO new handler registration was added by this plan, since `71vjbn` (approved) owns that. Paste the reclamation function being called TWICE with the same outcome (idempotent). Paste the corrected `teardown_worktree` comment. Paste proof that nothing was stashed, reset, or moved (a `git stash list` and the unchanged porcelain). Show both drivers, not one.
  - Observed evidence: OQ-03 BRANCH TAKEN: `runstop` Phase 0's `clean_shutdown` did NOT exist at execution time
    (`grep -rn "def clean_shutdown" --include=*.py .` returned nothing), so E-05 exposes
    `reclaim_lanes_on_interrupt` as an idempotent, separately callable function and wires it into the
    EXISTING `KeyboardInterrupt` teardown path in `run_queue` in both drivers. When Phase 0 lands, its
    `clean_shutdown` should CALL this one function rather than duplicating the decision.

    MANDATORY OWNERSHIP GUARD (F13):

    ```text
    $ grep -n "signal.signal(" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py
    exit=1 (1 = NO match)
    ```

    No handler was registered, so `runstop` Phase 5 (`71vjbn`) keeps the handler slot uncontested.

    DIRECT CALL, twice, IDEMPOTENT, in BOTH drivers:

    ```text
    === V-05 for oc_runipd: DIRECT CALL, twice (idempotent) ===
      call 1 actions: {'aw/lane/aaaaaa': 'reclaimed', 'aw/lane/bbbbbb': 'preserved'}
      call 2 actions: {'aw/lane/aaaaaa': None, 'aw/lane/bbbbbb': 'preserved'}
      HOLDS-WORK lane byte-identical: tip be38220c93==be38220c93 True | porcelain ''=='' True
      its BRANCH STILL EXISTS: '+ aw/lane/bbbbbb'
      EMPTY lane gone: True | branch gone: True
      nothing stashed: '' | main porcelain: '?? .aw/'
    === V-05 for agy_runipd: DIRECT CALL, twice (idempotent) ===
      call 1 actions: {'aw/lane/aaaaaa': 'reclaimed', 'aw/lane/bbbbbb': 'preserved'}
      call 2 actions: {'aw/lane/aaaaaa': None, 'aw/lane/bbbbbb': 'preserved'}
      HOLDS-WORK lane byte-identical: tip be38220c93==be38220c93 True | porcelain ''=='' True
      its BRANCH STILL EXISTS: '+ aw/lane/bbbbbb'
      EMPTY lane gone: True | branch gone: True
      nothing stashed: '' | main porcelain: '?? .aw/'
    ```

    Both drivers agree exactly. `git stash list` is empty and main's porcelain shows only the
    gitignored `.aw/` dir, so nothing was stashed, reset, or moved (REFUSE-AND-REPORT, matching
    `runstop` Phase 0's independently reached conclusion).

    THE SIGINT PATH, through a REAL `os.kill(os.getpid(), signal.SIGINT)` reaching the driver's own
    `KeyboardInterrupt` handling (full transcript under V-07's end-to-end section): the run exited 130,
    two work-holding lanes were preserved and reported, and the one provably-empty lane was reclaimed.

    SIGTERM: covered by DIRECT INVOCATION of the same callable, per E-05. No SIGTERM handler is
    installed here because `71vjbn` owns it (spec `c4gd2h` R13); once that lands its handler calls this
    same function, so the SIGTERM path exercises identical code.

    CORRECTED `teardown_worktree` COMMENT (the old text called the branch deletion "best-effort" and
    "not a correctness hazard", which F5 disproves):

    ```text
    DATA-SAFETY WARNING, and it is not theoretical: this deletes the per-lane BRANCH as well as the
    worktree, and `--force` also destroys UNCOMMITTED files in the lane. MEASURED: after tearing down
    a lane holding one commit, the branch is gone, `git reflog show <branch>` is EMPTY, and the commit
    survives only as an UNREFERENCED object, i.e. garbage-collectable with no ref and no reflog to
    recover it from; and uncommitted lane files are gone from git AND from disk with nothing to
    recover. So the branch deletion is a DATA-SAFETY HAZARD for any lane that holds work, NOT the
    "best-effort, not a correctness hazard" cleanup an earlier comment here claimed.
    ```

    A lane owned by ANOTHER live process is never torn down: `lane_owned_by_other_live_process` gates
    it, and `TestReclamationPreservesWorkAndReclaimsOnlyEmpty::test_a_live_owners_lane_is_never_torn_down`
    asserts it. That predicate deliberately answers "does a DIFFERENT live process own this" rather than
    "is the owner alive", because a driver reclaiming its own lanes at shutdown IS the live owner of
    every one of them; a bare liveness test made reclamation a no-op and leaked every lane, which the
    test suite caught during execution.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the interrupt report for a run with one empty and one work-holding lane, showing the operator can tell them apart without running git. Confirm no em or en dash. Confirm by grep that no new CLI verb or flag was added and that the reported facts come from the E-01 classifier rather than a second git probe.
  - Observed evidence: The interrupt report, for a run with one empty and two work-holding lanes, printed by
    `print_lane_interrupt_report` (real SIGINT run, full transcript in V-07):

    ```text
    --- Lane reclamation ---
    PRESERVED (holds work; inspect these, nothing was deleted):
      bbbbbb bbbbbb: HOLDS WORK (1 commit(s) beyond base)
          branch aw/lane/bbbbbb
          worktree /tmp/.../e2e/repo/.aw/worktrees/bbbbbb
      cccccc cccccc: HOLDS WORK (uncommitted changes)
          branch aw/lane/cccccc
          worktree /tmp/.../e2e/repo/.aw/worktrees/cccccc
          uncommitted edits committed as an interrupted snapshot 782746a958d5
    Reclaimed (provably empty, nothing to recover):
      aaaaaa aw/lane/aaaaaa
    ```

    The operator can tell at a glance which lane matters without running any git command: the branch,
    the worktree path, whether it is ahead of base and by how many commits, whether the tree is dirty,
    and the snapshot commit are all in the text. This is what the incident lacked, where five lanes had
    to be inspected by hand to find the one holding roughly 1180 lines of real work.

    NO em or en dash appears (asserted in
    `TestInterruptReportIsActionable::test_report_distinguishes_empty_from_work_holding`, which checks
    U+2014 and U+2013 explicitly).

    NO new CLI verb or flag was added: `aw doctor --lanes` and `aw recover <run-id>` remain owned by
    plan `2c122z`, asserted by `test_no_new_cli_verb_or_flag_was_added`, which greps `cli.py` for
    `--lanes` and `"recover"`. The reported facts come from the E-01 classifier and not a second git
    probe, asserted field-by-field in `test_report_facts_come_from_the_classifier` (state, dirty,
    commits_ahead, holds_work all compared against `inspect_lane`'s own reading).

    If plan `2c122z` wants a shared helper for its discovery verbs, `describe_lane` and
    `format_lane_report` in the drivers are the consumable pair, both built on `inspect_lane`.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: state which liveness mechanism was chosen (`git worktree lock` or a durable owner record) and why. Then paste a TWO-PROCESS demonstration on a fixture repo: process A allocates lane `X` and stays alive; process B allocates lane `X` and must NOT adopt A's worktree. Paste `git worktree list --porcelain` and `git branch --list 'aw/lane/*'` showing TWO distinct paths and TWO distinct branches, and paste A's worktree porcelain before and after B's allocation showing it unchanged. Then paste the COMPLEMENT, which proves the check did not simply disable adoption: with the owner process GONE, the same lane IS adopted and no second worktree appears. Finally show the liveness signal is durable across process exit (read it from a fresh process) and that the ambiguous/unreadable case falls through to attempt-scoping rather than adopting.
  - Observed evidence: MECHANISM CHOSEN: a durable OWNER RECORD (`.aw/worktrees/.owners/<lane>.json`, inside the
    gitignored worktrees root so it is never committed, but OUTSIDE any lane directory so it survives a
    `git worktree remove` and is readable for a branch-only leftover), carrying host, pid, and a
    boot-scoped `start_token` from `/proc/<pid>/stat` that detects pid REUSE.

    WHY NOT `git worktree lock`, though it was verified available at git 2.43.0: it is keyed on the
    WORKTREE, so it says nothing about a branch-only leftover (the likelier residue per F2), and a lock
    left behind by a KILLED process is indistinguishable from a live one, which would make the ACTUAL
    target case (a dead owner) permanently unadoptable and so defeat the fix.

    TWO REAL PROCESSES. Process A allocates lane `X` and stays alive; process B allocates lane `X`:

    ```text
    process A (pid 995323) allocated: aw/lane/X at X (created)
    A is ALIVE: True
    process B allocated: aw/lane/X_attempt2 disposition=attempt-scoped
       detail: declined to adopt: owner pid 995323 on <host> is LIVE
    TWO DISTINCT paths:  True | X vs X_attempt2
    TWO DISTINCT branches: True
    git worktree list --porcelain:
    worktree /tmp/.../live
    HEAD bce7b15a239c3283206120ef3d8dcb730badf46d
    branch refs/heads/main

    worktree /tmp/.../live/.aw/worktrees/X
    HEAD bce7b15a239c3283206120ef3d8dcb730badf46d
    branch refs/heads/aw/lane/X

    worktree /tmp/.../live/.aw/worktrees/X_attempt2
    HEAD bce7b15a239c3283206120ef3d8dcb730badf46d
    branch refs/heads/aw/lane/X_attempt2
    git branch --list 'aw/lane/*': + aw/lane/X + aw/lane/X_attempt2
    A's worktree UNCHANGED: tip bce7b15a23==bce7b15a23 True ; porcelain ''=='' True
    liveness signal readable from a FRESH process while A lives: {"pid": 995323, "host": "<host>", "branch": "aw/lane/X"}
    ```

    THE COMPLEMENT, proving adoption was not simply disabled. With A's process GONE, the SAME lane IS
    adopted and no second worktree appears:

    ```text
    process A exited rc=0; owner record SURVIVES process exit: {"pid": 995323, "host": "<host>"}
    lane_is_safe_to_adopt now: True | owner pid 995323 is gone
    process C allocated: aw/lane/X disposition=adopted
       detail: adopted empty lane at the requested base (owner pid 995323 is gone)
    NO second worktree appeared: True (count 3 -> 3)
    ```

    AMBIGUOUS cases fall through to attempt-scoping rather than adopting, both of them:

    ```text
    owner record host forced to: some-other-machine.invalid
    lane_is_safe_to_adopt: (False, "owner liveness undeterminable ({'host': 'some-other-machine.invalid', 'pid': 995951}); failing safe")
    allocate disposition=attempt-scoped branch=aw/lane/Y_attempt2 (attempt-scoped, NOT adopted)
    corrupt record -> read_lane_owner: None -> safe_to_adopt: (False, 'owner record present but unreadable; failing safe')
    ```

    The unreadable-record case was a fail-OPEN hole found and closed during execution: a corrupt record
    initially read as "unclaimed" and therefore adoptable, so `lane_is_safe_to_adopt` now distinguishes
    NO record (adoptable) from an UNREADABLE one (fail safe).

    Asserted in `TestLiveOwnerGuardWithTwoRealProcesses` (marked `slow`, since it spawns real
    processes): `test_j_live_owner_not_adopted_and_dead_owner_is` covers the guard AND its complement in
    one test, so the guard cannot be satisfied by disabling adoption;
    `test_j_ambiguous_owner_record_falls_through_to_attempt_scoping` and
    `test_j_unreadable_owner_record_fails_safe` cover the fail-safe paths.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste all seven cases passing. Paste the FALSIFIABILITY output for (a), (b), (e), (f) against pre-fix code as actual failures, not claims. For (e) specifically, paste the assertion text showing it checks REFERENCE reachability and not object existence, and show it FAILING when teardown is replaced with a blanket force teardown, since that is the F5 behavior it exists to catch. Paste (g) failing when only one driver is changed. Finally paste `git worktree list` and `git branch --list 'aw/lane/*'` showing only pre-existing lanes remain.
  - Observed evidence: `tests/test_lane_allocation_idempotent.py` passes in full at HEAD `d4d265b67a12e89893ff77b7ff093b0abd5a45f9` (35 tests; the
    ten E-07 cases plus the classifier, disposition, reporting, prompt, and symmetry guards):

    ```text
    $ git rev-parse HEAD
    d4d265b67a12e89893ff77b7ff093b0abd5a45f9
    $ python3 -m pytest tests/test_lane_allocation_idempotent.py -m '' -q
    ...................................                                      [100%]
    35 passed in 3.08s
    ```

    FALSIFIABILITY. All measured against a `git archive HEAD` tree of unmodified HEAD `d4d265b67a12e89893ff77b7ff093b0abd5a45f9` with
    zero of this plan's package changes (`grep -c laneorphan agent_workflows/worktree_lease.py` = 0)
    and only the test file copied in. 29 of the 33 then-present tests failed. The mandated cases, with
    ACTUAL output:

    ```text
    (a) >       second = WL.allocate_worktree(repo, "abc123")
        E           agent_workflows.worktree_lease.WorktreeError: git worktree add failed for lane 'abc123': Preparing worktree (new branch 'aw/lane/abc123')
        E           fatal: a branch named 'aw/lane/abc123' already exists
    (b) >       again = WL.allocate_worktree(repo, "lonely")
        E           agent_workflows.worktree_lease.WorktreeError: git worktree add failed for lane 'lonely': Preparing worktree (new branch 'aw/lane/lonely')
        E           fatal: a branch named 'aw/lane/lonely' already exists
    FAILED ...::TestAllocationIsIdempotent::test_a_second_allocation_for_same_lane_id_does_not_raise
    FAILED ...::TestAllocationIsIdempotent::test_b_branch_only_leftover_also_allocates
    FAILED ...::TestReclamationPreservesWorkAndReclaimsOnlyEmpty::test_e_interrupt_leaves_work_holding_lane_reachable_by_reference
    FAILED ...::TestReclamationPreservesWorkAndReclaimsOnlyEmpty::test_f_next_run_of_the_same_set_allocates_after_an_interrupt
    FAILED ...::TestAllocationIsIdempotent::test_h_stale_base_lane_is_attempt_scoped_not_adopted
    FAILED ...::TestAllocationFailurePathIsNonDestructive::test_i_failed_add_never_deletes_a_pre_existing_work_holding_branch
    FAILED ...::TestLiveOwnerGuardWithTwoRealProcesses::test_j_live_owner_not_adopted_and_dead_owner_is
    FAILED ...::TestDriverSymmetry::test_g_both_drivers_expose_the_same_lane_reclamation_surface
    ```

    Cases (a) and (b) fail on the real reported BEHAVIOR, not on a missing attribute: each performs the
    second allocation BEFORE touching any new field.

    CASE (e) IS THE F5 GUARD, and it must fail against a blanket force teardown. MUTATION TEST: the
    classify-then-preserve decision in `reclaim_lanes_on_interrupt` was replaced with the F5 behavior
    (`if False:` on the holds-work branch plus removal of the `reclaimable` gate), and (e) fails:

    ```text
    >               self.assertEqual(out(repo, "rev-parse", held.branch), tip)
    E               AssertionError: 'aw/lane/bbbbbb' != 'c312b4bc474987266f3c66feafff390d8b53ac54'
    FAILED ...::test_e_interrupt_leaves_work_holding_lane_reachable_by_reference
    ```

    The assertion text checks REFERENCE reachability, not object existence:
    `self.assertIn("refs/heads/" + held.branch, refs_pointing_at(repo, tip), "the work-holding lane's
    tip MUST still be reachable by a ref")`, where `refs_pointing_at` runs
    `git for-each-ref --points-at <sha>`. Why that standard is mandatory, measured against the mutant:

    ```text
    AGAINST THE MUTANT (blanket force teardown, i.e. the F5 behavior):
      object still exists (cat-file -e): True  <- an object-existence assertion would PASS here
      refs pointing at it: ''  <- the REFERENCE assertion FAILS, which is the point
      reflog: ''
    ```

    CASE (g) fails when only ONE driver is changed. MUTATION TEST: `agy_runipd.py` reverted to pre-fix
    while `oc_runipd.py` keeps the fix:

    ```text
    MUTATION: agy_runipd.py reverted to PRE-FIX (only oc_runipd changed)
    FAILED ...::TestDriverSymmetry::test_g_both_drivers_expose_the_same_lane_reclamation_surface
    FAILED ...::TestDriverSymmetry::test_g_both_drivers_reclaim_on_the_existing_interrupt_path
    FAILED ...::TestDriverSymmetry::test_g_both_drivers_record_lane_identity_at_allocation
    ```

    END-TO-END, the property the backlog item actually asks for. A run allocates three lanes (one
    empty, one with a commit, one dirty), takes a REAL SIGINT, then the SAME Set runs again:

    ```text
    === BEFORE (run 1 not started) ===
    git worktree list:
    /tmp/.../e2e/repo  32b33be [main]
    git branch --list 'aw/lane/*': ''

    === RUN 1: allocate, work, then REAL SIGINT ===
    LANES ALLOCATED; sending myself a REAL SIGINT now
    INTERRUPT HANDLED

    --- Lane reclamation ---
    PRESERVED (holds work; inspect these, nothing was deleted):
      bbbbbb bbbbbb: HOLDS WORK (1 commit(s) beyond base)
          branch aw/lane/bbbbbb
          worktree /tmp/.../e2e/repo/.aw/worktrees/bbbbbb
      cccccc cccccc: HOLDS WORK (uncommitted changes)
          branch aw/lane/cccccc
          worktree /tmp/.../e2e/repo/.aw/worktrees/cccccc
          uncommitted edits committed as an interrupted snapshot 782746a958d5
    Reclaimed (provably empty, nothing to recover):
      aaaaaa aw/lane/aaaaaa

    run 1 exit code: 130 (130 == interrupted)
    === AFTER RUN 1's interrupt ===
    git worktree list:
    /tmp/.../e2e/repo                       32b33be [main]
    /tmp/.../e2e/repo/.aw/worktrees/bbbbbb  c7a4791 [aw/lane/bbbbbb]
    /tmp/.../e2e/repo/.aw/worktrees/cccccc  782746a [aw/lane/cccccc]
    git branch --list 'aw/lane/*':
    + aw/lane/bbbbbb
    + aw/lane/cccccc
    git stash list: '' <- nothing stashed
    MAIN status --porcelain: '?? .aw/' <- main untouched
      aw/lane/bbbbbb: tip c7a4791648, refs pointing at it: 'refs/heads/aw/lane/bbbbbb'
      aw/lane/cccccc: tip 782746a958, refs pointing at it: 'refs/heads/aw/lane/cccccc'

    === RUN 2: THE SAME SET AGAIN (the property the item asks for) ===
      allocate aaaaaa: OK  disposition=created         branch=aw/lane/aaaaaa
      allocate bbbbbb: OK  disposition=attempt-scoped  branch=aw/lane/bbbbbb_attempt2
      allocate cccccc: OK  disposition=attempt-scoped  branch=aw/lane/cccccc_attempt2
    NO 'already exists' failure; run 2 proceeds.
    run 1's real work still reachable: refs/heads/aw/lane/bbbbbb
    ```

    THE SAME run-2 sequence against PRE-FIX code, for contrast:

    ```text
    PRE-FIX code (unmodified HEAD d4d265b6):
      run 1 allocated aw/lane/bbbbbb and did real work; then it is interrupted (NO cleanup exists)
      run 2, SAME Set:
        allocate bbbbbb: DIED -> fatal: a branch named 'aw/lane/bbbbbb' already exists
        => the Set stays WEDGED until a human removes the debris by hand.
    ```

    THIS REPOSITORY'S LIVE LANES WERE NOT TOUCHED. Every probe and test built its own fixture repo
    under `/tmp`; no lane was created or removed in this checkout. 25 live lanes are present and intact
    (`aw/lane/15zvu6 1o4eif 1qxuke 2c122z 2ouj70 58ha43 7nkcgp 7p9n2v 8guhs0 8h9lap af7i6p foi1b3
    gq6m2u i79rgh j4v6ga jxqdcw lbgzxg plqjt7 qcqhj7 rchpms rygds7 uyd3lw w0ln4q z2isfg zwnjp3`), and
    only my own four files are modified (`git status --porcelain`).

    SUITE BASELINE, both readings taken at HEAD `d4d265b67a12e89893ff77b7ff093b0abd5a45f9` with the same runner:

    ```text
    MY TREE   (fast, make test):   15 failed, 2942 passed, 3 skipped, 4 xfailed
    MY TREE   (full, make test-all): 19 failed, 3274 passed, 3 skipped, 4 xfailed
    ```

    Every one of those failures is PRE-EXISTING at unmodified HEAD, proven by a per-test set
    comparison rather than a count: the failing test IDs in my tree are byte-identical to the failing
    test IDs at unmodified HEAD (`diff` of the two sorted `FAILED` lists is empty). They live in
    `tests/test_run_viewer.py` (15) plus `tests/test_cli.py`, `tests/test_command_surface_declarations.py`,
    and `tests/test_cli_conformance_matrix.py` (4 more, slow-only), none of which this plan touches.
    ZERO new failures.

    The subprocess tests are marked `slow` per repo convention (`pyproject.toml:131` sets
    `addopts = "-q -n auto --dist=worksteal -m 'not slow'"`), so a bare `pytest` deselects them and
    `make test-all` runs them. `tests/test_ipd_set_executor.py:292`
    (`test_real_worktree_create_and_teardown`) still passes unweakened. No `-n auto` and no second `-q`
    were added.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 8 E-leaves across 3 task groups, under the thresholds. Right-sizing checked per leaf: E-01 the classifier, E-02 the allocation policy, E-08 the liveness guard on adoption, E-03 the caller-visible disposition, E-04 durable registration, E-05 the reclamation decision, E-06 the report, E-07 the tests. Each has its own falsifiable surface. E-08 was added at review rather than folded into E-02 deliberately: it is a distinct concern (cross-process ownership, not debris classification), it has its own test surface requiring two real processes, and bundling it would have made E-02 both the allocation policy and a concurrency protocol.

Open questions: ALL RESOLVED from measurement and from sibling-plan ownership boundaries. The maintainer should be aware of THREE judgment calls rather than hidden assumptions. First, OQ-02 declines research `x03wgn`'s fuller run-id-keyed lane naming in favor of a suffix, because adopting the full scheme would change lane identity while `2c122z` is mid-flight in a live run; if you want the full scheme, this plan should be re-scoped or the change assigned to `2c122z`. NOTE the tension surfaced at review: finding F12 shows the absence of run scoping is precisely what lets two concurrent runs collide on one lane name, so E-08 adds a liveness GUARD rather than the naming fix. That is the correct minimal move for a release blocker, but it means the underlying identity weakness remains and is worth assigning deliberately. Second, OQ-03's answer was CORRECTED at review: this plan must NOT install a signal handler, because `runstop` Phase 5 (`71vjbn`) is already approved to own SIGINT/SIGTERM in these same two files (F13); E-05 now exposes a callable that Phase 5 and Phase 0 both invoke. If you would rather this land strictly after Phase 0, that is a scheduling decision only you can make, and the cost of waiting is that runs stay wedgeable meanwhile. Third, E-08's liveness mechanism is left to the executor between `git worktree lock` and a durable owner record (both verified workable); if you have a preference, state it, since it becomes the ownership convention other lane tooling will read.

Scope fence: touch ONLY `agent_workflows/worktree_lease.py`, `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, and the new test module. Do NOT add `aw doctor --lanes` or `aw recover` (owned by `2c122z`), do NOT implement any stop LEVEL or the stop-request flag (owned by the `runstop` Set), do NOT change `ipd_lifecycle.py` (owned by `z2isfg` and `lbgzxg`), and do NOT introduce run-id-keyed lane naming (OQ-02). If it seems to need more, STOP and report.

CRITICAL SAFETY RULE FOR THE EXECUTOR, not optional: this repo had SIX LIVE LANES owned by TWO RUNNING drivers at review time (`1o4eif`, `2c122z`, `58ha43`, `7p9n2v`, `qcqhj7`, `rchpms`), and the set churns, so take your own reading rather than trusting this list. Never remove, reset, or check out another party's lane worktree or branch, and never run a repo-wide `git worktree prune` or a wildcard branch delete. Create your own fixture repos for every test. If you create a lane while probing, remember that a failed `git worktree add` still creates the branch, so clean up branches as well as worktrees, and only the ones YOU made.

EXTRA HAZARD FOR THIS PLAN SPECIFICALLY: you are editing the very allocation code the live drivers are CALLING. A half-applied change to `allocate_worktree` can break a running lane allocation, and one of the live runs was executing this Set at review time. Keep each edit to `worktree_lease.py` complete and syntactically valid in a single write, do not leave the module importable-but-broken between edits, and never test the new adoption or reclamation paths against this repo's real `.aw/worktrees/`.

Honesty rule (HARD MUST): when you report tests or validation passed, paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Never claim a pass you did not run, and never reuse this plan's recorded baseline as if freshly measured.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, and never push. Before every commit run `git diff --cached --name-only` and unstage anything not modified by this plan. This is a SHARED CHECKOUT and both driver modules are under active concurrent edit by other sessions, so re-read them immediately before editing and locate code by SYMBOL. Line numbers are deliberately omitted from this plan for that reason.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand. Do not create or push a git tag or release.
