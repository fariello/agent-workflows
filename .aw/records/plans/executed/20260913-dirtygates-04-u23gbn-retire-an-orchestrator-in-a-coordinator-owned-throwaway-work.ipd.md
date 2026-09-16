# IPD: Retire an orchestrator in a coordinator-owned throwaway worktree so the rollup lands as one ref update

- Date: 2026-09-13
- Kind: child
- Concern: Orchestrator retirement performs three mutations in the SHARED checkout (edit the plan's status, move it to `executed/`, commit) behind a journal. Between the move and the commit there is a real window in which main is dirty, and a slow or contended commit widens it. MEASURED AT REVIEW rather than asserted: mid-retirement the shared tree really does read `RM ...pending/... -> ...executed/...` at the post-move instant and `R  ...` plus two untracked index files at the pre-commit instant (F-1a). Separately, a fault-injected retirement rolled the plan back correctly but still left two untracked index files behind, so a failed retirement does not restore the tree it started from.
- Scope: Shrink that window by performing the retirement's mutations AND its commit in a COORDINATOR-OWNED throwaway worktree, and letting a REFUSING fast-forward in the shared checkout be the single step that advances the branch; plus the two consequential fixes the relocation forces, namely moving the plans-index refresh after the reconciliation so its fail-loud gate keeps guarding (E-07, F-12) and guarding the rollback's write to the plan's original path so a failed retirement cannot destroy a peer's in-flight edit (E-08, F-14). NOT a compare-and-swap ref advance: F-10 and F-11 measured that a CAS before the reconciliation makes the reconciliation a no-op that reports success. THE WINDOW SHRINKS, IT DOES NOT VANISH, and the plan says so because review measured that a ref update alone cannot deliver the stronger claim (F-7). Excludes the pre-launch gate (Order 01), the integration gate (Order 02), and the backlog close (Order 03). Excludes any change to the eligibility rule or to the worker-role refusal. THE INDEX-RESIDUE FIX WAS CARVED OUT to Order 06 (`4xt6u4`) at revision: `/plan-review` established it is not gated by this plan's blocking OQ-03 and needs no architecture ruling, so it ships independently.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/commit_lock.py, tests/test_orchestrator_retirement.py, tests/test_ipd_lifecycle_cli.py, tests/test_isolated_commit.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: dirtygates
- Order: 4
- Highest E allocated: 08
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: u23gbn
- Priority: medium
- Work-Kind: bug

## Workflow history
- 2026-09-16 executed (aw oc run): aw oc run self-finalize: u23gbn verified (set dirtygates, attempt 1).
- 2026-09-14 approved (aw set): status set to approved
- 2026-09-13 reviewed (maintainer, --by-human attestation via askme): MAINTAINER ATTESTATION 2026-09-13: readiness set to `go-pending-approval` BY THE MAINTAINER, not by an agent and not by a review. The prior `no-go` was written by this plan's own earlier review round while a blocking question was open; the maintainer then answered every open question in this plan through the `askme` workflow on 2026-09-13, one interactive prompt at a time, and each answer is recorded in this plan's `## Open questions` with its reasoning. Asked directly how the stale verdict should be cleared, the maintainer chose to attest it themselves rather than fund a further review round, having read every resolution as it was written. THE ALTERNATIVE WAS PRICED AND REJECTED ON EVIDENCE: the round that ran earlier the same day cost 3h 02m and $106.07 across nine items, cleared three plans, and raised four NEW blocking questions on the rest, so a further round was not expected to yield a clean sheet. NO AGENT WROTE THIS VALUE ON ITS OWN AUTHORITY. Recorded here because the auto-approve predicate reads this field FIRST (`plan_readiness.is_plan_review_approved`), so a stale `no-go` is a live refusal that would have silently skipped this plan when the Set executed.
- 2026-09-13 reviewed (opencode (its_direct/pt3-claude-opus-5-1m-us)): /plan-review ROUND 3: REVIEWED - OPEN QUESTIONS; readiness NO-GO. PR-021..PR-025; PR-021 OPEN and escalated as blocking OQ-04, the rest FIXED. Round 2's fixes held, but three defects the relocation CREATES were measured and were owned by nobody: F-11 commit_isolated cannot be reused (its copy direction is shared->worktree, measured error), F-12 the plans-index fail-loud gate INVERTS into a false pass leaving check.stale-index-stale unreported, F-14 the rollback destroys a peer's in-flight edit to the plan file (measured, bytes lost). New E-07, E-08 and V-07, V-08 close the last two; OQ-04 escalates the first because fixing commit_isolated touches the helper behind every aw self-commit.
- 2026-09-13 to-review (aw set): status set to to-review

- 2026-09-13 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review ROUND 1: REVIEWED - OPEN QUESTIONS; readiness NO-GO. PR-401..PR-408; PR-401 OPEN and escalated as blocking OQ-03, the rest FIXED. `aw ipd lint` CONFORMING at `--phase author` before semantic review. DISCLOSURE: same model family as the author, so the value rests on what was DRIVEN, not re-read; every claim below was measured at HEAD `b16e1108`. THE PLAN'S DIAGNOSIS IS CORRECT AND REVIEW CONFIRMED IT INDEPENDENTLY: instrumenting a real successful retirement (patching `_refresh_plans_index_fail_loud` and `commit_isolated`) showed the shared tree reading `RM pending/... -> executed/...` at the post-move instant and `R  ...` plus two untracked index files at the pre-commit instant, so the window the maintainer challenged is real (new F-1a). F-3's residue also reproduced exactly as stated. THE FINDING THAT STOPS THE PLAN IS A BLAST RADIUS IT NEVER DECLARES (PR-401, new F-8): `_finalize_transaction` is SHARED CODE with exactly two callers, `finalize` (`:2544`) and `retire_orchestrator` (`:2405`), so relocating the mutations inside it changes the terminal transition for EVERY ordinary plan, not only an orchestrator rollup, while confining the change instead FORKS a second transaction body -- and spec `77tr3o` OQ-1's ACCEPTED COST is precisely that "two transition paths CAN DRIFT". Which of those two the maintainer wants is an architecture and risk call on the most load-bearing write in the toolkit, so it is escalated rather than chosen here. THE CENTRAL MECHANISM ALSO DOES NOT DELIVER ITS STATED ACCEPTANCE (PR-402, new F-7): built by hand in a scratch repo, a worktree commit landed by BARE CAS leaves the shared checkout reading `R  p/executed/plan.md -> p/pending/plan.md`, dirty in the INVERSE direction, because HEAD now says `executed/` while the working tree still holds `pending/`; adding `commit_isolated`'s own trailing `git reset` makes it ` D p/executed/plan.md` plus `?? p/pending/`. So "no write to the shared checkout" is unobtainable and V-01's demanded proof could not have been produced; E-01's outcome is rewritten to the honest claim, new E-06 adds the ff-only reconciliation (measured to REFUSE, rc=1, with the peer's bytes preserved, when a local change would be overwritten), and V-06 pins the refusal. OQ-02's PREFERRED ROUTE WAS MEASURED TO BREAK THE SUCCESS PATH (PR-403, new F-9): a fresh detached worktree does NOT receive the gitignored `INDEX.json`/`INDEX.md`, and after the worktree is removed the shared copies still hold their STALE bytes, which flips `aw index plans --check` to `check.stale-index-stale` -- registered `warning`, which FAILS the gate (`check_engine.py:336`) -- and de-facto removes `plans-index-refresh-fail-loud` from the shared tree while the drift test that guards it (`tests/test_orchestrator_retirement.py:2079`, `:2104`) keys only on the STRING and would still pass. OQ-02 is therefore resolved AGAINST the author's preference. V-03 WAS SATISFIABLE WITHOUT ANY FIX (PR-404): both index files are gitignored HERE, so a repo-level `git status` is empty before and after regardless, and the residue is visible only in the fixture; V-03 now demands the fixture-level observation. E-05'S PRESCRIBED TECHNIQUE CANNOT WORK (PR-405): fault injection RAISES `_InjectedFault` and aborts (`:2593-2595`), so it cannot observe a SUCCESSFUL retirement at those instants; E-05 now requires a real observation seam, naming the one review actually used. Also fixed: `runner_shared.py` was declared in `Scope-Paths` with no E-item touching it (PR-406, over-scope, removed); the spec-sync section cited R-4/R-5/R-6 but the GOVERNING text is OQ-1's accepted cost (PR-407); and F-6's "cheap and frequent, so the window is hit often" is overstated -- measured 4 retirements in the whole corpus against 41 executed orchestrators (PR-408, F-6 corrected). Verified sound and left alone: the worker-role analysis (F-5) and the insistence that the role stay `coordinator`, the journal-is-recovery-not-atomicity distinction (F-2), F-3a's own honest severity qualifier, and the refusal to touch the eligibility or `Kind` gates. One `Reversible: no` decision (D-1) taken and escalated as OQ-03 per the workflow's own rule.
- 2026-09-13 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): authored after the maintainer challenged the claim that retirement is atomic. The challenge was correct: it is three operations, and a fault-injection run proved the rollback leaves untracked residue (F-3).
- 2026-09-13 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.

## Goal

Shrink the window in which an orchestrator's retirement leaves the shared checkout dirty, by doing the work in a coordinator-owned throwaway worktree and landing it as one ref update plus a refusing fast-forward. Keep the coordinator role, the eligibility gate, and the worker-role refusal exactly as they are.

THE GOAL NOW CARRIES TWO OBLIGATIONS IT DID NOT HAVE, ADDED AT REVIEW ROUND 3, because review measured that the relocation CREATES two defects rather than merely relocating work. Moving the mutations off the shared checkout (a) makes the fail-loud plans-index gate scan a disk that no longer reflects the transition, inverting the gate from a guard into a false pass (F-12, E-07), and (b) turns the rollback's restore of the plan's original path from a correct undo into an unconditional overwrite of whatever a peer has there (F-14, E-08). So the honest goal is: shrink the window AND leave the index gate genuinely live AND leave a failed retirement incapable of destroying a co-worker's bytes. A change that delivers only the first is not a partial win; it trades a reported dirty window for an unreported one plus a data-loss path.

WHAT THIS GOAL DELIBERATELY NO LONGER CLAIMS, corrected at review. The original goal said "one ref update that either happened or did not", i.e. that the shared checkout is never written at all. That is UNOBTAINABLE and was measured so (F-7): a ref update alone leaves the shared working tree holding the plan at its OLD path while HEAD says the new one, which is dirty in the inverse direction and is worse than today, because it reads as an unexplained reverse rename rather than an in-progress move. The shared tree must therefore still be brought into line with the new HEAD, and the honest goal is that the write be (a) a fast-forward git itself performs, (b) one that REFUSES rather than clobbers when a peer's change is in the way, and (c) as short as possible. That is strictly better than today's three-mutation window; it is not atomicity, and this plan must not be validated as if it were.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: do the mutations off the shared checkout

- [x] E-01 Perform the retirement's mutation sequence (the status edit and the plan move) in a throwaway worktree created and owned by the COORDINATOR, so the shared checkout is not the place those mutations happen. The existing pattern to reuse is `commit_lock.commit_isolated` (`commit_lock.py:210-292`), which snapshots HEAD into a detached worktree, mirrors the paths, runs the real hooks there, and advances the branch under a compare-and-swap; it exists precisely because committing in the shared tree lets `pre-commit` stash and then restore over a peer's write. THE ROLE MUST REMAIN `coordinator`: retirement's first gate refuses when `AW_EXECUTION_ROLE=worker` (`ipd_lifecycle.py:2237-2246`), and this worktree is a coordinator-owned scratch tree, NOT a worker lane. Do not set, inherit, or emulate the worker role in it.
  - THE OUTCOME BELOW WAS WEAKENED AT REVIEW BECAUSE THE ORIGINAL WAS UNOBTAINABLE, and an executor must know that before starting. It read "a retirement performs no edit, move, or commit in the shared checkout; main advances by one ref update", and F-7 measures why that cannot hold: after a worktree commit and a bare CAS, the shared checkout reads `R  p/executed/plan.md -> p/pending/plan.md` -- dirty in the INVERSE direction, because HEAD holds the plan under `executed/` while the working tree still holds it under `pending/`. Adding `commit_isolated`'s own trailing `git reset --quiet HEAD -- <rel>` (`commit_lock.py:281-284`) does not clean it either; it produces ` D p/executed/plan.md` plus `?? p/pending/`. So the shared tree MUST still be reconciled, which is E-06's job, and E-01's honest deliverable is that the mutation and the commit stop happening there, not that nothing happens there.
  - OQ-03 IS ANSWERED: option (a), CHANGE THE SHARED `_finalize_transaction` IN PLACE; do NOT fork a rollup-specific body. CORRECTED AT REVIEW ROUND 2 (PR-014): this bullet previously said "DO NOT IMPLEMENT THIS UNTIL OQ-03 IS ANSWERED", which would stall an executor on a resolved question. Know the consequence the answer carries: the change reaches EVERY plan's terminal transition, not only a rollup retirement, so `tests/test_ipd_lifecycle_cli.py` is a required part of validation and no `77tr3o` amendment is expected (that was the "fork" branch, which was not taken).
  - `commit_isolated` CANNOT BE REUSED AT ALL HERE, AND THE REASON IS ITS COPY DIRECTION, NOT ONLY ITS CAS. FOUND AND MEASURED AT REVIEW ROUND 3 (PR-021, F-11), and this supersedes the earlier "resolve the tension" instruction, which understated the problem. `commit_isolated` creates its OWN worktree and mirrors each named path FROM the shared tree INTO it (`shutil.copy2(src, dst)`, `commit_lock.py:226-231`), propagating a DELETION when the shared-tree source is absent (`dst.unlink()`, `:232-234`). The direction is shared -> worktree. So a mutation performed in a DIFFERENT, coordinator-owned worktree is invisible to it, and the paths it is asked to commit do not exist in the shared tree at all. MEASURED against the real function: mutate in a coordinator worktree, then call `commit_isolated(repo, ["p/pending/plan.md","p/executed/plan.md"])`; it returned `error` / "git add failed in isolated worktree: fatal: pathspec 'p/executed/plan.md' did not match any files", HEAD unmoved and nothing committed. Two worktrees cannot be reconciled by a helper whose whole contract is "copy the shared tree's version of these paths".
  - SO COMMIT IN THE COORDINATOR'S OWN WORKTREE DIRECTLY, and do not advance the ref there. MEASURED END TO END at review round 3, and this is the shape to implement: create the coordinator worktree detached at the pre-transition HEAD; perform the status edit and the relocation THERE; stage with `git add -- <only paths that exist>` (the SAME existence filter `_finalize_transaction` already applies at `:2720`, because `git mv` in the worktree leaves the old path absent and `git add` on it exits 128 -- measured); `git commit` THERE so the real hooks run in a private tree exactly as `commit_isolated` intends; then let E-06's `git merge --ff-only <landed>` in the shared checkout be the single step that advances the branch. Result measured: worktree staged `R100 p/pending/plan.md -> p/executed/plan.md`, ref still at base before the merge, merge rc=0 "Fast-forward", shared tree ends with the plan at `executed/` carrying the EDITED bytes, `git status --porcelain` reading exactly ` M peer.txt`, and the commit's `--name-status` containing only the rename.
  - DO NOT DUPLICATE `commit_isolated`'S BODY. Its CAS arm, its `ISO_RACED` honesty and its cleanup `finally` are the parts worth keeping; what must change is that the branch advance becomes the CALLER's step. Prefer teaching `commit_isolated` (or a sibling in the same module) to return the landed sha WITHOUT advancing the ref, and to accept a caller-supplied worktree, over writing a second near-copy in `ipd_lifecycle`. Whichever route is taken, `agent_workflows/commit_lock.py` and `tests/test_isolated_commit.py` become this plan's files and MUST be added to `Scope-Paths`; the 12 tests in that suite pin the current contract and any signature change must keep them green.
  - Depends on: none
  - Expected outcome: the status edit, the plan move and the commit all occur in a coordinator-owned detached worktree; the branch is NOT advanced there; and the only remaining shared-checkout writes are E-06's ff-only merge and E-07's index refresh.
  - Execution state: performed
- [x] E-02 Keep the journalled transaction and its rollback, and state plainly what each layer now guarantees. The journal (`PHASE_PREPARED` -> `PHASE_MUTATING` -> `PHASE_READY_TO_COMMIT` -> `PHASE_COMMITTED_INCOMPLETE`/`PHASE_COMPLETE`, `:132-147`) plus `_rollback_precommit` (`:1874`) handle crash recovery ACROSS invocations; the throwaway worktree shortens the shared-tree exposure WITHIN one invocation. These are complementary, not redundant. Do NOT delete the journal in the belief the worktree replaces it: `PHASE_COMMITTED_INCOMPLETE` and `PHASE_UNKNOWN_OUTCOME` still classify outcomes the CAS cannot.
  - THE JOURNAL MUST NOW COVER ONE MORE FAILURE, which is a consequence of E-06 rather than of the worktree. Once the commit lands by CAS but the shared-tree fast-forward REFUSES, the repository is in a genuinely new state: the transition is committed and correct on the ref, while the working tree still shows the old layout. That is a `PHASE_COMMITTED_INCOMPLETE` situation and must be recorded as one, not reported as success and not rolled back (rolling back a landed commit is exactly what `_resume_post_commit` refuses to do, `:2884-2891`). Say so in the journal's phase documentation.
  - Depends on: E-01
  - Expected outcome: crash recovery still works; the docstrings say which layer covers within-invocation exposure and which covers across-invocation crashes; and a refused reconciliation is classified committed-incomplete rather than as success or as a rollback.
  - Execution state: performed
- [x] E-08 Make `_rollback_precommit` STOP writing to the shared checkout for a mutation it no longer performed there. FOUND AND MEASURED AT REVIEW ROUND 3 (PR-024, F-14): this is the one finding in this plan whose failure mode is DESTROYING A CO-WORKER'S UNCOMMITTED BYTES, which is the exact harm the whole Set exists to stop.
  - THE DEFECT, and why it is CREATED by E-01 rather than merely uncovered. Step 2 of `_rollback_precommit` (`:1910-1920`) unconditionally writes `journal["original_bytes"]` over `original_path`. That is correct TODAY, because this transaction is the party that moved that file away, so nothing else can legitimately be there. Once E-01 performs the relocation in the coordinator worktree, the shared-tree file is NEVER TOUCHED by the transaction, so the same write becomes an unconditional overwrite of whatever the shared tree currently holds. Note the asymmetry that makes this reachable: step 1 (`:1888-1908`) DOES carry a concurrency guard, comparing the destination against `journal["moved_bytes"]` and refusing a destructive restore on mismatch, but `original_path` has no such guard because until now it needed none.
  - MEASURED, against the real function. With a journal shaped as the new sequence leaves it and a peer edit in flight at the plan's pending path, `_rollback_precommit` overwrote the peer's content with the snapshot bytes: before `'- Status: approved\nPEER EDIT IN FLIGHT, uncommitted\n'`, after `'- Status: approved\nORIGINAL\n'`. The peer's bytes were gone. (The call also returned `ok=False` for an unrelated fixture reason, the manifest path, which is itself instructive: the destructive write happens in step 2 and is NOT undone by the later failure, so a rollback that reports failure has already destroyed the edit.)
  - THE FIX: give `original_path` the same guard `dest_path` already has. Restore it only when the transaction actually mutated it, or when its current bytes match what the transaction believes it wrote; otherwise refuse the destructive restore and classify unknown-outcome, exactly as step 1 does, naming the path. Under the new sequence the ordinary case needs no write at all, because the shared-tree file was never moved, so the correct default becomes "leave it alone".
  - THIS ALSO MEANS THE ROLLBACK MUST NOT UNDO THE FF-ONLY MERGE. If the reconciliation succeeded, the commit has landed and the rollback path is not the right tool (see E-02). If it refused, nothing was written and there is nothing to restore. Say both in the docstring so a later reader does not add a "helpful" reset.
  - Depends on: E-01
  - Expected outcome: a rollback performed after a worktree-side mutation writes NOTHING at the plan's original path when the shared-tree bytes are not the transaction's own, refuses with an unknown-outcome classification naming the path instead, and a test proves a peer's in-flight edit to the plan file survives a failed retirement byte for byte.
  - Execution state: performed

### Task group 3: measure what the window actually became

- [x] E-05 Add a test that measures the shared checkout's state at each observable instant of a SUCCESSFUL retirement, and pins the improvement the change actually delivers rather than a claim of cleanliness the mechanism cannot support (see E-01's weakened outcome and F-7).
  - THE PLAN ORIGINALLY PRESCRIBED A TECHNIQUE THAT CANNOT WORK, corrected here. It said to use "the fault-injection hooks `after_move` and `before_commit`" to observe those instants. Fault injection RAISES `_InjectedFault` and aborts the transaction (`:2593-2595`, `:154-155`), so it can only ever observe a FAILED retirement; by construction it cannot observe a successful one at those points. USE THE SEAM REVIEW ACTUALLY USED, which needs no production change: patch `_refresh_plans_index_fail_loud` to sample `git status --porcelain` at the post-move instant, and patch `commit_lock.commit_isolated` to sample it at the pre-commit instant, delegating to the real function in both cases. That produced the F-1a measurement and is reproducible.
  - THE ASSERTION IS A COMPARISON, NOT AN ABSOLUTE. Record the samples before the change (F-1a's values are the baseline: `RM pending/... -> executed/...` at post-move, `R  ...` plus the two untracked manifests at pre-commit) and after it, and assert that the post-change samples show NO staged rename and NO moved plan in the shared tree at either instant. Whatever residue remains must be enumerated in the test's own docstring, so the next reader learns the real property instead of inferring a stronger one. F-1a's baseline was RE-MEASURED at review round 3 against HEAD `5b0396b0` and reproduced exactly, so it is trustworthy as a baseline; capture it again anyway, since the plan's own rule is that a baseline comes from the same commit.
  - THE SEAM ITSELF MOVES, WHICH THE EXECUTOR MUST HANDLE RATHER THAN DISCOVER (added at review round 3). Both patch points named above are changed by this plan's own items: E-07 relocates `_refresh_plans_index_fail_loud` to AFTER the reconciliation, so it is no longer the post-move instant, and F-11 establishes that `commit_isolated` is no longer the call that commits this transaction, so patching it no longer observes the pre-commit instant. So capture the BEFORE samples FIRST, against unmodified code, using the seam as described; then choose the equivalent post-change instants in the new sequence (immediately after the coordinator worktree's commit and immediately before the ff-only merge are the natural ones) and say in the test's docstring which instant each sample corresponds to and why it is the counterpart of the original. A test that silently samples different instants before and after is not a comparison.
  - Depends on: E-01, E-02, E-06, E-07
  - Expected outcome: a test that names, for each observable instant, exactly what the shared checkout holds after the change, and fails if the mutation or the commit returns to the shared tree.
  - Execution state: performed

### Task group 4: reconcile the shared tree honestly

- [x] E-06 Bring the shared checkout into line with the new HEAD by a fast-forward that git performs and that REFUSES rather than clobbers. This item exists because review measured that E-01 alone leaves the tree dirty in the inverse direction (F-7), which is worse than the state it replaces.
  - THE MECHANISM, measured in a scratch repo before being prescribed: after the CAS advances the branch, run the reconciliation in the shared checkout as a `--ff-only` merge of the landed commit. VERIFIED CLEAN CASE: with an unrelated peer edit in flight (`peer.txt` modified), the ff-only merge applied the rename, left `git status --porcelain` reading exactly ` M peer.txt`, and the peer's uncommitted bytes were preserved verbatim. VERIFIED REFUSAL CASE: with a local modification to the very plan file being moved, git REFUSED (rc=1, "Your local changes to the following files would be overwritten by merge"), the working tree kept the peer's content, and nothing was lost. That refusal is the correct outcome and must be reported, never forced: do NOT reach for `git checkout -f`, `git reset --hard`, or a manual file move, each of which destroys the co-worker's edit that git just protected.
  - THE ORDER OF CAS-THEN-FF-ONLY IS WRONG AND WOULD SHIP A NO-OP. FOUND AND MEASURED AT REVIEW ROUND 2 (PR-013), reproduced twice. If `git update-ref refs/heads/main <new> <old>` runs FIRST, then by the time the reconciliation runs the branch ALREADY points at the landed commit, so `git merge --ff-only <landed>` prints "Already up to date." and exits 0 WITHOUT TOUCHING THE WORKING TREE. Measured shared-tree state after that sequence: `D  p/executed/plan.md`, `A  p/pending/plan.md`, ` M peer.txt`. So the reconciliation reports SUCCESS while leaving the tree dirty in the inverse direction, which is exactly the state F-7 says must not be shipped, and the ff-only refusal branch this item relies on becomes UNREACHABLE (there is nothing left to fast-forward, so git never checks for an overwrite).
  - THE CORRECT SEQUENCE IS TO LET THE FF-ONLY MERGE BE THE THING THAT ADVANCES THE BRANCH. Do NOT advance `refs/heads/main` yourself and then reconcile. Instead leave the branch where it is and run `git merge --ff-only <landed-commit>` in the shared checkout as the SINGLE operation: it moves the ref AND updates the working tree in one step, and it is the operation whose refusal protects a peer. MEASURED, same fixture, with an unrelated peer edit in flight: rc=0, "Updating <old>..<new> / Fast-forward", the plan ends at its `executed/` path, `p/pending/` is gone, `git status --porcelain` reads exactly ` M peer.txt`, the peer's bytes are verbatim, and HEAD equals the landed commit. MEASURED CONTENDED CASE, same sequence with a peer modification to the plan being moved: rc=1 with git's own "Your local changes to the following files would be overwritten by merge: p/pending/plan.md ... Aborting", the peer's edit intact, and HEAD NOT ADVANCED. Note the consequence for E-02: in this ordering a refusal leaves the commit UNREACHABLE FROM main rather than landed-but-unreconciled, so it is NOT `PHASE_COMMITTED_INCOMPLETE`; classify it by what actually happened and say which, rather than inheriting E-02's wording.
  - WHICH MEANS `commit_isolated` CANNOT BE USED UNCHANGED HERE, and the executor must confront that rather than discover it. `commit_lock.commit_isolated` performs the CAS itself (`commit_lock.py:270`), which is precisely the step that must NOT precede the reconciliation. So E-01's "reuse `commit_isolated`" and this item's mechanism are in tension: either `commit_isolated` grows a way to return the commit WITHOUT advancing the branch (so the caller reconciles by ff-only), or the reconciliation must be something other than a fast-forward. Resolve this explicitly in E-01, name the route chosen in a code comment, and do not assume the two items compose as written.
  - REPORT A REFUSAL AS COMMITTED-INCOMPLETE, per E-02, naming the paths git objected to and the landed commit, so an operator can reconcile by hand. Note the existing `_assert_rollup_touched_only_owned_paths` gate (`:2155-2184`) already refuses up front when the ORCHESTRATOR'S OWN plan file is dirty, so the most likely refusal cause is excluded before any mutation; this branch handles the residual race in which that becomes true during the transaction.
  - A DIVERGED BRANCH IS A THIRD ARM, DISTINCT FROM THE CONTENDED ONE, AND IT MUST BE CLASSIFIED SEPARATELY. FOUND AT REVIEW ROUND 3 (PR-023, F-13). E-06 as written measures only two cases (clean, and a peer editing the moved file). If a peer COMMITS anything to main between the coordinator worktree's snapshot and the merge, the branch has DIVERGED and no fast-forward exists. MEASURED: `git merge --ff-only <landed>` then exits **128** (not 1) with "fatal: Not possible to fast-forward, aborting", HEAD unmoved, the landed commit NOT an ancestor of HEAD, and the shared tree CLEAN (`git status --porcelain` empty) with the plan still at `pending/`. This is exactly the condition `commit_isolated` reports as `ISO_RACED` today, so classify it the same way and reuse that vocabulary rather than inventing a second one: the work exists as a reachable commit, the branch was not moved, and the operator is told to retry. Distinguish the arms by EXIT CODE and by whether the tree is dirty, not by string-matching git's prose, which differs between the two (`error:` + rc=1 for the overwrite refusal, `fatal:` + rc=128 for divergence).
  - Depends on: E-01
  - Expected outcome: on the clean path the shared checkout ends with the plan in `executed/`, no staged rename, `git status --porcelain` showing only unrelated peer dirt, and HEAD equal to the landed commit; on the contended path the reconciliation refuses with git's own text (rc=1), the peer's bytes survive, main is NOT advanced, and the outcome is reported honestly with the objecting paths named; on the diverged path (rc=128) the outcome is reported as a race with the landed commit named. The ff-only merge, not a separate `update-ref`, MUST be what advances the branch.
  - Execution state: performed

### Task group 5: keep the index gate live under the new ordering

- [x] E-07 Refresh the plans manifests AFTER the reconciliation lands the rename, not before it, and keep the fail-loud gate meaningful. THIS ITEM EXISTS BECAUSE REVIEW ROUND 3 MEASURED THAT E-01 SILENTLY BREAKS THE `plans-index-refresh-fail-loud` GATE (PR-022, F-12), which `ROLLUP_SHARED_GATES` (`:2066`) declares the rollup keeps and which spec `77tr3o` OQ-1 requires a test to pin.
  - THE MECHANISM OF THE BREAKAGE, measured in the repository's own fixture. `_refresh_plans_index_fail_loud` (`:1656-1695`) regenerates the manifests by scanning the plans tree ON DISK (`plans_index.scan_plans` walks `plans_dir.rglob("*.md")`, `plans_index.py:99`) and then re-runs `--check` and RAISES if it did not converge. Today it runs at `:2700`, INSIDE the mutating phase, AFTER the shared-tree `git mv`, so the disk it scans already shows the plan at `executed/`. Once E-01 moves that relocation into the coordinator worktree, the shared disk still shows the plan at `pending/` when the refresh runs, so the manifest is generated describing the OLD layout, converges against it, and the gate PASSES. Then the ff-only merge relocates the file and the manifest is instantly stale. MEASURED: after that sequence, the manifest contained the `pending/` path and not the `executed/` one, and `aw index plans --check` returned rc=1 reporting `INDEX.json: check.stale-index-stale` and `INDEX.md: check.stale-index-stale`, both at `warning` severity (`check_engine.py:336`), which fails the gate.
  - WHY THIS IS THE SERIOUS ONE. The gate does not merely mis-order; it INVERTS. It reports success on a manifest it can already tell is about to be wrong, and the repository is left in exactly the `check.stale-index-stale` state the gate exists to prevent, with no failure recorded. F-9 already established that the test guarding this gate (`tests/test_orchestrator_retirement.py:2079`, `:2104`) asserts only that the gate's NAME appears in `ROLLUP_SHARED_GATES`, so it cannot detect a gate lost in fact. That is the same invisible-divergence class OQ-03 was resolved to avoid, arriving by a different door.
  - THE FIX: move the refresh to AFTER the reconciliation succeeds, so it scans a disk that already holds the final layout, and keep it fail-loud. Note the consequence for the journal, which is E-02's business: the refresh then happens AFTER the commit has landed, so a refresh failure is no longer a pre-commit failure that can be rolled back. It is a `PHASE_COMMITTED_INCOMPLETE` condition and must be recorded as one. Do NOT roll back a landed commit to undo a manifest regeneration; the manifests are gitignored generated views (`.aw/.gitignore:45-46`) whose remedy is mechanical (`aw index plans`), and `_resume_post_commit` (`:2884-2891`) already establishes that a landed lifecycle commit is resumed, never reverted.
  - DO NOT INSTEAD REGENERATE IN THE WORKTREE. F-9 measured that route and it fails: the manifests are gitignored, a fresh detached worktree never receives them, and a regeneration there is discarded with the worktree while the shared copies keep stale bytes. That is how OQ-02 was resolved, and this item must not reopen it.
  - Depends on: E-01, E-06
  - Expected outcome: the manifests are regenerated from the post-reconciliation disk, `aw index plans --check` is clean in the fixture after a successful retirement, the fail-loud gate still raises on a genuine non-convergence, and a post-commit refresh failure is classified committed-incomplete rather than rolled back.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A WORKER may commit facts about its own item; only the COORDINATOR may commit facts about a whole Set. Retirement asserts every child of a Set is executed, so it is coordinator-only and re-checks eligibility itself rather than trusting the caller ("Kind alone is NOT authority"). This plan changes WHERE the coordinator works, never WHO may retire.
- `commit_isolated` is the shipped precedent for "run the real hooks somewhere private, then advance the ref under a CAS". It even reports `ISO_RACED` when a peer commit landed since the snapshot, which is the honest outcome rather than silently discarding their work.
- THE RETIREMENT ALREADY COMMITS THROUGH `commit_isolated` TODAY, which review verified and which materially narrows this plan's remaining value. `_finalize_transaction` calls it at `:2752` with an explanatory comment ("Committing in the SHARED tree lets `pre-commit` stash the whole working tree ... `commit_isolated` runs the SAME hooks in a private detached worktree"). So the COMMIT is already isolated on both paths; what is still performed in the shared checkout is the status edit and the `git mv`, plus the index regeneration. State this plainly so nobody executing this plan believes they are introducing worktree isolation to a path that has none.
- THE TRANSACTION BODY IS SHARED, WHICH IS THE PLAN'S REAL ARCHITECTURAL CONSTRAINT. `_finalize_transaction` (`:2559`) has exactly two callers, `finalize` (`:2544`) and `retire_orchestrator` (`:2405`), verified by grep. Any change to where its mutations happen is a change to EVERY plan's terminal transition. See F-8 and OQ-03.
- Retirement deliberately omits the pre-transition E/V checkpoint because an orchestrator's items are performed by its children. That omission is recorded in `ROLLUP_OMITTED_GATES` and is out of scope here.
- `aw check` REPORTS `check.lifecycle-transition-invalid` FOR THIS PLAN, AND THAT REPORT IS A CHECKER LIMITATION, NOT A DEFECT IN THE PLAN'S HISTORY. DO NOT EDIT THE WORKFLOW HISTORY TO SILENCE IT. The offending step is `reviewed -> to-review`, a REAL maintainer act: round 1 reviewed the plan, the maintainer then sent it back for another round via `aw set`. `validate_transition` treats any rank decrease as backwards and `check_lifecycle_transitions` exempts only off-sequence targets, so a legitimate re-review demotion has no representation. Verified at review round 3: the flag reproduces against the COMMITTED pre-edit file, so it predates this round's revisions, and 15 plans repo-wide carry it including siblings in this Set. The identical finding was already recorded in this Set's Order 01 and in `orchprobe` PR-014, so it is a known cross-Set pattern owned by the check engine, not by this plan.
- THE PLAN MOVE IS A `git mv`, NOT A WRITE-THEN-UNLINK, and it is deliberate: `status_set.apply_status_change` records that `git mv` makes the relocation "a SINGLE staged rename, so there are no halves to pair up" (`status_set.py:902-919`). That is why the mid-transaction shared-tree state reads `RM`/`R ` rather than as an untracked addition plus a deletion, and it is why a bare CAS leaves an INVERSE rename rather than nothing (F-7).

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | Retirement is three mutations, not one, and only the last is a commit. So there is a window in which the shared checkout holds a moved-but-uncommitted plan. | `retire_orchestrator` (`ipd_lifecycle.py:2187`) delegates the status change to `status_set`, then the finalize transaction stages and commits; phases `PHASE_MUTATING` and `PHASE_READY_TO_COMMIT` (`:133-138`) name that window explicitly |
| F-1a | THE WINDOW IS CONFIRMED BY DIRECT OBSERVATION, added at review so the plan rests on a measurement rather than on reading the phase names. Instrumenting a real SUCCESSFUL rollup retirement and sampling `git status --porcelain` in the fixture at two instants gave: post-move `RM .aw/records/plans/pending/<plan> -> .aw/records/plans/executed/<plan>`, and pre-commit `R  <same rename>` plus `?? .aw/records/plans/INDEX.json` and `?? .aw/records/plans/INDEX.md`. So the maintainer's challenge is correct and this is the baseline E-05 must improve on. | measured at review by patching `_refresh_plans_index_fail_loud` and `commit_lock.commit_isolated` around `retire_orchestrator(apply=True)` in the repo's own fixture |
| F-2 | The journal provides RECOVERY, not atomicity. A failure is repaired by replaying or rolling back on a later invocation, which is strictly weaker than a ref update that either happened or did not. | `_rollback_precommit` (`:1874-1925`) and the `PHASE_COMMITTED_INCOMPLETE` / `PHASE_UNKNOWN_OUTCOME` classifications (`:139-144`) |
| F-3 | A FAILED retirement does not restore the tree it started from. Measured with the shipped fault injector: tree before was empty; after `after_move` the plan was correctly restored and HEAD unmoved, but the tree held `?? .aw/records/plans/INDEX.json` and `?? .aw/records/plans/INDEX.md`. | reproduced during authoring via the repository's own test harness |
| F-3a | SEVERITY QUALIFIER ADDED AT REVIEW, so the fix is not oversold: in THIS repository both index files are GITIGNORED (`.aw/.gitignore:45-46`, confirmed with `git check-ignore -v`; neither is tracked), so they do not appear in `git status --porcelain` here at all and cannot dirty this checkout. The residue was observed in the test harness's own fixture repo, which does not carry that ignore rule. So F-3 is a real correctness defect in the rollback (it writes files it does not restore) and is worth fixing, but it is NOT a live cause of the 2026-09-13 outage and must not be described as one. E-04's tree-cleanliness assertion is the durable value here, because it pins the property in the fixture where the residue IS visible. | `.aw/.gitignore:45-46`; `git check-ignore -v .aw/records/plans/INDEX.json`; `git ls-files --error-unmatch` reports both untracked |
| F-4 | The existing fault tests would not catch F-3, because they assert plan restoration and HEAD but never tree cleanliness. | `tests/test_orchestrator_retirement.py:1961-1972` |
| F-5 | Retirement CANNOT be moved into a worker lane, so a coordinator-owned scratch worktree is the only route to a single-ref-update rollup. | `retire_orchestrator`'s first gate refuses `AW_EXECUTION_ROLE=worker` (`ipd_lifecycle.py:2237-2246`), and a lane turn runs as worker |
| F-6 | Retirement spends no agent turn and runs as an ordinary queue item on both hosts, so it is CHEAP. CORRECTED AT REVIEW on the second half: it is NOT frequent, and the original "so the window is hit often" overstated the exposure. Measured across the whole tracked corpus, exactly 4 plans carry a rollup retirement history line, against 41 plans in `executed/` carrying `Kind: orchestrator`. So the window is real (F-1a) but is entered rarely, which is why this plan is `Priority: medium` while its siblings are `high`. | `dispatch_orchestrator_item` (`runner_shared.py:3258`), called from `oc_runipd.py:7386` and `agy_runipd.py:4398`; corpus counts measured at review by grepping for the `rollup_history_message` prefix |
| F-7 | THE CENTRAL MECHANISM DOES NOT DELIVER "NO WRITE TO THE SHARED CHECKOUT", so the plan's original goal and V-01's demanded proof were both unobtainable. Built by hand: commit the rename in a detached worktree, advance the branch by `git update-ref <ref> <new> <old>`, and the shared checkout then reads `R  p/executed/plan.md -> p/pending/plan.md` -- dirty in the INVERSE direction, because HEAD holds the new path while the working tree holds the old one. Adding `commit_isolated`'s own trailing `git reset --quiet HEAD -- <rel>` yields ` D p/executed/plan.md` plus `?? p/pending/` instead, which is no better. The shared tree must therefore be reconciled, and the honest mechanism is a REFUSING fast-forward: measured, `git merge --ff-only <landed>` applies the rename and leaves an unrelated peer's ` M peer.txt` untouched, and when a local change to the moved file would be overwritten it exits 1 preserving the peer's bytes. Addressed by E-06; E-01's outcome and the plan's Goal both rewritten. AMENDED AT REVIEW ROUND 2: the reconciliation prescribed here was measured as an ff-only merge run AFTER the CAS, and in that order it is a NO-OP that reports success (see F-10). The ff-only merge is still the right mechanism; it must simply BE the step that advances the branch rather than following a step that already did. The clean/refusal behaviors quoted here were re-measured and hold in the corrected ordering. | measured at review in scratch repos under `/tmp`; the reset whose effect was tested is `commit_lock.py:281-284`; ordering correction measured at round 2 (F-10) |
| F-8 | THE BLAST RADIUS IS THE WHOLE TERMINAL TRANSITION, WHICH THE PLAN NEVER DECLARED. `_finalize_transaction` (`:2559`) is shared code with exactly two callers: `finalize` (`:2544`), the path every ordinary plan and `aw set executed` takes, and `retire_orchestrator` (`:2405`). Relocating its mutations therefore changes the transition for all 500+ plans, not only the 4 rollup retirements F-6 counts; confining the change to the rollup instead means a SECOND transaction body, which is exactly the drift spec `77tr3o` OQ-1 accepted as a known cost and instructed be minimized. Neither option is an executor's to pick. Escalated as blocking OQ-03. | callers verified by grep over `agent_workflows/`; the accepted-cost wording is `.aw/records/specs/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md:220-227` |
| F-11 | `commit_isolated` CANNOT BE REUSED FOR A MUTATION PERFORMED IN A DIFFERENT WORKTREE, so E-01's central "reuse the existing pattern" instruction was not implementable as written. FOUND AT REVIEW ROUND 3. Its copy direction is SHARED -> WORKTREE: it creates its own detached worktree and mirrors each named path from the shared tree into it (`shutil.copy2(src, dst)`, `commit_lock.py:226-231`), propagating a deletion when the shared source is absent (`:232-234`). A mutation made in a coordinator-owned worktree is therefore invisible to it, and the paths it is told to commit are absent from the shared tree. MEASURED against the real function: mutate in a coordinator worktree, then call `commit_isolated(repo, ["p/pending/plan.md","p/executed/plan.md"])`; it returned `error` / "git add failed in isolated worktree: fatal: pathspec 'p/executed/plan.md' did not match any files", HEAD unmoved, nothing committed. This is a stronger statement than F-10's CAS-ordering tension: it is not that the two steps compose badly, it is that this helper cannot see the work at all. THE SOUND SHAPE, measured end to end: commit in the coordinator's OWN worktree (staging only paths that exist, since `git add` on the vanished old path exits 128), do NOT advance the ref there, and let E-06's ff-only merge advance it. Result: worktree staged `R100 pending -> executed`, ref at base before the merge, merge rc=0 Fast-forward, shared tree holding the EDITED bytes at `executed/`, status exactly ` M peer.txt`, commit name-status containing only the rename. Addressed by E-01 as rewritten. | measured at review round 3 against `agent_workflows/commit_lock.commit_isolated`; the copy/unlink lines are `commit_lock.py:226-234`; the existence filter precedent is `ipd_lifecycle.py:2720` |
| F-12 | RELOCATING THE MUTATIONS SILENTLY BREAKS THE `plans-index-refresh-fail-loud` GATE, INVERTING IT FROM A GUARD INTO A FALSE PASS. FOUND AT REVIEW ROUND 3 and measured in the repository's own fixture. `_refresh_plans_index_fail_loud` (`:1656-1695`) regenerates the manifests by scanning the plans tree ON DISK (`plans_index.scan_plans` walks `rglob("*.md")`, `plans_index.py:99`), then re-runs `--check` and raises if it did not converge. It runs at `:2700`, inside the mutating phase, AFTER today's shared-tree `git mv`. Once the relocation moves into the coordinator worktree, the shared disk still shows the plan at `pending/`, so the manifest is generated describing the OLD layout, converges against it, and the gate PASSES; the ff-only merge then relocates the file and the manifest is instantly stale. MEASURED: the manifest contained the `pending/` path and not the `executed/` one, and `aw index plans --check` returned rc=1 reporting `INDEX.json: check.stale-index-stale` and `INDEX.md: check.stale-index-stale`, both `warning` (`check_engine.py:336`), which fails the gate. So the transaction reports success while leaving the exact state the gate exists to prevent. `ROLLUP_SHARED_GATES` (`:2066`) declares the rollup KEEPS this gate and spec `77tr3o` OQ-1 requires a test to pin that it does; per F-9 the guarding test checks only the gate's NAME, so this loss would be invisible. Addressed by new E-07. | measured at review round 3 by running `_refresh_plans_index_fail_loud` with the plan still at `pending/`, then relocating it and re-running `plans_index.run_index(check=True)`; severity at `check_engine.py:336`; gate declaration at `ipd_lifecycle.py:2066` |
| F-13 | A DIVERGED BRANCH IS A THIRD RECONCILIATION ARM WITH A DIFFERENT EXIT CODE, WHICH E-06 DID NOT MEASURE. FOUND AT REVIEW ROUND 3. If a peer COMMITS to main between the coordinator worktree's snapshot and the merge, no fast-forward exists at all. MEASURED: `git merge --ff-only <landed>` exits **128** (not the 1 of the overwrite refusal) with "fatal: Not possible to fast-forward, aborting"; HEAD is unmoved, the landed commit is NOT an ancestor of HEAD, and the shared tree is CLEAN with the plan still at `pending/`. That is materially different from the contended case (dirty tree, rc=1, `error:` prefix) and must be classified separately; it is precisely the condition `commit_isolated` already reports as `ISO_RACED` (`commit_lock.py:270-279`), so that vocabulary should be reused rather than a second one invented. Distinguish the arms by exit code and tree state, never by string-matching git's prose. Addressed by an added bullet in E-06 and by V-06. | measured at review round 3 in a scratch repo: a peer commit landed on main, then `git merge --ff-only` returned rc=128 "fatal: Not possible to fast-forward, aborting" with `git status --porcelain` empty and `git merge-base --is-ancestor <landed> HEAD` false |
| F-14 | THE ROLLBACK BECOMES A PEER-DATA-DESTROYING WRITE, WHICH IS THE HARM THIS WHOLE SET EXISTS TO STOP. FOUND AT REVIEW ROUND 3 and measured against the real function. Step 2 of `_rollback_precommit` (`:1910-1920`) unconditionally writes `journal["original_bytes"]` over `original_path`. That is correct TODAY because this transaction is the party that moved that file away. Once E-01 performs the relocation in the coordinator worktree, the shared-tree file is never touched by the transaction, so the same write becomes an unconditional overwrite of whatever a peer has there. The asymmetry that makes it reachable: step 1 (`:1888-1908`) DOES guard the destination against `journal["moved_bytes"]` and refuses a destructive restore on mismatch, while `original_path` has no guard because until now it needed none. MEASURED with a journal shaped as the new sequence leaves it and a peer edit in flight: before `'- Status: approved\nPEER EDIT IN FLIGHT, uncommitted\n'`, after `'- Status: approved\nORIGINAL\n'` -- the peer's bytes destroyed. The call then returned `ok=False` for an unrelated fixture reason, which is itself instructive: the destructive write is not undone by the later failure, so even a rollback that REPORTS failure has already destroyed the edit. Addressed by new E-08. | measured at review round 3 by calling `ipd_lifecycle._rollback_precommit` with a worktree-shaped journal against a shared-tree file holding peer content; the unguarded write is `ipd_lifecycle.py:1910-1920`, the guarded twin `:1888-1908` |
| F-10 | THE PRESCRIBED CAS-THEN-RECONCILE SEQUENCE IS A NO-OP, AND THE REFUSAL BRANCH IT RELIES ON IS UNREACHABLE. FOUND AT REVIEW ROUND 2 by building both orderings by hand. Sequence as written (worktree commit -> `git update-ref refs/heads/main <new> <old>` -> `git merge --ff-only <new>` in the shared tree): the merge prints "Already up to date." and exits 0 WITHOUT touching the working tree, because the branch already points at the landed commit. Shared-tree state afterwards: `D  p/executed/plan.md`, `A  p/pending/plan.md`, ` M peer.txt`, i.e. the inverse-direction dirt F-7 forbids, while the reconciliation REPORTS SUCCESS. And because nothing remains to fast-forward, git never performs the would-be-overwritten check, so E-06's peer-protecting refusal can never fire. CORRECT SEQUENCE, measured in the same fixture: do NOT advance the ref yourself; run `git merge --ff-only <landed>` in the shared checkout as the single operation. Clean case with an unrelated peer edit in flight: rc=0, "Updating .. / Fast-forward", plan at `executed/`, `p/pending/` gone, status exactly ` M peer.txt`, peer bytes verbatim, HEAD == landed. Contended case (peer modified the plan being moved): rc=1, git's own "Your local changes ... would be overwritten by merge: p/pending/plan.md ... Aborting", peer bytes intact, HEAD NOT advanced. CONSEQUENCE: E-06's ordering is corrected in place, and a refusal in the correct ordering is NOT `PHASE_COMMITTED_INCOMPLETE` (the commit is simply unreachable from main), so E-02's classification wording must not be inherited blindly. It also puts E-01's "reuse `commit_isolated`" in tension with E-06, since `commit_isolated` performs the CAS itself (`commit_lock.py:270`). | measured at review round 2 in two scratch repos under `/tmp`: bare-CAS-then-ff-only left `D `/`A ` staged entries with the merge reporting "Already up to date."; ff-only-as-the-advance left ` M peer.txt` only, and refused with rc=1 on the contended case |
| F-9 | OQ-02'S PREFERRED ROUTE BREAKS THE SUCCESS PATH, so the question is resolved against the author's preference. Both plans manifests are gitignored (`.aw/.gitignore:45-46`), and a fresh detached worktree does not receive a gitignored generated file at all (verified: absent in a newly added worktree). A regeneration performed inside the worktree is therefore discarded with the worktree, and the shared copies retain their STALE bytes (verified: the shared file still read its pre-run content after the worktree was removed). `aw index plans --check` then reports `check.stale-index-stale`, registered `warning`, which FAILS the gate. Worse, that would de-facto remove the `plans-index-refresh-fail-loud` gate from the shared tree while the test guarding it still passes, because the test asserts only that the string is present in `ROLLUP_SHARED_GATES`. Addressed by E-03 restoring prior bytes instead. | measured at review in a scratch repo; severity at `check_engine.py:336`; the string-only assertions at `tests/test_orchestrator_retirement.py:2079` and `:2104` |

## Proposed changes (ordered, validatable)

1. Perform the status edit, the plan move AND the commit in a coordinator-owned throwaway worktree WITHOUT advancing the branch there (E-01), in the shared `_finalize_transaction` per OQ-03's answered option (a). Per F-11 this cannot reuse `commit_isolated` unchanged.
2. Keep the journal, document which layer covers which failure, and classify a refused reconciliation honestly (E-02).
3. Reconcile the shared tree with a refusing fast-forward that is ITSELF the branch advance (E-06), per F-10, and classify its three arms (clean, contended rc=1, diverged rc=128) per F-13.
4. Refresh the plans manifests AFTER the reconciliation, so the fail-loud index gate keeps guarding instead of falsely passing (E-07), per F-12.
5. Guard the rollback's write to the plan's original path, so a failed retirement cannot destroy a peer's in-flight edit (E-08), per F-14.
6. Measure and pin what the window actually became, using a real observation seam rather than fault injection (E-05).

ORDER MATTERS AND IS NOT THE LIST ORDER ABOVE FOR E-05, which is last deliberately: it measures the finished mechanism. But note E-07 and E-08 are NOT optional polish. Each closes a defect that E-01 CREATES: without E-07 a declared gate silently inverts, and without E-08 a failed retirement destroys a co-worker's bytes. Shipping E-01 without both is strictly worse than shipping nothing.

CORRECTED AT REVIEW ROUND 2 (PR-015): this list previously named E-03 and E-04 as items of this plan and
told the executor to fall back to them if OQ-03 ruled against relocation. NEITHER EXISTS HERE ANY MORE:
both were CARVED OUT to Order 06 (`4xt6u4`) at the earlier revision, as the Scope line and the deferred
section already say. Nothing in this plan is gated now (OQ-03 is answered), so there is no fallback
subset to describe, and an executor who went looking for E-03/E-04 here would find no such checklist
items. The index-residue fix and its assertions belong to Order 06 and are validated there.

## Deferred / out of scope (with reason)

- Moving retirement into a worker lane. Impossible by design per F-5; the worker-role gate refuses it, and that gate is correct because retirement is a Set-level claim.
- Removing the journalled transaction. Complementary to the worktree per E-02, and it still classifies outcomes a CAS cannot.
- Changing the eligibility rule, the `Kind: orchestrator` gate, or the omitted pre-transition checkpoint. All out of scope; this plan changes only where the coordinator performs its writes.
- Making the plans index tracked, or changing HOW it is generated. Still out of scope. CORRECTED AT REVIEW ROUND 3: this entry cited E-03, which lives in Order 06, and it now needs a sharper boundary because E-07 changes WHEN the refresh runs. Moving the refresh's POSITION in the transaction is IN scope (F-12 makes it mandatory); changing the generator, the manifest format, or the manifests' tracked/gitignored status is NOT. Note F-9 makes this boundary load-bearing rather than merely tidy: because the manifests are gitignored, moving their GENERATION into a worktree is not a free relocation, which is why E-07 moves the timing and not the place.
- STRENGTHENING THE STRING-ONLY DRIFT TEST that F-9 found (`tests/test_orchestrator_retirement.py:2079`, `:2104` assert only that a gate NAME appears in `ROLLUP_SHARED_GATES`, so a gate could be removed in fact while the test passes). Real, and out of scope here: it is a test-design gap affecting all ten declared gates, not a retirement bug, and fixing it inside this plan would put an unrelated property in this plan's commit. Worth its own item.
- AUDITING THE OTHER COORDINATOR-SIDE WRITES to the shared checkout. Sibling Orders 03 and 05 each address one; a systematic audit is neither of theirs nor this plan's.

## Scope check

- Over-scope: `agent_workflows/runner_shared.py` was declared in `Scope-Paths` at authoring with NO E-item touching it (its only role here is F-6's citation of `dispatch_orchestrator_item`, which is a call site this plan does not change). REMOVED at review, since a declared-but-unmodified path costs the executor a `--scope-ack` at finalize for no reason.
- Under-scope, CLOSED AT REVIEW ROUND 3 (PR-021, PR-025). `Scope-Paths` now declares the five files this plan's E-items actually touch. THREE WERE ADDED at this round: `tests/test_ipd_lifecycle_cli.py`, which round 2 already established this plan needs (the shared-body change makes its 57 tests this plan's regression surface) but which was left undeclared with only a prose instruction to add it later, an obligation an executor would have had to discover at finalize; and `agent_workflows/commit_lock.py` plus `tests/test_isolated_commit.py`, which F-11 makes unavoidable, since `commit_isolated` cannot be reused unchanged and must either gain a no-advance mode or a sibling. A declared path that an E-item genuinely edits is not over-scope; leaving it undeclared until finalize is.
- Under-scope, RE-ASSIGNED AT REVIEW ROUND 2 (PR-015). This note previously obliged E-04 to fix the identical assertion hole in `tests/test_ipd_lifecycle_cli.py` (`:969`, `:985`; the earlier `:968`/`:983` anchors were off by one and are corrected here). E-04 NO LONGER EXISTS IN THIS PLAN, so as written the obligation attached to nothing. It splits in two. (a) THE ROLLBACK-ASSERTION HOLE BELONGS TO ORDER 06, which owns the residue fix and whose E-02 already extends the fault tests; verified at review that `tests/test_ipd_lifecycle_cli.py` has NO `git status --porcelain` tree-cleanliness assertion in either fault test, so the hole is real and Order 06 is where it must be closed. Order 06 declares only `tests/test_orchestrator_retirement.py`, so that plan must add this file to ITS `Scope-Paths`, not this one. (b) THIS PLAN STILL NEEDS THAT FILE, for the independent reason that OQ-03's option (a) changes the shared `_finalize_transaction` and this suite exercises the ordinary finalize path (F-8); add it in the same pass.
- The blast-radius question (F-8) is a scope question the plan cannot settle by itself, which is why it is a blocking open question rather than a scope-check note.

## Required tests / validation

- `tests/test_ipd_lifecycle_cli.py` (57 tests) AND `tests/test_orchestrator_retirement.py` (112 tests) both run and pasted, because OQ-03's answered option (a) changes the shared transaction body that BOTH exercise. CORRECTED AT REVIEW ROUND 2: this line previously required "the existing fault-injection tests, extended with a tree-state-preservation assertion (E-04)", which is Order 06's deliverable and not this plan's. Do not add that assertion here; run these suites as the regression that the shared-body relocation broke nothing. COUNT CORRECTED AT REVIEW ROUND 3 (PR-025): measured at HEAD `5b0396b0`, `tests/test_ipd_lifecycle_cli.py` is **57 passed**, not 58; `tests/test_orchestrator_retirement.py` is 112 passed, which was right. Re-measure both at execution time rather than trusting these integers, and note the suite must be narrowed with `-o addopts=""` to see per-file counts at all (the configured `addopts` supplies `-q -n auto`).
- `tests/test_isolated_commit.py` (12 tests) run and pasted, because F-11 makes `agent_workflows/commit_lock.py` this plan's file: `commit_isolated` must either grow a no-advance mode or gain a sibling, and that suite is what pins its current contract (the CAS arm, `ISO_RACED`, the hook gating, the worktree cleanup). A signature change that leaves those red is a regression, not a refactor.
- THE INDEX GATE MUST BE PROVEN STILL LIVE UNDER THE NEW ORDERING, which is E-07's whole point and is stated separately from the older index bullet below because F-12 measures a DIFFERENT failure than F-9 did. After a successful retirement in the fixture, assert the manifest names the plan's `executed/` path and NOT its `pending/` path, and paste `aw index plans --check` clean. A `check.stale-index-stale` finding here means the refresh still runs before the reconciliation and the gate is falsely passing.
- A PEER'S IN-FLIGHT EDIT TO THE PLAN FILE MUST SURVIVE A FAILED RETIREMENT BYTE FOR BYTE (E-08, F-14). Paste the before and after bytes. This is the one required test whose failure means data loss rather than a wrong report.
- The during-retirement observation test (E-05), passing, with its samples pasted rather than summarized.
- A successful retirement still lands: the orchestrator reaches `executed/`, the commit subject keeps its `lifecycle(<id>)` marker so the journal's observed-state classification still works (`_lifecycle_commit_exists`, `:1867-1869`), and the commit is path-scoped to owned paths only (`tests/test_orchestrator_retirement.py:1251` asserts this via `git show --name-only` and must stay green).
- THE INDEX GATE MUST BE PROVEN STILL LIVE, not merely still named, because F-9 shows the guarding test cannot tell the difference: after a successful retirement, run `aw index plans --check` in the fixture and paste a clean result. A `check.stale-index-stale` finding here means E-03 was implemented the way OQ-02 originally preferred and the gate has been silently lost.
- A CAS race case: a peer commit landing between snapshot and update is reported honestly rather than silently discarding the peer's work (the `ISO_RACED` arm, `commit_lock.py:270-279`, already surfaced at `ipd_lifecycle.py:2758-2762`).
- The E-06 refusal case: a local modification to the plan being moved makes the reconciliation refuse (rc=1), the peer's bytes survive, and the outcome is classified by what actually happened. Paste git's actual refusal. CORRECTED AT REVIEW ROUND 3: this line said the outcome is "committed-incomplete", which F-10 already established is FALSE in the corrected ordering (the commit is unreachable from main, so nothing is committed as far as main is concerned). Classify and paste the real class.
- The E-06 DIVERGED case (F-13), which is a separate arm from the refusal: a peer COMMIT lands on main between the worktree snapshot and the merge, `git merge --ff-only` exits 128 with "fatal: Not possible to fast-forward", HEAD is unmoved, the landed commit is not an ancestor of HEAD, and the result is reported as a race naming the preserved commit. Paste the exit code, not only the message, since the two refusal arms differ by code.
- Both hosts, since `dispatch_orchestrator_item` is shared and called by each (`oc_runipd.py:7386`, `agy_runipd.py:4398`).
- The ORDINARY finalize path, not only the rollup, whatever OQ-03 rules: if the shared transaction body changed, every plan's terminal transition changed with it (F-8), so `tests/test_ipd_lifecycle_cli.py` (58 tests) must be run and pasted alongside `tests/test_orchestrator_retirement.py` (112 tests).
- Full suite run bare (`python3 -m pytest`), with the failure set diffed against a baseline captured from the SAME commit before any edit; paste both counts and the diff. Do not state a baseline from memory: two sibling reviews in this Set each found a plan's claimed baseline to be wrong.

## Spec / documentation sync

- THE GOVERNING SPEC TEXT IS NOT R-4/R-5/R-6, corrected at review. Those requirements are about the transition's HONESTY (R-4), the E/V checkpoint resolution (R-5) and the receipt (R-6), and this plan touches none of them. What DOES govern is spec `77tr3o` OQ-1's recorded ACCEPTED COST (`:220-227`): "two transition paths CAN DRIFT, so the rollup transition must keep every gate the main path applies except the E/V checkpoint ... and a test must pin that it does." That sentence is the reason OQ-03 exists, and whichever way OQ-03 is answered, the answer must be reconciled with it.
- IF OQ-03 RULES "FORK", the spec MUST be amended in this plan, because a second transaction body is precisely the drift that sentence warns against and shipping one silently would leave the spec asserting a discipline the code no longer follows. Add `.aw/records/specs/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md` to `Scope-Paths` before doing so, so the runner announces the declared spec edit before the run starts. IF OQ-03 RULES "CHANGE THE SHARED BODY", no amendment is expected, since the two paths stay one body.
- Update `retire_orchestrator`'s docstring and the `ROLLUP_*` commentary to describe the worktree AND the reconciliation, including what remains written in the shared tree, so a later reader neither reintroduces shared-tree mutation nor believes a stronger property than F-7 supports.

## Open questions

### OQ-01: Reuse `commit_isolated` directly, or add a retirement-specific isolated transaction?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED AT REVIEW FROM CODE, and the question was partly built on a false premise. `commit_isolated` is ALREADY the commit mechanism on this path: `_finalize_transaction` calls it at `:2752`, with a comment explaining that committing in the shared tree lets `pre-commit` stash and restore over a peer's write. So there is nothing to "reuse or fork" for the COMMIT; it is done. What remains is only where the status edit and the `git mv` happen, and for that the answer is REUSE THE SAME WORKTREE rather than write a second isolated-commit helper: `commit_isolated` already creates and tears down a detached worktree (`commit_lock.py:210-292`) and forking a near-copy would duplicate the CAS, the `ISO_RACED` honesty and the cleanup `finally`.
  RE-RESOLVED AT REVIEW ROUND 3, AND THE ANSWER'S SECOND HALF IS NOW WRONG (PR-021, F-11). "Reuse the same worktree" is not available, and the reason is not the shape difficulty this rationale anticipated. MEASURED: `commit_isolated` copies each named path FROM the shared tree INTO its own worktree (`commit_lock.py:226-231`) and propagates a deletion when the shared source is absent (`:232-234`), so its direction is shared -> worktree and a mutation made in a coordinator-owned worktree is invisible to it. Called that way against the real function it returned `error` / "git add failed in isolated worktree: fatal: pathspec 'p/executed/plan.md' did not match any files", nothing committed. So the commit must happen IN the coordinator's own worktree, and `commit_isolated` must either grow a no-advance mode accepting a caller-supplied worktree or gain a sibling in the same module. The FORK-OR-REUSE INSTINCT of this resolution still holds and is what OQ-04 now puts to the maintainer: do not write a near-copy in `ipd_lifecycle`. What changed is that touching `commit_lock.py` is unavoidable, which is why it and its test suite are now declared in `Scope-Paths`.

### OQ-02: Should the index files be regenerated in the worktree, or restored from the journal on rollback?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED AT REVIEW BY MEASUREMENT, AGAINST the author's stated preference. Regenerating in the worktree is not merely a different route to the same property; it BREAKS the success path (F-9). Both manifests are gitignored, so a detached worktree never receives them, a regeneration there is discarded with the worktree, and the shared copies stay stale, which turns `aw index plans --check` into a `check.stale-index-stale` finding whose registered severity is `warning` and which therefore fails the gate. It would also de-facto remove the `plans-index-refresh-fail-loud` gate from the shared tree while the test guarding that gate still passes, because the test asserts only that the gate's NAME is listed. So: RESTORE PRIOR BYTES FROM THE JOURNAL on rollback (E-03), and leave the success path's regeneration in the shared tree. Recorded as `Reversible: yes`: if a later change makes the manifests tracked, this trade-off should be revisited.

### OQ-03: Change the SHARED transaction body, or fork a rollup-specific one?

- Blocking: yes
- Finding: PR-401
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: NOT resolvable from repository evidence, because the repository documents the cost of one option and the code documents the cost of the other, and choosing between them is an architecture and risk call on the most load-bearing write in the toolkit. THE FACTS, all verified (F-8): `_finalize_transaction` (`:2559`) has exactly two callers, `finalize` (`:2544`) and `retire_orchestrator` (`:2405`). OPTION (a), change it in place: the relocation reaches EVERY plan's terminal transition, including `aw ipd finalize` and `aw set executed`, i.e. 500+ plans rather than the 4 rollup retirements F-6 counts, and any defect in it lands on the path the whole lifecycle depends on. OPTION (b), confine the change to the rollup: that means a second transaction body, which is exactly the drift spec `77tr3o` OQ-1 accepted as a KNOWN COST while instructing that the rollup "must keep every gate the main path applies" and that "a test must pin that it does" (`:220-227`) -- and F-9 shows the test that pins it today cannot detect a gate lost in fact, only one lost in name. THE AUTHOR'S OWN FRAMING ASSUMED (b) WITHOUT SAYING SO: the plan is titled and scoped as being about orchestrator retirement, yet every mechanism it proposes lives in shared code. Blocking because it decides where the code goes, what the blast radius is, and whether this plan must amend an approved spec; and because option (a) is not cleanly reversible once every plan's transition has moved. E-01, E-02, E-05 and E-06 MUST NOT be started before this is answered; E-03 and E-04 are NOT gated and may be executed on their own.
  RESOLVED 2026-09-13 by the maintainer: OPTION (a), CHANGE THE SHARED `_finalize_transaction` IN PLACE. Do NOT fork a rollup-specific body.
  THE DECIDING ARGUMENT IS THE FORK'S, NOT THE SHARED PATH'S. Spec `77tr3o` requires the rollup keep every gate the main path applies, and review established that the test pinning this CANNOT DETECT A GATE LOST IN FACT, ONLY ONE LOST IN NAME (F-9). So a forked copy's divergence would be INVISIBLE, and an invisible failure mode is precisely the class that produced this Set's four measured outages. One implementation with a known, testable risk beats two implementations whose drift cannot be detected. Further, if the moved-but-uncommitted window is a real defect then EVERY plan's terminal transition has it, so fixing only the rollup would leave the larger exposure in place while adding the drift risk.
  THREE OF THE AUTHOR'S EARLIER OBJECTIONS TO OPTION (a) WERE WRONG AND ARE WITHDRAWN, recorded so they are not re-raised. (1) "It reaches 476 plans" was a COUNT OF ALREADY-EXECUTED PLANS, i.e. history, which no code change can reach; the honest scope is the 124 pending plans plus every future one, which is the path every FUTURE finalize takes. (2) "Not cleanly reversible" had no scenario behind it; reverting is reverting a commit, and the status quo is worse on that axis because work-in-main leaves a half-mutated tree needing repair while a ref that never advanced leaves nothing. (3) "Hooks may behave differently in a private worktree" is already the shipped behavior: `commit_isolated` ALREADY runs every hook in a throwaway worktree for every finalize today, so it is not a new risk. A fourth objection (journal/phase re-reasoning) was stated BACKWARDS: the phase machinery exists to clean up exactly the in-main half-mutation this change removes, so it is implementation care, not a cost of the change.
  THE ONE REAL COST, MEASURED AND KEPT: `commit_isolated` advances the branch with a COMPARE-AND-SWAP ref update (`git update-ref <ref> <new> <expected-old>`, `commit_lock.py:270`), NOT a merge. A ref move does not touch working files. Demonstrated in a scratch repository during this resolution: after the CAS, HEAD held the new content while the shared checkout's file still held the old, and `git status` reported it as a MODIFICATION when in truth the working copy was merely stale. Today the code gets away with this because the mutations happen IN MAIN, so the content is already on disk and it only drops the stale index entry (`reset --quiet HEAD -- <paths>`). Once the mutations move into the worktree that no longer holds, so the shared checkout MUST be reconciled to the new HEAD. That reconciliation is E-06's job, it requires a DESTRUCTIVE reset (only `git reset --hard HEAD` cleared the stale state in the demonstration; `restore`/`checkout -- <path>` did not), and in a shared checkout a destructive reset needs its own validation and its own refusal path. This is known, bounded work rather than a hazard, but it MUST NOT be treated as a one-liner.
  OUT OF SCOPE HERE, FILED SEPARATELY: whether `commit_isolated` should MERGE rather than CAS. Under CAS a peer commit landing in the window returns `ISO_RACED`, meaning the work is committed but NOT LANDED (the operator is told to cherry-pick or retry), whereas a merge would land it because the paths are disjoint. That question affects every finalize today, is not caused by this plan, and is therefore its own item.

### OQ-04: `commit_isolated` must gain a no-advance mode or a sibling. Which, given it also backs every `aw` self-commit?

- Blocking: yes
- Finding: PR-021
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: NOT resolvable from repository evidence, because the repository shows the cost of each option and choosing between them is a blast-radius and risk call on the second most load-bearing write in the toolkit. It is the DIRECT DESCENDANT of OQ-03: that question asked whether to change the shared transaction body and was answered "yes, change it in place"; this one asks the same question one layer down, about the shared COMMIT helper, and the answer does not follow automatically because the caller sets differ.
  RESOLVED 2026-09-13 by the maintainer, and NEITHER OPTION (a) NOR (b) WAS CHOSEN: the question is DISSOLVED. `commit_isolated` is not extended and no sibling is added, because the retirement will not call it at all. THE RULING: mint a fresh branch, allocate a worktree on it, perform the status edit and the plan move THERE, commit normally, and merge into main. That is the same pattern every worker lane already uses (`worktree_lease.py:643`, `git worktree add -b aw/lane/<id6> <path> <base>`), and nine of the ten worktrees live in this repository at the time of this ruling are on their own branch by exactly that route.
  WHY THIS WAS AVAILABLE AND THE PLAN MISSED IT. `commit_isolated` needs its awkward shape ONLY because it insists on committing onto `main`, which the operator's own checkout already has checked out. Git permits many worktrees but only ONE PER BRANCH (verified: three simultaneous `git worktree add -b foo/bar/N` succeed from main, while a second worktree on an already-checked-out branch fails with "fatal: 'X' is already used by worktree at ..."). So `commit_isolated` must use `--detach`, which leaves it no branch to commit onto, which is why it then moves main's ref by hand under a compare-and-swap, which is what forces both the copy-in step and the post-CAS reconcile. Minting a NEW branch satisfies the one-worktree-per-branch rule for free and removes all three complications at once.
  MEASURED, so the ruling rests on facts and not on preference. (1) `git worktree add --force <path> main` DOES let a second worktree claim main, and it is a trap: after committing from the forced worktree, the original checkout showed HEAD moved, the file on disk still holding the OLD content, and `git status` reporting a MODIFICATION the operator never made. (2) Three worktrees each on their own branch edited different files, committed independently, left main clean throughout, and all three merged back in sequence. (3) The worker-role gate that refuses this transition (`ipd_lifecycle.py:74-81`) reads only the `AW_EXECUTION_ROLE` environment variable, which the runner sets to `worker` ONLY on a CHILD agent's env and only when that child gets a lane (`oc_runipd.py:5559-5562`); absent, empty and `coordinator` all return False. So a coordinator-owned branch worktree does NOT trip it, and the gate keeps protecting exactly what it was built for: a WORKER manufacturing a claim about a whole Set.
  CONSEQUENCES FOR THIS PLAN, which the executor must apply. The shared commit helper is UNTOUCHED, so `offer_commit`'s documented guarantee and the 12 tests in `tests/test_isolated_commit.py` keep holding without this plan's involvement. The compare-and-swap disappears, and with it F-10's ordering hazard (CAS-before-reconcile shipping a silent no-op) and the destructive `git reset --hard` the reconcile needed: a `git merge` lands the work and updates the working tree in one operation. E-06's reconcile step is therefore no longer a separate concern to get right. THE REMAINING COST, stated honestly: one short-lived branch per retirement, and the merge can REFUSE when main holds conflicting uncommitted work, which is a visible refusal that leaves main clean rather than a silent half-state.
  THE FACTS, all measured at review round 3. F-11 establishes `commit_isolated` cannot be reused as-is: its copy direction is shared -> worktree (`commit_lock.py:226-234`), so a mutation made in a coordinator worktree is invisible to it, and it returned `error` / "pathspec did not match any files" when called that way. F-10 establishes its CAS (`commit_lock.py:270`) must not run before the reconciliation. So it needs BOTH a caller-supplied worktree AND a no-advance return. And it has TWO callers, verified by grep: `ipd_lifecycle.py:2752` (this plan's path) and `git_commit_helper.py:595`, which is `offer_commit`, the single shared commit path behind `aw set`, `aw rename`, `aw commit`, `aw archive`, `aw specs`, `work_cmd` and the runners (7 call sites across 8 modules). AGENTS.md names `offer_commit` as the tooled commit path that is "immune by construction" to sweeping a co-worker's work into a commit, so it is a documented safety guarantee, not merely a helper.
  OPTION (a), EXTEND `commit_isolated` IN PLACE with optional parameters (a caller-supplied worktree, and a flag to return the sha without advancing the ref). One implementation, no drift, consistent with OQ-03's ruling. COST: every change to it is a change to the path behind every `aw` self-commit, and the new parameters create a combination (caller worktree + no advance) that no existing caller exercises, so `offer_commit`'s guarantee is only as safe as the default-argument discipline. OPTION (b), ADD A SIBLING in `commit_lock.py` (for example a `commit_in_worktree` that takes a prepared worktree and returns the sha) leaving `commit_isolated` untouched. COST: two functions that must keep the CAS, the `ISO_RACED` honesty and the cleanup `finally` in agreement, which is the drift spec `77tr3o` OQ-1 named as an accepted-but-minimized cost, and OQ-03 was resolved AGAINST a fork on exactly that reasoning. BENEFIT: `offer_commit`'s path is provably unchanged, and the 12 tests in `tests/test_isolated_commit.py` keep pinning it untouched.
  BLOCKING because it decides whether this plan modifies the commit helper behind every `aw` verb, and because OQ-03's precedent argues for (a) while OQ-03's own reasoning (invisible divergence is the danger) argues that `offer_commit`'s documented guarantee should not be put at risk to avoid a second function. A reviewer should not pick that. E-01 MUST NOT be started before this is answered; E-06, E-07 and E-08 all depend on E-01 and are gated with it. NOTE what is NOT gated and may proceed: nothing in this plan, since every remaining item depends on E-01 either directly or transitively. If the maintainer wants executable work in the meantime, sibling Order 06 (`4xt6u4`) is ungated.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste a successful retirement showing the orchestrator in `executed/` on main, and paste the resulting commit's `git show --name-status`, which must contain ONLY the plan rename. Then paste the two `git status --porcelain` samples taken at the post-move and pre-commit instants (via E-05's seam, NOT fault injection) and state, in words, exactly what each shows. DO NOT ASSERT THEY ARE EMPTY: F-7 measures that they cannot be, and V-01 originally demanded proof of a property the mechanism does not have. The passing criterion is that neither sample contains a staged rename of the plan and neither shows the plan present at its `executed/` path in the shared tree before the commit. Also paste `git rev-list --count <pre>..<post>` showing main advanced by exactly one commit.
  - Observed evidence: PASS. Baseline captured FIRST, against unmodified code at HEAD `73e284a6`
    (transcript: `.aw/state/lane-submissions/run-20260916T182835Z-1650244/05-u23gbn/attempt-1/evidence/baseline-f1a-f12-f14.txt`);
    post-change transcript in the same directory as `postchange-v01-v08.txt`. Durable assertions live in
    `tests/test_orchestrator_retirement.py::TheSharedCheckoutIsNotWhereTheMutationHappens` (4 tests) and
    `tests/test_ipd_lifecycle_cli.py::TheORDINARYFinalizeAlsoMutatesOffTheSharedCheckout` (6 tests), all passing.

    THE SUCCESSFUL RETIREMENT, post-change:

        retire exit_code: 0 | message: finalized orc000 -> executed at 75da7deb334e (actor aw oc run model=test)
        commit --name-status: R082  .aw/records/plans/pending/20260906-post1a-00-orc000-synthetic.ipd.md   .aw/records/plans/executed/20260906-post1a-00-orc000-synthetic.ipd.md
        rev-list --count pre..post: 1

    So the commit contains ONLY the plan rename, and main advanced by exactly one commit.

    THE TWO INSTANT SAMPLES, post-change (`git status --porcelain` in the SHARED checkout), with an
    unrelated peer's uncommitted edit to `peer.txt` in flight throughout:

        pre-commit (inside the coordinator worktree's `git commit`):   " M peer.txt"
        pre-shared-write (the post-move counterpart, immediately
          before the shared checkout is written at all):              " M peer.txt"

    IN WORDS. Each sample shows exactly ONE entry, the peer's own unrelated modified file, which was
    never this transaction's to touch. Neither sample contains a staged rename of the plan (no `R`/`RM`
    entry at all) and neither shows the plan present at its `executed/` path in the shared tree. THIS IS
    NOT A CLAIM OF EMPTINESS: the peer's dirt is present and is expected, and after the transaction the
    two GITIGNORED plans manifests appear as `?? INDEX.json` / `?? INDEX.md` in this fixture (they cannot
    dirty the real repository, whose `.aw/.gitignore` ignores them; see F-3a).

    THE BASELINE THIS IMPROVES ON, for comparison (same fixture shape, unmodified code):

        post-move:   "RM .aw/records/plans/pending/<plan> -> .aw/records/plans/executed/<plan>" + " M peer.txt"
        pre-commit:  "R  .aw/records/plans/pending/<plan> -> .aw/records/plans/executed/<plan>" + " M peer.txt"
                     + "?? .aw/records/plans/INDEX.json" + "?? .aw/records/plans/INDEX.md"

    The staged rename that was present at BOTH pre-change instants is absent at both post-change ones.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste a crash-recovery case (a stale pre-commit journal) still recovering correctly, and paste the docstring text stating which layer covers within-invocation exposure and which covers across-invocation crashes. ALSO paste the new committed-incomplete case from E-02's second bullet: a retirement whose commit landed but whose reconciliation refused, showing the journal phase is `PHASE_COMMITTED_INCOMPLETE`, that the landed commit is still reachable, and that no rollback of it was attempted.
  - Observed evidence: PASS, with ONE PART OF THE DEMAND REPORTED AS UNSATISFIABLE BY CONSTRUCTION
    rather than faked; that is stated first because it is the honest half.

    THE UNSATISFIABLE PART. This item asks for "a retirement whose commit landed but whose reconciliation
    refused, showing the journal phase is `PHASE_COMMITTED_INCOMPLETE`". THAT STATE CANNOT EXIST in the
    ordering the plan itself corrected. F-10 established that the ff-only merge must BE the branch
    advance, so a refusal means the branch never moved and the commit is NOT reachable from it: nothing
    landed as far as the branch is concerned. E-06's own bullet says exactly this ("in this ordering a
    refusal leaves the commit UNREACHABLE FROM main rather than landed-but-unreconciled, so it is NOT
    `PHASE_COMMITTED_INCOMPLETE`; classify it by what actually happened"), and V-06's third bullet
    repeats it. The two demands are therefore in direct conflict, and this V-item's wording is the
    stale one; it was written when the CAS-then-reconcile ordering was still assumed. MEASURED, so this
    is not an argument from prose (`postchange-v01-v08.txt`, contended arm):

        classification: refused-would-overwrite | git rc: 1
        HEAD unmoved: True
        is the abandoned commit an ancestor of HEAD: False
        journal after: unknown-outcome

    The recorded class agrees with reality. `tests/test_ipd_lifecycle_cli.py::
    TheORDINARYFinalizeAlsoMutatesOffTheSharedCheckout::
    test_a_refused_reconciliation_rolls_back_and_is_NOT_committed_incomplete` PINS that it is not
    reported as committed-incomplete, which is the property this item was really protecting.

    THE COMMITTED-INCOMPLETE CASE THAT DOES EXIST is the POST-COMMIT one E-07 creates, and it is
    evidenced instead. Measured:

        retire exit_code: 1
        message: finalize is COMMITTED-INCOMPLETE for orc000: the lifecycle commit 013e5ddb2dec LANDED,
          but the fail-loud plans-index refresh did not converge (did not converge). The commit is NOT
          rolled back (a landed lifecycle commit is resumed, never reverted) ...
        recorded phase: committed-incomplete

    The commit is reachable, no rollback of it was attempted, and the outcome is not success.

    CRASH RECOVERY STILL WORKS, on both paths (actual runner output):

        $ python3 -m pytest -o addopts="" tests/test_orchestrator_retirement.py -q \
            -k "test_a_stale_pre_commit_journal_is_ROLLED_BACK_before_a_fresh_attempt or \
                test_the_transaction_journal_is_written_and_cleared or \
                test_an_injected_pre_commit_FAULT_rolls_the_rollup_back"
        3 passed, 127 deselected in 0.58s

        $ python3 -m pytest -o addopts="" tests/test_ipd_lifecycle_cli.py -q \
            -k "test_crash_restart_before_commit_recovers_on_reinvocation or \
                test_committed_incomplete_then_same_command_resume or \
                test_rollback_preserves_disjoint_dirty_and_staged_work or \
                test_journal_records_ownership_and_is_atomic_before_mutation"
        4 passed, 76 deselected in 0.76s

    THE DOCSTRING NAMING WHICH LAYER COVERS WHAT (`ipd_lifecycle._finalize_transaction`, verbatim):

        WHICH LAYER COVERS WHICH FAILURE, since the journal and the worktree are complementary and
        deleting either would be a mistake:

        * THE WORKTREE shortens the WITHIN-INVOCATION exposure of the shared checkout. It cannot classify
          anything, and it does not survive the process.
        * THE JOURNAL covers ACROSS-INVOCATION crashes. ``PHASE_PREPARED``/``PHASE_MUTATING``/
          ``PHASE_READY_TO_COMMIT`` are rolled back idempotently on the next invocation;
          ``PHASE_COMMITTED_INCOMPLETE`` is RESUMED, never reverted; ``PHASE_UNKNOWN_OUTCOME`` fails
          closed. A compare-and-swap or a fast-forward can express none of that.

    The journal is intact: no phase and no rollback path was deleted.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: paste the observation test's actual samples at both instants, before and after the change, side by side, so the improvement is visible as a diff rather than asserted. The before values must match F-1a (`RM pending/... -> executed/...`; then `R  ...` plus the two untracked manifests) or the discrepancy must be explained. Also paste the test's docstring enumerating what residue remains, and confirm the test does NOT use `fault_injection` for these instants (which raises and aborts, `:2593-2595`, so it cannot observe a successful run).
  - ALSO STATE WHICH INSTANTS THE POST-CHANGE SAMPLES CORRESPOND TO, and why each is the counterpart of the pre-change one. Per E-05's third bullet both original patch points move under E-07 and F-11, so a post-change sample taken at a differently-chosen instant is not comparable. If the counterpart instants are not defensibly equivalent, say so plainly rather than presenting the pair as a diff.
  - Observed evidence: PASS. The test is
    `tests/test_orchestrator_retirement.py::TheSharedCheckoutIsNotWhereTheMutationHappens`, 4 tests, all
    passing (verbose run in `evidence/new-tests-verbose.txt`).

    IT DOES NOT USE `fault_injection` FOR THESE INSTANTS, confirmed: the plan's original prescription
    cannot work, because injecting a fault RAISES `_InjectedFault` and ABORTS the transaction, so it can
    only ever observe a FAILED retirement. The test patches `land_worktree_commit` and
    `ipd_lifecycle._git`, each DELEGATING to the real function, so it observes a genuinely SUCCESSFUL
    retirement. (The class docstring states this.)

    SIDE BY SIDE, same fixture shape, same `git status --porcelain` command:

        instant                     | BEFORE (HEAD 73e284a6, unmodified)                        | AFTER
        ----------------------------+-----------------------------------------------------------+------------------
        post-move / pre-shared-write| RM .../pending/<plan> -> .../executed/<plan>              | " M peer.txt"
                                    | " M peer.txt"                                             |
        pre-commit                  | R  .../pending/<plan> -> .../executed/<plan>              | " M peer.txt"
                                    | " M peer.txt"                                             |
                                    | ?? .aw/records/plans/INDEX.json                           |
                                    | ?? .aw/records/plans/INDEX.md                             |

    The BEFORE values match F-1a exactly (re-measured at execution time rather than trusted; transcript
    `evidence/baseline-f1a-f12-f14.txt`).

    WHICH INSTANTS THE POST-CHANGE SAMPLES CORRESPOND TO, and why they are the counterparts. Both
    original patch points move under this plan, exactly as E-05's third bullet warned, so the instants
    are named rather than assumed:

    * POST-MOVE -> the moment `land_worktree_commit` is ENTERED, i.e. after the status edit, the plan
      move AND the commit have all happened in the coordinator worktree and immediately BEFORE the shared
      checkout is touched at all. This is DEFENSIBLY EQUIVALENT AND THEN SOME: it is strictly LATER in
      the sequence than the old post-move instant, so anything the old sample showed must be absent here
      a fortiori. `_refresh_plans_index_fail_loud` is no longer this instant (E-07 moved it after the
      reconciliation), which is why the seam changed.
    * PRE-COMMIT -> sampled INSIDE the coordinator worktree's own `git commit` invocation. `commit_isolated`
      is no longer the call that commits this transaction (F-11), so patching it would observe nothing and
      pass vacuously; the counterpart is the commit that actually happens.

    THE TEST'S OWN DOCSTRING ENUMERATES THE REMAINING RESIDUE, verbatim: "the peer's own unrelated dirty
    file (never ours to touch), and after the transaction the two GITIGNORED plans manifests
    (`INDEX.json`/`INDEX.md`), which are regenerated generated views that no `aw` verb commits and which
    do not appear in this repository's own `git status` at all because `.aw/.gitignore` ignores them.
    What must NOT appear at either instant is a staged rename of the plan or the plan present at its
    `executed/` path in the shared tree."
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: paste BOTH reconciliation cases from the real code path, not from a scratch repo. CLEAN: an unrelated peer file dirty in the shared checkout, the retirement succeeding, and `git status --porcelain` afterwards showing the peer's entry and nothing about the plan, with the peer's bytes shown unchanged. CONTENDED: a local modification to the plan being moved, git's ACTUAL refusal text pasted, the peer's bytes shown intact, the result reported honestly naming the objecting path, and proof that no `checkout -f` / `reset --hard` / manual move was performed (paste the reconciliation's own command line).
  - THE NO-OP MUST BE RULED OUT EXPLICITLY (F-10), because the broken ordering PASSES every assertion above except this one. Paste the reconciliation's actual git output and show it is NOT "Already up to date.": on the clean path it must read "Updating <old>..<new>" / "Fast-forward". Additionally paste the shared checkout's `git status --porcelain` and show it contains NO staged `D `/`A ` pair for the plan's two paths, which is the exact signature of the no-op ordering. State whether the implementation advances `refs/heads/main` separately; if it does, this item FAILS regardless of the other evidence.
  - ON THE CONTENDED PATH, state and prove which outcome class was recorded and that it matches reality: in the corrected ordering the commit is NOT reachable from main, so `PHASE_COMMITTED_INCOMPLETE` would be a FALSE classification. Paste `git merge-base --is-ancestor <landed> HEAD` (or equivalent) to show whether the commit landed, and show the recorded phase agrees with it.
  - Also paste `aw index plans --check` clean after the successful case, per the index-gate requirement above.
  - Observed evidence: PASS, all THREE arms, through the REAL code path (`retire_orchestrator` in the
    repository's own git-backed fixture, not a scratch repo). Tests:
    `tests/test_orchestrator_retirement.py::TheSharedTreeIsReconciledByARefusingFastForward`, 4 tests,
    passing. Transcript: `evidence/postchange-v01-v08.txt`.

    THE IMPLEMENTATION DOES NOT ADVANCE `refs/heads/main` SEPARATELY. Stated explicitly because this item
    fails outright if it does. The reconciliation is one command,
    `_git(repo_root, ["merge", "--ff-only", landed])` (`ipd_lifecycle.land_worktree_commit`), and
    `test_the_ff_only_merge_is_what_advances_the_branch_not_a_separate_update_ref` asserts on the parsed
    git ARGUMENT LISTS (comments and docstrings stripped, so the check cannot be satisfied by deleting a
    warning) that `_finalize_transaction` contains no `update-ref` and that the lander runs no `reset`,
    `checkout`, `restore`, `clean`, `stash` or `update-ref`.

    CLEAN ARM, with an unrelated peer file dirty in the shared checkout:

        classification: reconciled | git rc: 0
        git said: Updating d0b1f2b..75da7de / Fast-forward
        status afterwards: " M peer.txt" + "?? .aw/records/plans/INDEX.json" + "?? .aw/records/plans/INDEX.md"
        peer.txt bytes: 'peer v2 UNCOMMITTED\n'   (unchanged, verbatim)
        aw index plans --check rc: 0

    THE NO-OP IS RULED OUT EXPLICITLY. git's output reads "Updating <old>..<new>" / "Fast-forward" and NOT
    "Already up to date."; the test asserts both. The shared status contains NO staged `D `/`A ` pair for
    the plan's two paths (nothing about the plan at all), which is the exact signature of the broken
    ordering. `land_worktree_commit` additionally CLASSIFIES an "Already up to date." rc=0 as a race
    rather than success, so the no-op cannot be reported as a clean reconciliation even if it occurred.

    CONTENDED ARM (a peer's edit to the plan being moved lands mid-transaction). git's ACTUAL text:

        classification: refused-would-overwrite | git rc: 1
        objecting paths: ('.aw/records/plans/pending/20260906-postcont-00-orc000-synthetic.ipd.md',)
        Updating 032d7c0..04c4fd5

        error: Your local changes to the following files would be overwritten by merge:
                .aw/records/plans/pending/20260906-postcont-00-orc000-synthetic.ipd.md
        Please commit your changes or stash them before you merge.
        Aborting

        retire exit_code: 2
        PEER BYTES SURVIVED: True
        HEAD unmoved: True
        is the abandoned commit an ancestor of HEAD: False
        journal after: unknown-outcome

    WHICH OUTCOME CLASS WAS RECORDED, AND THAT IT MATCHES REALITY: `git merge-base --is-ancestor <landed>
    HEAD` returns NONZERO, i.e. the commit is NOT reachable from main, so `PHASE_COMMITTED_INCOMPLETE`
    would be a FALSE classification and is not what was recorded. The refusal is surfaced with git's own
    text and the objecting path named. NO FORCING WAS PERFORMED: the reconciliation's own command line is
    `git merge --ff-only <landed>` and nothing else (asserted on the parsed argument lists, above).

    DIVERGED ARM (a peer COMMIT lands on main mid-transaction) - a THIRD arm with its own exit code:

        classification: raced | git rc: 128
        fatal: Not possible to fast-forward, aborting. The branch moved from b869c480c5ec to cf366be1a22c meanwhile.
        retire exit_code: 2
        tip subject: peer landed first
        is the preserved commit an ancestor of HEAD: False
        preserved commit named in the message: True
        shared status: ''            (clean, unlike the contended arm)
        plan back at pending/: True

    The arms are distinguished by EXIT CODE and tree state (1 + dirty vs 128 + clean), never by
    string-matching git's prose, whose wording differs between them.
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: prove the index gate is LIVE under the new ordering, not merely still named. After a successful retirement in the fixture, paste the generated `INDEX.json` content (or a grep of it) showing it names the plan's `executed/` path and does NOT name its `pending/` path, and paste `aw index plans --check` returning clean. Then paste the baseline for comparison: the same two samples taken with the refresh left in its OLD position (before the reconciliation), which per F-12 must show the `pending/` path present, the `executed/` path absent, and `--check` failing with `check.stale-index-stale` on both manifests. A V-07 that shows only the passing case cannot distinguish the fix from the falsely-passing gate it replaces.
  - ALSO prove the gate still REFUSES. Paste a case where the manifest genuinely cannot converge and show `_refresh_plans_index_fail_loud` still raises and the transaction still fails closed, so the fix did not turn a fail-loud gate into a fail-quiet one. State which phase a post-commit refresh failure is recorded as, and show it is not reported as success and not rolled back.
  - Observed evidence: PASS, with BOTH the passing case and the falsely-passing baseline it replaces, so
    the two are distinguishable. Tests:
    `tests/test_orchestrator_retirement.py::TheIndexGateIsStillLiveUnderTheNewOrdering`, 4 tests, passing.
    Transcripts: `evidence/postchange-v01-v08.txt` and `evidence/baseline-f1a-f12-f14.txt`.

    POST-CHANGE, after a successful retirement in the fixture (grep of the generated `INDEX.json`):

        observed call ORDER: ['reconcile', 'refresh']
        manifest grep, executed/ path present: True
        manifest grep, pending/ path present : False
        aw index plans --check rc: 0

    The refresh is proven to run AFTER the reconciliation as an ORDER of observed calls, not merely by a
    passing happy path (`test_the_refresh_runs_AFTER_the_reconciliation_not_before`), because the wrong
    order also passes a happy path.

    THE BASELINE, i.e. the refresh left in its OLD position, measured against unmodified code:

        refresh with the plan still at pending/: RAISED? no (the gate PASSED)
        manifest names the pending/ path: True
        manifest names the executed/ path: False
        INDEX.json: check.stale-index-stale: INDEX.json is out of date; run 'aw index plans'
        INDEX.md: check.stale-index-stale: INDEX.md is out of date; run 'aw index plans'
        aw index plans --check rc after the relocation: 1

    That is the inversion in full: the gate PASSED on a manifest describing the OLD layout, and the
    repository was then left in exactly the `check.stale-index-stale` state the gate exists to prevent,
    with no failure recorded. `test_the_old_position_would_have_produced_a_stale_manifest` pins it, so
    the fix and the falsely-passing gate cannot be confused by a later reader.

    THE GATE STILL REFUSES (fail-loud, not fail-quiet):

        retire exit_code: 1
        message: finalize is COMMITTED-INCOMPLETE for orc000: the lifecycle commit 013e5ddb2dec LANDED,
          but the fail-loud plans-index refresh did not converge (did not converge). The commit is NOT
          rolled back (a landed lifecycle commit is resumed, never reverted) and the manifests are
          gitignored generated views, so the remedy is to run `aw index plans` and then re-run the SAME
          command to resume.
        recorded phase: committed-incomplete

    WHICH PHASE A POST-COMMIT REFRESH FAILURE IS RECORDED AS: `committed-incomplete`. It is NOT reported
    as success (exit_code 1, EXIT_FINDINGS) and the landed commit is NOT rolled back, consistent with
    `_resume_post_commit`, which resumes a landed lifecycle commit and never reverts one. Two
    pre-existing tests that pinned the OLD classification were updated with the reason recorded in their
    docstrings rather than deleted: `test_a_FAILING_plans_index_refresh_fails_the_whole_transaction`
    (retirement) and `test_fail_loud_index_refresh_aborts_transaction` +
    `test_fault_after_index_is_committed_incomplete_not_rolled_back` (ordinary finalize).
  - Result: pass
- [x] V-08 validates E-08
  - Required evidence: paste the peer-preservation case from the real code path. Set a peer's uncommitted edit at the plan's pending path, drive a FAILED retirement whose rollback runs, and paste the file's bytes BEFORE and AFTER, showing them identical. Then paste the recorded outcome, showing the rollback REFUSED the destructive restore and classified unknown-outcome naming that path, rather than reporting a clean restore.
  - THE PRE-FIX BASELINE MUST BE PASTED TOO, because this V-item is otherwise satisfiable by a fixture that never had a peer edit. Per F-14 the pre-fix measurement is: before `'- Status: approved\nPEER EDIT IN FLIGHT, uncommitted\n'`, after `'- Status: approved\nORIGINAL\n'`. Show your own equivalent before-and-after against the unfixed code, then the same case passing after the fix.
  - Observed evidence: PASS, with the PRE-FIX baseline pasted first, since that is what makes this item
    more than a fixture that never had a peer edit. Tests:
    `tests/test_orchestrator_retirement.py::AFailedRetirementCannotDestroyAPeersInFlightEdit`, 4 tests,
    passing.

    PRE-FIX BASELINE, measured against unmodified code at HEAD `73e284a6` with a worktree-shaped journal
    and a peer edit in flight at the plan's pending path (`evidence/baseline-f1a-f12-f14.txt`):

        BEFORE bytes (tail): 'ost-gate lifecycle move).\n\nPEER EDIT IN FLIGHT, uncommitted\n'
        rollback ok: True | message: pre-commit state restored (plan bytes/path + owned Git-index; index regenerated).
        AFTER bytes (tail): ' gate prose (execution contract, post-gate lifecycle move).\n'
        PEER EDIT SURVIVED: False

    The peer's bytes were DESTROYED, and the rollback reported a clean restore while doing it. That
    matches F-14's measurement in kind (F-14 used a minimal plan whose tail read
    `'- Status: approved\nORIGINAL\n'`; this fixture uses the repository's real conforming scaffold, so
    the surrounding bytes differ while the loss is identical).

    POST-FIX, the SAME call, same fixture shape (`evidence/postchange-v01-v08.txt`):

        BEFORE bytes (tail): 'ost-gate lifecycle move).\n\nPEER EDIT IN FLIGHT, uncommitted\n'
        rollback ok: False
        rollback message: unknown-outcome: the plan's original path
          .aw/records/plans/pending/20260906-postrb-00-orc000-synthetic.ipd.md holds content this
          transaction did not write (a concurrent writer's in-flight edit); refusing a destructive
          restore. Those bytes are intact and were NOT overwritten.
        AFTER bytes (tail): 'ost-gate lifecycle move).\n\nPEER EDIT IN FLIGHT, uncommitted\n'
        PEER EDIT SURVIVED: True
        BYTES IDENTICAL: True

    The bytes are IDENTICAL before and after, and the rollback REFUSED the destructive restore and
    classified `unknown-outcome` NAMING the path, instead of reporting a clean restore.

    END TO END through the real transaction, not only the helper (a fault-injected retirement whose
    rollback runs, with the peer's edit landing during the transaction):

        retire exit_code: 2
        message: fault-injected finalize failure (before_commit); rollback FAILED (unknown-outcome: the
          plan's original path ...postrbe2e... holds content this transaction did not write ...);
          journal retained, repository NOT reported restored.
        PEER BYTES IDENTICAL: True
        HEAD unmoved: True

    THE GUARD IS NOT OVER-BROAD, which matters because a guard that refused everything would break the
    case rollback exists for. Two further tests pin the other directions:
    `test_a_genuine_half_move_is_STILL_restored` (an ABSENT origin is restored and the moved destination
    removed) and `test_the_rollback_is_IDEMPOTENT_when_the_origin_already_matches` (re-running a
    completed rollback is a no-op, not a refusal).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit only files this plan changed, path-scoped, never `git add -A`, never push. Paste actual runner output for every test claim; a claimed baseline must be captured from the same commit, never stated from memory. The declared scope is `Scope-Paths`; an out-of-scope edit must be made and then JUSTIFIED with `--scope-reason` at finalize, and a declared-but-unmodified path acknowledged with `--scope-ack`. CORRECTED AT REVIEW ROUND 3: the earlier instruction to ADD `tests/test_ipd_lifecycle_cli.py` to `Scope-Paths` during execution is DISCHARGED, because review has now declared it, along with `agent_workflows/commit_lock.py` and `tests/test_isolated_commit.py` which F-11 makes unavoidable. The declaration is a reviewed contract, so changing it mid-execution invalidates the begin receipt (`frozen_region_digest` covers `Scope-Paths`, `ipd_lifecycle.py:495-503`, and `finalize_precheck` refuses a stale receipt at `:1476-1483`); if a further path proves necessary, make the edit and justify it with `--scope-reason` at finalize rather than editing the declaration. No `77tr3o` amendment is expected (the "fork" branch was not taken).

OQ-04 IS BLOCKING AND GATES EVERY ITEM IN THIS PLAN (added at review round 3, PR-021). OQ-03 is answered, but F-11 exposed a SECOND architecture decision one layer down that OQ-03's answer does not settle: `commit_isolated` cannot be reused as it stands, and fixing it means either extending the helper that backs every `aw` self-commit through `git_commit_helper.offer_commit` (7 call sites across 8 modules) or adding a sibling and accepting a second implementation of the CAS and its `ISO_RACED` honesty. Do not start E-01 before that is answered; E-06, E-07 and E-08 all depend on E-01, so nothing in this plan is executable until it is. Sibling Order 06 (`4xt6u4`) is ungated if executable work is wanted meanwhile.

OQ-03 IS ANSWERED AND NOTHING HERE IS GATED BY IT. CORRECTED AT REVIEW ROUND 2 (PR-014): this paragraph previously read "OQ-03 IS BLOCKING AND GATES MOST OF THIS PLAN ... Do not start E-01, E-02, E-05 or E-06 before it is answered", and it also referred to E-03/E-04, which no longer exist in this plan (they were carved to Order 06). The answer is option (a): change the shared `_finalize_transaction` in place. TWO OBLIGATIONS FOLLOW FROM THAT ANSWER, and they are the reason it is restated here rather than only in the OQ. FIRST, the blast radius is EVERY plan's terminal transition (F-8), so `tests/test_ipd_lifecycle_cli.py` MUST be run and pasted alongside `tests/test_orchestrator_retirement.py`. SECOND, no `77tr3o` spec amendment is expected, because that obligation attached to the "fork" branch which was not taken; do not add the spec file to `Scope-Paths`.

Do not weaken the worker-role gate or the eligibility gate in the course of this change; both are load-bearing and neither is in scope. Do not resolve a refused reconciliation by forcing it (`git checkout -f`, `git reset --hard`, or a manual file move): git's refusal is protecting a co-worker's uncommitted bytes, and destroying them is the exact harm this Set exists to stop.

DO NOT SHIP E-01 WITHOUT E-07 AND E-08, added at review round 3 and stated here because it is the one sequencing constraint an executor could plausibly get wrong while believing they were delivering incremental value. Both fix defects that E-01 CREATES rather than pre-existing ones: without E-07 the `plans-index-refresh-fail-loud` gate that `ROLLUP_SHARED_GATES` (`:2066`) declares the rollup keeps inverts into a false pass, leaving the repository in the `check.stale-index-stale` state the gate exists to prevent while reporting success (F-12); without E-08 a FAILED retirement overwrites a peer's uncommitted edit to the plan file, measured (F-14). Either one alone makes the repository worse than it is today. If the work must be split across runs, E-01 is not the piece that ships first on its own.

Post-gate lifecycle move: this plan reaches `executed/` only when every V-item above carries pasted evidence and `aw ipd lint --phase pre-transition` reports conforming.
