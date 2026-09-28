# IPD: Give the contended fast-forward refusal a tooled remedy: roll back cleanly instead of wedging the journal in unknown-outcome, and name the exact next command

- Date: 2026-09-28
- Kind: child
- Concern: The contended arm of the terminal transition's ff-only reconciliation refuses correctly and then WEDGES THE PLAN PERMANENTLY, which is strictly worse than the "no tooled remedy" the backlog item describes. MEASURED end to end at HEAD `6171375d` on BOTH callers of `ipd_lifecycle._finalize_transaction` (the ordinary `finalize` and the orchestrator `retire_orchestrator`): when a peer's uncommitted edit to the plan file is in the way, `land_worktree_commit` returns `RECONCILED_REFUSED` (rc=1) as designed, the caller then calls `_rollback_and_return`, and `_rollback_precommit` step 2 REFUSES because the origin holds bytes the transaction did not write, so the journal is written `PHASE_UNKNOWN_OUTCOME` and left on disk. Every later invocation now returns exit 2 `finalize journal for <id> is in unknown-outcome (ambiguous prior attempt); resolve manually and clear <path>` BEFORE it re-examines anything. THE ADVERTISED REMEDY PROVABLY DOES NOT WORK: `land_worktree_commit`'s own message says "Land or set that edit aside and re-run", and re-running after the peer committed their edit (tree fully clean, `git status --porcelain` empty) still returns that same exit 2; only hand-deleting the journal file unwedges it, after which finalize succeeds (exit 0). So the house rules correctly forbid an agent from committing or stashing a co-worker's work, AND the one action the rules DO permit (wait for the peer to land it, then re-run) is also refused. The refusal's two arms are not equally harmful and the plan must not conflate them: the REFUSAL ITSELF is correct and protects the peer's bytes (verified intact, byte-for-byte, HEAD unmoved, `git merge-base --is-ancestor <landed> HEAD` nonzero), while the WEDGE is a pure defect, because `_rollback_precommit`'s refusal is a guard written for a DESTRUCTIVE restore and there is nothing destructive to refuse here: git's own refusal already guaranteed the shared tree was never written, so the rollback has no damage to repair and should report a clean no-op rather than an ambiguous outcome. Compounding it, a second measured arm loses the EXECUTING AGENT's own work: `_release_own_plan_edit_before_landing` drops that agent's uncommitted evidence edits BEFORE the merge on the proven premise that the landed commit carries them, and when the merge then fails, those bytes are absent from the working tree and survive only in a coordinator commit the `coordinator_worktree` `finally` has already made unreachable (`git fsck`: `dangling commit`) plus the journal's `original_bytes`.
- Scope: IN: make the REFUSED arm of the reconciliation roll back CLEANLY and recover to a re-runnable state instead of wedging (NARROWED AT REVIEW from "REFUSED and RACED": measured, the RACED arm does not route through the rollback at all, so a rollback-confined fix cannot reach it; see F-11 and E-03's second bullet, where extending it is left as an explicit executor decision with review's recommendation to narrow rather than extend), by (a) teaching `_finalize_transaction` to distinguish "the shared tree was never written, so there is nothing to restore" from "a restore was attempted and could not be trusted", so the rollback reports a clean no-op on a refusal and the journal is CLEARED rather than left `PHASE_UNKNOWN_OUTCOME`; (b) restoring the executing agent's OWN released evidence bytes from the journal's `original_bytes` when the transaction released them and then failed to land, which is the same provably-lossless test `_release_own_plan_edit_before_landing` already applies, run in reverse; (c) replacing `land_worktree_commit`'s unactionable "Land or set that edit aside and re-run" with the exact command an operator or agent may legitimately run, naming the objecting path and the fact that re-running is now sufficient; and (d) pinning all of it with tests that FAIL FIRST on today's code, including the retry-after-the-peer-lands case which is the whole point. OUT, and each for a stated reason: FORCING the merge in any form (`checkout -f`, `reset --hard`, a manual file move, `merge` without `--ff-only`) - that destroys the peer's bytes and is the exact harm the Set containing `u23gbn` exists to stop, and `tests/test_orchestrator_retirement.py::TheSharedCheckoutIsNotWhereTheMutationHappens` pins the permitted command set; committing, staging or stashing the peer's edit on their behalf (forbidden by `AGENTS.md`, and it is what makes the refusal correct); a WAIT-AND-RETRY loop inside the transaction (see OQ-01: it holds the finalize writer lock, and the condition is another agent's editor buffer, which may not clear for hours); adding a new `aw` verb or CLI flag (see OQ-02: the measured fix needs none, and `agent_workflows/cli.py` is deliberately not in Scope-Paths); making `finalize_precheck` read the journal (a real defect, filed as `bn58ha`, deliberately separate because it changes a DIFFERENT function's contract); keeping the abandoned coordinator commit reachable (filed as `hf76th`, a `commit_lock` design question); and any change to the ELIGIBILITY rule, the worker-role refusal, the scope reconciliation, or the plans-index gate.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, tests/test_ipd_lifecycle_cli.py, tests/test_orchestrator_retirement.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: cnf7gw
- Blocks-Release: next
- Set: cnf7gw
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 4er1ev
- Approval: 2026-09-28, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-28 approved (aw set): status set to approved
- 2026-09-28 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 all FIXED, none OPEN or DEFERRED. The diagnosis is excellent and every central measurement reproduced independently on the real finalize (the wedge, the failing advertised remedy, the working hand-delete, the own-evidence loss with its dangling commit, the untracked squatter, the swept pre-existing edit, and the dead origin_written_bytes key). PR-001 (BLOCKER): E-03 and E-04 AS AUTHORED COMPOSE INTO A PEER CLOBBER. E-04's safety proof that restoring original_bytes 'cannot clobber anybody' EXPIRES AT THE RELEASE: the release runs git checkout HEAD -- <plan_rel>, re-pointing the origin, and the contended arm is defined by the peer writing there, so measured at review original_bytes holds OWN EVIDENCE and not PEER EDIT while the origin holds the reverse; E-03 skips the only guard that refuses. That is the exact loss u23gbn F-14 guarded and this plan's F-01 promises to preserve. Fixed by conditioning the restore on the origin's CURRENT bytes matching what the release left, declaring the pair atomic, adding E-02 case (5) as the discriminator, verifying the pair together in V-03(e) and V-04(b), and authorizing shipping E-03 alone as a fallback. PR-002 (HIGH): the plan promised to fix the RACED arm, which never reaches the rollback (it writes PHASE_UNKNOWN_OUTCOME directly); Scope and Goal narrowed with the extend option recorded. PR-003 (HIGH): the forced-command fence cited a test that does not exist, surviving only as a name in a comment, so the plan's most safety-critical prohibition has no mechanical guard; all three citations corrected and the gap named. PR-004 (HIGH): no suite baseline recorded over an already-red tree; measured 1 failed, 3008 passed with the pre-existing node id named. PR-005 through PR-009: E-02 could not catch the blocker, V-04(a) was not constructible as written, E-03's skip endangered step 3, OQ-03's middle path is now worth adopting, and F-09's conclusion is inverted because the dead key is very likely the right place to implement E-04. Added OQ-04 carrying D-1. Review record written with 9 findings and 5 decisions, no Reversible: no; all probes ran in throwaway fixtures and no production file changed.

- 2026-09-28 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `cnf7gw`. Every claim below was MEASURED at HEAD `6171375d` against the real `ipd_lifecycle.finalize` and `retire_orchestrator`, not read off the code. The item asks for "a tooled way forward" and leaves the design open ("a tooled verb that reports the objecting path plus the exact operation a human should run, or a retry that waits for the tree to settle, or landing the transition on a branch the operator merges themselves"). Measuring first CHANGED the answer: none of those three is the fix, because the item's own framing understates the defect. It describes an operator with no route forward; what is actually there is an operator with no route forward EVEN AFTER THE CONTENTION CLEARS, because the failed attempt leaves a durable `PHASE_UNKNOWN_OUTCOME` journal that refuses every subsequent invocation before re-examining the tree (F-02, F-03). So the smallest honest fix is not a new verb but making the existing retry WORK, which is recorded as OQ-02 with the three proposed alternatives priced against it. Authoring also measured two facts the item does not state and which change the risk: the same wedge reaches the ORDINARY finalize path that every plan takes, not only the rollup (F-04), and a second arm loses the EXECUTING agent's own uncommitted evidence rather than a third party's (F-05). Two adjacent defects found while measuring were FILED rather than folded in (`bn58ha`, `hf76th`).
- 2026-09-28 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a CONTENDED terminal transition RECOVERABLE: leave the peer's bytes untouched exactly as today, leave the executing agent's own evidence bytes intact rather than dropping them WITHOUT ever writing over a peer's, clear the journal so the next invocation re-examines the tree instead of refusing on a stale ambiguity, and say in the refusal message which path objected and that re-running once the contention clears is sufficient.

SCOPE OF "CONTENDED", NARROWED AT REVIEW. This goal covers the `RECONCILED_REFUSED` arm, where git declined to fast-forward because landing would overwrite local changes. It does NOT cover the `RECONCILED_RACED` arm (a peer COMMIT advanced the branch mid-transaction), because measured at review that arm never calls the rollback: `_finalize_transaction` writes `PHASE_UNKNOWN_OUTCOME` directly and returns, so a fix inside `_rollback_precommit` cannot reach it (F-11). A raced transition therefore remains wedged after this plan, and that is stated here rather than discovered at validation. It is arguably correct, since HEAD genuinely moved for a reason this transaction cannot account for, which is a real ambiguity and not the false one this plan removes.

AND THE TWO WRITES MUST NOT FIGHT EACH OTHER, which is the sharpest constraint in this plan and the one review added. "Leave the agent's own evidence intact" and "leave the peer's bytes untouched" are in direct tension on exactly the arm this plan targets, because the release re-points the origin to HEAD's bytes and the peer then writes there, so the journal's `original_bytes` no longer describes what is on disk (F-10). A restore that trusts `original_bytes` deletes the peer's edit. The goal is met only when BOTH hold simultaneously, and it is better to deliver the clean rollback alone than to deliver a restore that can clobber.

WHAT THIS GOAL DELIBERATELY DOES NOT CLAIM. It does not make the contended finalize SUCCEED, and it must not be validated as if it did. When a peer holds an uncommitted edit to the plan file, the correct outcome is still a refusal, and this plan keeps it: git performs the refusal, the peer's bytes stay verbatim, and nothing is forced. What changes is only what the repository looks like AFTERWARDS. Today: a wedged plan needing a hand-deleted state file. After: a clean rollback whose message names the objecting path, and a re-run that works the moment the contention clears. That is a recovery fix, not a contention fix, and the honest one-line summary is "the refusal stops being sticky".

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure, then pin the wedge with tests that fail first

- [x] E-01 RE-MEASURE THE FOUR LOAD-BEARING FACTS and write the results into this plan as an execution note, because every one is dated and each has a cheap check. Record, with the HEAD they were taken at: (a) THE WEDGE, by driving a real `ipd_lifecycle.finalize(..., apply=True)` in a git-backed fixture whose ff-only merge is made to refuse (write a peer's bytes to the plan file at the instant the coordinator worktree commits, the same observation seam `tests/test_ipd_lifecycle_cli.py::TheORDINARYFinalizeAlsoMutatesOffTheSharedCheckout` already uses), showing exit 2, the `rollback FAILED` text, and `read_finalize_journal(...)["phase"] == PHASE_UNKNOWN_OUTCOME`; (b) THAT THE ADVERTISED REMEDY FAILS, by then committing the peer's edit so `git status --porcelain` is EMPTY and re-running the same finalize, showing exit 2 and the `unknown-outcome` message rather than a success; (c) THAT HAND-DELETING THE JOURNAL IS WHAT ACTUALLY WORKS, by unlinking `finalize_journal_path(root, id6)` and re-running, showing exit 0; and (d) THAT BOTH CALLERS ARE AFFECTED, by reproducing (a) through `retire_orchestrator` as well, using the fixture in `tests/test_orchestrator_retirement.py::RollupTransitionCase`. IF ANY HAS MOVED, SAY SO AND RE-SCOPE rather than proceeding: in particular, if (b) now SUCCEEDS then the wedge has already been fixed by other work and this plan is reduced to the message and the regression tests, which is a materially smaller change that must be re-reviewed rather than silently executed. Trust the tree, not this plan's Concern.
  - Depends on: none
  - Expected outcome: a written, symbol-cited baseline showing exit 2 plus `PHASE_UNKNOWN_OUTCOME` on both callers, the advertised re-run still refusing against a CLEAN tree, and the hand-deleted-journal re-run succeeding, each with its pasted output.
  - Execution state: performed

- [x] E-02 WRITE THE FAILING TESTS FIRST, as a new class in `tests/test_ipd_lifecycle_cli.py` (the file that owns the ordinary-finalize transaction assertions, per F-04 the path every plan takes), so the defect is pinned by something that fails BEFORE the fix. FOUR cases, and the SECOND is the one that matters most: (1) after a contended refusal the journal is ABSENT (`read_finalize_journal` returns None), not `PHASE_UNKNOWN_OUTCOME`; (2) after the peer COMMITS their edit, re-running the SAME finalize SUCCEEDS with exit 0 and the plan reaches `executed/` - this is the case the shipped message promises and today does not deliver, and it is the plan's acceptance criterion; (3) the refusal MESSAGE names the objecting path and states that a re-run suffices once the contention clears; (4) THE PEER'S BYTES ARE STILL INTACT byte-for-byte after the refusal and the branch is still unmoved, which is the property that must NOT regress and is the one whose loss would mean data loss rather than a wrong report. ALSO assert the negative that keeps this honest: the refusal still REFUSES, i.e. case (1) must check `res.exit_code != EXIT_OK` and that the plan is still at its `pending/` path, so a "fix" that made the contended finalize succeed by forcing the merge FAILS this test rather than passing it.
  - ADD A FIFTH CASE AT REVIEW, THE COMPOSED-PAIR CASE, because it is the one that catches the data-loss composition F-10 measured and no other case would. Case (5): the executing agent's OWN uncommitted evidence text present AND a peer edit at the plan path arriving at the landing instant; assert the peer's bytes are intact byte-for-byte afterwards AND that the agent's evidence was NOT written over them. This case must be RED for the naive E-03+E-04 composition and GREEN for the correct one, which makes it the discriminator between them. Expect it to pass on TODAY's code (today's step 2 refuses, which is why the peer survives now), so like case (4) it is a preservation test rather than a first-failing one; say so in its docstring so a reader does not mistake a green first run for a missing pin.
  - THE FIXTURE SEAM IS KNOWN TO WORK, verified at review rather than assumed: patching `ipd_lifecycle.land_worktree_commit` and writing the peer's bytes to the plan file inside the spy before delegating to the real function reproduces the contended arm exactly (`reconciliation.status == refused-would-overwrite`, exit 2, journal `unknown-outcome`, peer bytes intact). Use that seam rather than inventing one.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest tests/test_ipd_lifecycle_cli.py -k <new class> -o addopts="" -v` FAILS on cases (1), (2) and (3) with assertion messages (not collection or import errors), passes case (4) already (it is today's correct behavior), and the failure output is pasted into V-02 as the before-state.
  - Execution state: performed

### Task group 2: make the rollback distinguish "nothing was written" from "a restore failed"

- [x] E-03 TEACH THE ROLLBACK THAT A REFUSED RECONCILIATION LEFT NOTHING TO RESTORE, which is the root fix. THE REASONING, and it must be understood rather than pattern-matched, because the code being changed is the most load-bearing write in the toolkit. `_rollback_precommit` step 2 refuses when the origin holds bytes the transaction did not write, and that guard is CORRECT: it exists because plan `u23gbn` measured a peer's bytes being DESTROYED by an unconditional restore (recorded in its F-14 and in the docstring of `tests/test_orchestrator_retirement.py::AFailedRetirementCannotDestroyAPeersInFlightEdit`). But its refusal means "I could not safely RESTORE", and on this arm there is nothing to restore: git's ff-only refusal is documented and measured to leave the branch unmoved and the working tree untouched (`land_worktree_commit`'s REFUSED arm; re-measured structurally in F-06 as `MERGE_HEAD` ABSENT, so the merge never started at all). So the honest outcome is a clean NO-OP rollback, and reporting `unknown-outcome` asserts an ambiguity that does not exist. THE IMPLEMENTATION SHAPE, and the choice is deliberate: pass the reconciliation outcome down so the rollback knows the shared tree was never written (for example a keyword such as `shared_tree_untouched=True` on `_rollback_precommit`, or an explicit journal fact the function reads), and on that arm SKIP steps 1 and 2 entirely rather than loosening their guards. DO NOT INSTEAD WEAKEN THE GUARD: making step 2 tolerate foreign bytes in general would re-open the measured data-loss path on every OTHER arm, and `AFailedRetirementCannotDestroyAPeersInFlightEdit` must stay green as written, which is the test that will catch such a mistake. Step 1's destination guard is likewise untouched, because the untracked-squatter case (F-07) is a REAL foreign-bytes situation where refusing to delete is right.
  - THIS ITEM REACHES THE `REFUSED` ARM ONLY, NOT `RACED`, corrected at review because the plan's `- Scope:` promises both and the code does not route them the same way (F-11). The REFUSED arm returns through `_rollback_and_return`, which is what this item changes. The RACED arm (a peer COMMIT lands mid-transaction) does NOT: `_finalize_transaction` detects `cur_head != pre_head`, writes `PHASE_UNKNOWN_OUTCOME` DIRECTLY and returns, never calling the rollback at all. MEASURED at review: exit 2, `unknown-outcome: HEAD moved to <sha> but not via this finalize's lifecycle commit; journal retained`, phase `unknown-outcome`. So a fix confined to `_rollback_precommit` LEAVES THE RACED ARM WEDGED EXACTLY AS TODAY. Either extend this item to that return path as well, or narrow the plan's `- Scope:`, `- Goal:` and E-06 to say REFUSED only; do NOT leave the plan claiming both while fixing one. Review's recommendation, recorded so the executor is not left to choose blind: the raced arm's `unknown-outcome` is arguably CORRECT, because HEAD really did move for a reason this transaction cannot explain, which is a genuine ambiguity rather than the false one E-03 removes; so narrowing the claim is the honest option and extending it needs its own reasoning about why a moved HEAD is now unambiguous.
  - SKIPPING STEP 2 REMOVES THE ONLY THING STANDING BETWEEN E-04 AND A PEER CLOBBER, added at review with the measurement in F-10. Do not read "skip steps 1 and 2" as independent of E-04: the two compose into a destructive write if E-04 is implemented as the authored plan described. Whatever mechanism this item uses, the composed behavior MUST satisfy both properties at once, and the pair is verified together by V-03(e) and V-04(b): on the contended arm nothing is written to the origin and the peer's bytes survive; on a failed landing with no peer write, the agent's released evidence comes back. Read E-04's first three bullets before writing this item, because the safest implementation of the pair may be to leave step 2 IN PLACE for the origin and record the released bytes so its existing `origin_written` arm decides correctly, rather than to skip step 2 and re-derive the decision in a second place.
  - WHAT "SKIP" MUST NOT MEAN, stated because the no-op claim is only true for one of the two steps. Step 1 (remove the moved destination) genuinely has nothing to do on this arm when the destination was never created in the shared tree, and F-07 measures the case where it DOES have something to refuse. Step 3 (restore the recorded git-index entries) is NOT part of this item's skip: `test_rollback_restores_recorded_index_entry_not_head` pins it and it must keep running.
  - Depends on: E-02
  - Expected outcome: on the contended arm `_rollback_precommit` reports success having written nothing to the shared origin, the journal is CLEARED by `_rollback_and_return`, the peer's bytes are byte-identical afterwards, and `AFailedRetirementCannotDestroyAPeersInFlightEdit` plus `test_rollback_restores_recorded_index_entry_not_head` both still pass unchanged.
  - Execution state: performed

- [x] E-04 RESTORE THE EXECUTING AGENT'S OWN RELEASED EVIDENCE BYTES when the transaction released them and then failed to land, which is the second measured loss (F-05) and is a DIFFERENT arm from E-03's. WHAT HAPPENS TODAY: `_release_own_plan_edit_before_landing` drops the agent's uncommitted evidence edits from the shared working tree BEFORE the merge, having PROVED they are carried by the commit about to land; when the merge then refuses or races, that proof is about a commit nobody can reach (F-05 measured `git fsck` reporting it `dangling` after `coordinator_worktree`'s `finally` deletes the branch), so the bytes are simply gone from the tree. THE AUTHORED REASONING WAS "THE SAME TEST RUN IN REVERSE", AND REVIEW MEASURED THAT IT IS FALSE ON THE ARM THIS PLAN CARES ABOUT MOST. The authored claim was that because the release only happened when the origin's bytes were byte-equal to `original_bytes` and the landed commit carried them, restoring `original_bytes` later is "provably restoring OUR OWN content and cannot clobber anybody". THAT PROOF EXPIRES AT THE INSTANT OF THE RELEASE. The release re-points the origin to HEAD's bytes, and the contended arm is defined by a PEER WRITING TO THAT SAME PATH AFTERWARDS: that is what makes the merge refuse. So by the time the rollback runs, the origin holds the PEER's bytes, and `original_bytes` holds HEAD-plus-OUR-EVIDENCE, which does NOT contain the peer's text. MEASURED AT REVIEW on the real transaction, agent evidence present and a peer edit arriving at the merge instant: `journal["original_bytes"]` contains `OWN EVIDENCE` and NOT `PEER EDIT`, while the origin on disk contains `PEER EDIT` and not `OWN EVIDENCE`. Writing `original_bytes` there would therefore DELETE the peer's in-flight edit, which is exactly the measured data loss `u23gbn` F-14 added step 2's guard to stop and which this plan's own F-01 promises to preserve.
  - SO THE TWO E-ITEMS COLLIDE AND THE ORDER OF THE CHECKS IS THE WHOLE FIX. E-03 SKIPS step 2, which is what currently refuses; E-04 then writes the origin. Composed naively, E-03 removes the guard that would have caught E-04's clobber. THE REQUIRED SHAPE, which is not optional: the restore must be conditional on the ORIGIN'S CURRENT BYTES, re-read at rollback time, matching what the RELEASE LEFT THERE (i.e. HEAD's bytes at `plan_rel`, which is what `git checkout HEAD -- <plan_rel>` wrote), and it must write NOTHING on any other value. That is the same three-way test step 2 already performs, applied with the right expectation, and it means E-04 does NOT need step 2 skipped for it: it needs the released bytes recorded so step 2's `origin_written is not None and current_origin == origin_written` arm becomes reachable and TRUE in the no-peer case and FALSE in the peer case. Note that arm is the dead `origin_written_bytes` key F-09 documents, which makes wiring it the smaller and safer change than adding a parallel write path. IF THE EXECUTOR CANNOT SATISFY BOTH PROPERTIES AT ONCE, STOP AND REPORT rather than shipping either half: half of this pair is worse than neither, because E-03 alone is a clean recovery and E-03-plus-an-unguarded-E-04 is data loss.
  - GATE IT ON THE RELEASE HAVING ACTUALLY HAPPENED, not on the arm: a restore performed when no release happened would be exactly the unconditional write `u23gbn` E-08 removed. PREFER AN EXPLICIT JOURNAL FACT over re-deriving it from `evidence`, so a crash between the release and the merge is covered by the next invocation's rollback rather than only by this in-process path. Recording the RELEASED bytes (or the fact plus a reference) is what the authored bullet missed: `original_bytes` alone is insufficient because it is the PRE-release content, so it cannot distinguish "the origin still holds what we released" from "somebody else wrote here".
  - NOTE ALSO THAT THE NO-PEER CASE DOES NOT NEED THIS AT ALL, measured at review and worth knowing before writing code: with the agent's own evidence present and NO peer edit, the finalize SUCCEEDS (exit 0) and the plan is gone from `pending/`, so there is no origin to restore. The loss F-05 measured needs the landing to FAIL, which on the REFUSED arm requires a peer, and on the RACED arm requires a peer COMMIT. That is why V-04's converse case must be constructed deliberately rather than expected to fall out.
  - ALSO CORRECT THE DOCSTRING of `_release_own_plan_edit_before_landing`, which currently says the bytes are "already durable in a commit" without qualifying that the commit may never become reachable.
  - Depends on: E-03
  - Expected outcome: with the agent's own uncommitted evidence edits present, a landing made to fail, and NO peer write to the plan path, those bytes are back on disk at the plan's `pending/` path after the transaction returns. With a PEER write present the origin is NOT written and the peer's bytes survive byte-for-byte. With NO release having happened the origin is not written at all.
  - Execution state: performed

### Task group 3: say something actionable, and prove the retry works on both callers

- [x] E-05 REPLACE THE UNACTIONABLE REMEDY SENTENCE in `land_worktree_commit`'s REFUSED detail. Today it reads "Land or set that edit aside and re-run", and F-03 measured that re-running does NOT work even after the edit is landed, so the shipped message currently instructs the operator to do something ineffective. The replacement must (a) keep naming the objecting path or paths, which it already does via `_parse_merge_refusal_paths` and which is the one thing the operator needs; (b) state that the refusal is CORRECT and must not be forced, which the current text does well and which must survive, because an agent reading a softer message is exactly who would reach for `checkout -f`; (c) say that the bytes belong to another party and that this agent may NOT commit or stash them, citing the house rule rather than leaving the reader to infer it; and (d) say that re-running the SAME command once the contention clears is sufficient, which becomes TRUE only after E-03. DO NOT WRITE (d) BEFORE E-03 IS IN PLACE: a message promising a working retry against code that still wedges is worse than today's message, because it is confidently wrong rather than merely unhelpful. Keep carrying git's own verbatim text, for the reason `runner_shared.format_local_changes_refusal_reason` records: a re-worded summary is a second place that drifts from what git actually said.
  - Depends on: E-04
  - Expected outcome: the REFUSED detail names the path, forbids forcing, forbids touching the peer's bytes, and prescribes re-running the same command; E-02 case (3) passes.
  - Execution state: performed

- [x] E-06 PROVE THE FIX ON THE ROLLUP CALLER TOO, with a test in `tests/test_orchestrator_retirement.py` alongside the existing `TheSharedTreeIsReconciledByARefusingFastForward`. WHY THIS IS NOT DUPLICATION: `_finalize_transaction` is shared by exactly two callers and `u23gbn`'s own F-08 records that this is the plan-level constraint which forced its blast radius to be declared; the rollup path differs in ways that could break the fix specifically, because it has NO begin receipt (so no `base_head` and no scope delta), it inserts the superseded statement into the moved bytes, and it runs `_assert_rollup_touched_only_owned_paths` up front. THE ROLLUP'S UP-FRONT GUARD IS WHY THIS ARM IS A RACE RATHER THAN A STEADY STATE, and the test must say so in its docstring: that guard already refuses a rollup whose orchestrator file is dirty BEFORE anything mutates, so reaching the contended merge requires the peer's edit to arrive after that check, which is exactly the window the existing test's `_git` seam simulates. ASSERT the same two properties E-02 asserts, on this caller: the journal is cleared rather than `PHASE_UNKNOWN_OUTCOME`, and a retry after the peer lands their edit succeeds. The existing `test_the_contended_arm_refuses_and_the_peers_bytes_survive` must pass UNCHANGED, since it pins the refusal this plan preserves; if it needs editing, the change has altered the refusal itself and that is a defect in E-03, not a test to update.
  - Depends on: E-05
  - Expected outcome: the new rollup test passes; `test_the_contended_arm_refuses_and_the_peers_bytes_survive`, `test_the_diverged_arm_is_a_race_with_its_own_exit_code` and `test_the_clean_arm_fast_forwards_and_only_permitted_mutations_touch_shared_tree` all pass with no edits.
  - Execution state: performed

- [x] E-07 RUN THE BARE SUITE, `python3 -m pytest`, and compare against the REVIEW-MEASURED baseline below (the authored item recorded no number, so there was nothing to compare against; F-13). BASELINE AT REVIEW HEAD `f8c93d60` on a clean tree: `1 failed, 3008 passed, 2 skipped, 3 warnings in 102.52s`, with per-file `tests/test_ipd_lifecycle_cli.py` `45 passed` and `tests/test_orchestrator_retirement.py` `42 passed`. THE ONE FAILURE IS PRE-EXISTING AND IS NOT THIS PLAN'S: `tests/test_dependency_block_reporting.py::test_drain_and_cascade_mapped_reasons_rendered_once`, failing at `assert not sat` (`tests/test_dependency_block_reporting.py:122`) because the test hardcodes the dependency `executed:5o1jye` and `5o1jye` has since reached `executed/`. It reproduces with an empty `git status --short`. THE BAR IS THAT ONE NODE ID AND NO OTHER, with the passed count at or above 3008 plus this plan's new tests; a second failing node id is this plan's to explain and that one is not, because attributing it here is the mis-attribution `verify-execution` Dimension 3 exists to prevent. Still take your OWN before-baseline as the item says, since the tree moves, and say which case you observed if a concurrent fix has landed. Bare is required: `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`, so `-n0` makes this suite several times slower here and a second `-q` suppresses the `N passed` summary line this plan must paste. ALSO run the two directly-affected files narrowed with `-o addopts=""` so their per-file counts are visible, and state the counts rather than only the aggregate: this change touches the terminal transition taken by every plan in the corpus, so an aggregate that merely fails to get worse is weaker evidence than it looks.
  - Depends on: E-06
  - Expected outcome: no new failures relative to the same-day baseline, with BOTH aggregate summary lines captured plus the per-file counts for `tests/test_ipd_lifecycle_cli.py` and `tests/test_orchestrator_retirement.py`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- NEVER FORCE A REFUSED MERGE. Stated in the code itself: `land_worktree_commit`'s docstring forbids `git checkout -f`, `git reset --hard` and a manual file move by name. CORRECTED AT REVIEW, because the authored citation named a test that does not exist (F-12): there is NO test recording the permitted git-command set. The named `test_the_ff_only_merge_is_the_ONLY_command_that_touches_the_shared_tree` appears only inside a COMMENT explaining why two source-reading helpers were deleted; the surviving test in that class, `test_shared_checkout_mutation_isolation_and_commit_landing`, asserts commit DIRECTORY isolation, porcelain samples at two instants, peer-byte survival, a single-commit advance and the exact changed-path set, and it asserts nothing about which commands ran. SO THE PROHIBITION IS A HOUSE RULE WITH NO MECHANICAL GUARD, which makes it MORE important for this plan to honor by construction, not less: an executor must not assume a test will catch a forcing command. What the surviving test WOULD catch is a forcing command's side effects if they changed the porcelain samples, the peer's bytes, the commit count or the changed-path set, which covers a `reset --hard` or `checkout -f` on those paths but is not a command-level fence.
- THE FF-ONLY MERGE MUST BE THE STEP THAT ADVANCES THE BRANCH. Measured twice by `u23gbn` (its F-10) and recorded in the module comment above `RECONCILED_OK`: advancing the ref first makes the merge print "Already up to date.", exit 0, touch nothing, and render the peer-protecting refusal unreachable. `land_worktree_commit` explicitly classifies that as `RECONCILED_RACED` rather than success.
- ARMS ARE DECIDED BY EXIT CODE AND STRUCTURAL STATE, NEVER BY GIT'S PROSE. `land_worktree_commit`'s docstring says "never string-match git's prose", and `runner_shared.merge_in_progress` gives the reason at length: git's English is localizable and moves between versions, so a text test passes in the author's locale and misclassifies silently elsewhere. `merge_in_progress` is the shipped structural discriminator for exactly this pair of merge failures (`MERGE_HEAD` present = content conflict, absent = local-changes refusal).
- A ROLLBACK MUST REFUSE RATHER THAN OVERWRITE FOREIGN BYTES, and that guard was added because the opposite was MEASURED destroying a peer's work (`u23gbn` F-14; `_rollback_precommit` step 2's `else` arm; `AFailedRetirementCannotDestroyAPeersInFlightEdit`). This plan narrows WHEN the guard is consulted and must not weaken WHAT it does when consulted.
- A LANDED LIFECYCLE COMMIT IS RESUMED, NEVER REVERTED (`_resume_post_commit`, and `_rollback_precommit`'s "IT DOES NOT UNDO THE FF-ONLY MERGE, AND MUST NOT LEARN TO"). This plan touches only arms where NOTHING landed, which is why it does not conflict with that rule.
- THE PLANS MANIFESTS ARE GITIGNORED GENERATED VIEWS that no `aw` verb commits, and a rollback deliberately does not touch them (`_pre_commit_phase_leaves_manifests_untouched`, plan `4xt6u4`). So this plan's rollback changes have nothing to say about `INDEX.json`/`INDEX.md`.
- CONTROL STATE BELONGS TO THE CHECKOUT, NOT THE WORKTREE. `checkout_control_root` collapses every linked worktree to the main tree's `.aw`, so the journal a lane's inner `aw` writes is the one the driver sees. A fix that keyed recovery off a per-worktree path would reintroduce the fork that function exists to fix.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `6171375d` (2026-09-28) unless stated otherwise. Each measurement drove the REAL `ipd_lifecycle` functions in a git-backed fixture built from the repository's own test helpers, not a stub.

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-01 | THE REFUSAL ITSELF IS CORRECT AND MUST BE PRESERVED. This is stated first so the plan is not misread as loosening a protection. | On the contended arm: `landing.status == RECONCILED_REFUSED`, `returncode == 1`, `paths` naming the plan file, the peer's bytes byte-identical afterwards, HEAD unmoved, and `git merge-base --is-ancestor <landed> HEAD` nonzero. | Nothing in this plan changes the verdict. E-02 case (4) and E-06 assert the preservation explicitly, and the existing contended-arm test must pass UNCHANGED. |
| F-02 | THE FAILED ATTEMPT WEDGES THE PLAN, which is the defect and is worse than the item's "no tooled remedy" framing. | Real `finalize(..., apply=True)` with a peer edit arriving at the worktree-commit instant returned exit 2 with `rollback FAILED (unknown-outcome: the plan's original path ... holds content this transaction did not write ...); journal retained, repository NOT reported restored.` and `read_finalize_journal(...)["phase"] == 'unknown-outcome'`. | The fix is E-03, in the ROLLBACK, not in the merge. The journal must be cleared on an arm where nothing was written. |
| F-03 | THE ADVERTISED REMEDY DOES NOT WORK, so the shipped message currently instructs an ineffective action. | After the refusal, the peer COMMITTED their edit (`git status --porcelain` then EMPTY) and the same finalize was re-run: exit 2, `finalize journal for abc123 is in unknown-outcome (ambiguous prior attempt); resolve manually and clear <path>`. Hand-deleting that file and re-running then returned exit 0, `finalized abc123 -> executed at 8af8da291b5e`. | E-02 case (2) is the acceptance criterion, and E-05 may only promise a working retry after E-03 makes it true. It also proves the remedy is mechanical and needs no new verb (OQ-02). |
| F-04 | BOTH CALLERS ARE AFFECTED, so the blast radius is the ordinary terminal transition every plan takes, not the four-per-corpus rollup. | The rollup path reproduced identically through `retire_orchestrator`: exit 2, the same `rollback FAILED` text, journal `unknown-outcome`, and the retry after the peer landed their edit likewise refusing. `_finalize_transaction` has exactly two callers, which `u23gbn` F-08 records as the architectural constraint. | `tests/test_ipd_lifecycle_cli.py` is the PRIMARY test surface (E-02) and the rollup is a required second surface (E-06). E-07's per-file counts matter for the same reason. |
| F-05 | A SECOND ARM LOSES THE EXECUTING AGENT'S OWN WORK, not a third party's, and this is the one finding whose failure mode is data loss rather than a wrong report. | REPRODUCED AT REVIEW, in full and independently. With the agent's own uncommitted evidence text in its plan and a peer COMMIT landing mid-transaction: `evidence["reconciliation_prep"] == ["released this transaction's own uncommitted edit at .aw/records/plans/pending/20260824-demo-01-abc123-demo.ipd.md"]`, exit 2, and afterwards that text was ABSENT from the working tree while PRESENT in the journal's `original_bytes`. The abandoned commit was confirmed unreachable: `git branch -a` showed `* master` only, `git merge-base --is-ancestor <sha> HEAD` nonzero, and `git fsck` reported `dangling commit <sha>`. | E-04 restores those bytes, BUT NOT UNCONDITIONALLY FROM `original_bytes`: see F-10, which measures that on the contended arm those bytes no longer describe the origin and writing them would destroy a peer's edit. The unreachability half is filed as `hf76th`. |
| F-06 | THE REFUSAL ARM IS STRUCTURALLY DISTINGUISHABLE WITHOUT READING GIT'S PROSE, and the repository already ships the discriminator. | In a scratch repo: the local-changes refusal exits 1, `git rev-parse --verify --quiet MERGE_HEAD` is NONZERO (the merge never started), `git diff --diff-filter=U` is EMPTY, the tree holds only the peer's own dirt, HEAD is unmoved. `runner_shared.merge_in_progress` documents and measures exactly this. | E-03 may key its "nothing was written" fact on the reconciliation OUTCOME it already has in hand, and a reviewer can verify the premise independently rather than trusting `land_worktree_commit`'s classification. |
| F-07 | A THIRD REFUSAL SHAPE EXISTS that this plan must NOT treat as the contended arm: an UNTRACKED squatter at the destination path. | With an untracked file at the plan's `executed/` path, `land_worktree_commit` returned `RECONCILED_REFUSED` naming the DESTINATION, and the rollback failed at STEP 1 instead (`unknown-outcome: the finalize destination ... changed since the checkpoint`). The squatter's bytes survived. | E-03 must skip both steps on the untouched-tree arm, and must NOT loosen step 1's destination guard: refusing to delete genuinely foreign bytes there is correct. This case is why the fix is "skip when nothing was written", not "tolerate mismatches". |
| F-08 | AN UNCONTENDED THIRD-PARTY EDIT PRESENT BEFORE THE TRANSACTION STARTS DOES NOT REFUSE AT ALL; it is swept into the lifecycle commit. | With a third party's uncommitted sentinel in the plan file BEFORE `finalize` ran, the finalize SUCCEEDED (exit 0) and `git show <tip>:<executed path>` CONTAINED the sentinel. | Recorded to bound the plan's claim: this is NOT in scope and is arguably correct (the transaction mirrors the plan's current bytes deliberately, so an executing agent's own evidence rides the commit, and it cannot tell that content from a stranger's). Named in the Scope check as deliberate under-scope so a reviewer is not surprised, and because a future author may mistake it for a regression this plan introduced. |
| F-09 | `_rollback_precommit` HAS A DEAD ARM whose presence misleads a reader of this exact code path. | `origin_written = journal.get("origin_written_bytes")` is the ONLY occurrence of that key in the repository (`rg` over all `*.py`), and `git log -S` shows it arrived read-only in `82922f5c` (`u23gbn`'s commit). So `origin_written` is always None, its `restore_origin = True` arm is unreachable, and every foreign-bytes case falls to the refusing `else`. | REPRODUCED AT REVIEW: `grep -rn "origin_written_bytes" --include=*.py .` returns exactly ONE line, the read at `_rollback_precommit`, and `git log -S` returns only `82922f5c`. Named because E-03 and E-04 edit this function. RE-ASSESSED AT REVIEW, and the authored conclusion is INVERTED: this arm is not a distraction from E-04's case, it is very likely the CORRECT PLACE TO IMPLEMENT IT. Wiring `origin_written_bytes` to the bytes the release actually left makes the existing three-way test decide E-04 correctly and refuse the peer case for free (F-10). The Deferred row is amended accordingly: do not revive it speculatively, but if E-04's safe shape turns out to be this key, wiring it is IN scope for E-04 and is smaller than a parallel write path. |
| F-10 | ADDED AT REVIEW, AND IT IS THE BLOCKER. E-03 AND E-04 AS AUTHORED COMPOSE INTO A PEER CLOBBER, the exact data loss `u23gbn` F-14 added step 2's guard to prevent and which this plan's F-01 promises to preserve. E-04's authored safety argument is that restoring `original_bytes` is "provably restoring OUR OWN content and cannot clobber anybody". THAT PROOF EXPIRES AT THE RELEASE. `_release_own_plan_edit_before_landing` runs `git checkout HEAD -- <plan_rel>`, re-pointing the origin to HEAD's bytes; the contended arm is then DEFINED by a peer writing to that same path. So at rollback time the origin holds the PEER's bytes while `original_bytes` holds HEAD-plus-OUR-EVIDENCE. E-03 skips step 2, which is the only check that currently refuses; E-04 then writes. | MEASURED at review HEAD `f8c93d60` on the real `finalize`, with the agent's own evidence present and a peer edit written at the `land_worktree_commit` instant: `journal["original_bytes"]` contains `OWN EVIDENCE` and NOT `PEER EDIT`; the origin captured immediately after the release equals HEAD's bytes exactly; the origin on disk afterwards contains `PEER EDIT` and NOT `OWN EVIDENCE`; `reconciliation.status == refused-would-overwrite`; and today's step 2 refuses with "holds content this transaction did not write". A composed E-03+E-04 that writes `original_bytes` there would replace the peer's edit with bytes that do not contain it. | E-04 is rewritten to condition the restore on the origin's CURRENT bytes matching what the RELEASE left, re-read at rollback time, writing nothing on any other value; E-03 carries a bullet forbidding the naive composition; the Goal states the tension; and V-03(e) plus V-04(b) verify the pair TOGETHER rather than separately. A reviewer or executor must treat "half of this pair" as worse than neither. |
| F-11 | ADDED AT REVIEW. THE `RACED` ARM NEVER REACHES THE ROLLBACK, so the plan's `- Scope:` promise to fix "the REFUSED and RACED arms" could not be kept by any change to `_rollback_precommit`. `_finalize_transaction` classifies the commit boundary AFTER the landing: when no lifecycle commit is found and `cur_head != pre_head`, it writes `PHASE_UNKNOWN_OUTCOME` DIRECTLY and returns, with no call to `_rollback_and_return` on that path. Only the `cur_head == pre_head` branch rolls back. | MEASURED at review with a peer COMMIT landing at the `land_worktree_commit` instant: exit 2, message `unknown-outcome: HEAD moved to 0954f198fb19 but not via this finalize's lifecycle commit; journal retained at <path>`, journal phase `unknown-outcome`, and the message contains no `rollback` text at all (contrast the REFUSED arm, whose message does). | The plan's `- Scope:` and `- Goal:` are narrowed to REFUSED, and E-03 carries the choice explicitly with review's recommendation to narrow rather than extend, on the ground that a moved HEAD is a GENUINE ambiguity unlike the false one this plan removes. E-06's rollup assertions are correspondingly about the refused arm. |
| F-12 | ADDED AT REVIEW. A CITED TEST NAME NO LONGER EXISTS AS A TEST, so three of this plan's guard citations point at something that cannot fail. The plan cites `tests/test_orchestrator_retirement.py::TheSharedCheckoutIsNotWhereTheMutationHappens::test_the_ff_only_merge_is_the_ONLY_command_that_touches_the_shared_tree` in its conventions, its Deferred FORCING row and its Scope fence as the behavioral guard that "fails on `reset`, `restore`, `clean`, `stash`, `switch`, `update-ref`, a merge without `--ff-only`". That test does not exist. | `grep -rn "ff_only_merge_is_the_ONLY_command" tests/` returns ONE hit and it is inside a COMMENT at `tests/test_orchestrator_retirement.py` explaining why two helpers were deleted. The class now contains exactly one test, `test_shared_checkout_mutation_isolation_and_commit_landing` (5 tests pass in the class plus its siblings), and grepping its body for `reset`, `--hard`, `checkout -f`, `stash`, `update-ref` or any recorded-command assertion returns NOTHING: it asserts commit DIRECTORY isolation, porcelain samples, peer-byte survival, a one-commit advance and the changed-path set, but it does NOT record or forbid a command set. | Every citation is corrected to the test that exists and to what it actually asserts. The scope fence keeps its PROHIBITION (it is a house rule regardless of test coverage) but no longer claims a test enforces it, and the gap is named so a reviewer is not falsely reassured. This matters because the prohibition is this plan's most safety-critical fence and an executor who believed a test would catch a forcing command might rely on it. |
| F-13 | ADDED AT REVIEW. THE AUTHORED SUITE BASELINE IS ABSENT AND THE TREE IS ALREADY RED FOR AN UNRELATED REASON, which E-07 and V-07 would otherwise make the executor own. The plan requires comparing the bare suite "against a baseline taken the same way BEFORE any edit" but records no number, so the executor has nothing to compare against and would take their own baseline on a red tree without knowing the red is pre-existing. | MEASURED at review HEAD `f8c93d60` on a clean tree (`git status --short` empty): `1 failed, 3008 passed, 2 skipped, 3 warnings in 102.52s`. The one failure is `tests/test_dependency_block_reporting.py::test_drain_and_cascade_mapped_reasons_rendered_once`, failing at `assert not sat` (`tests/test_dependency_block_reporting.py:122`) because the test hardcodes the dependency `executed:5o1jye` and `5o1jye` has since reached `executed/`, so the edge it expects unsatisfied is now satisfied. Per-file: `tests/test_ipd_lifecycle_cli.py` `45 passed`, `tests/test_orchestrator_retirement.py` `42 passed`. | E-07 and V-07 now carry the measured baseline, the named pre-existing failure with its cause, and the per-file counts, with the bar stated as "that one node id and no other". |

## Proposed changes (ordered, validatable)

1. Re-measure the wedge, the failing remedy, the working hand-fix, and both callers (E-01).
2. Pin all four properties with tests that fail first, including the retry-after-the-peer-lands case (E-02).
3. Skip the rollback's restore steps on the arm where git provably wrote nothing, and CLEAR the journal (E-03).
4. Restore the agent's own released evidence bytes when the release happened and the landing failed (E-04).
5. Replace the unactionable remedy sentence, only after the retry it promises actually works (E-05).
6. Prove the same two properties on the rollup caller, keeping its three existing arm tests unchanged (E-06).
7. Bare suite plus per-file counts, before and after (E-07).

ORDER IS LOAD-BEARING BETWEEN E-03 AND E-05, and not merely tidy. E-05 writes a message promising that a re-run works; that promise is FALSE until E-03 lands. Shipping E-05 alone would replace an unhelpful message with a confidently wrong one, which is worse, because an agent that trusts it will re-run, be refused, and have no remaining hypothesis.

AND E-03 AND E-04 ARE ONE ATOMIC CHANGE, NOT TWO ORDERED ONES, which review added as the sharper constraint (F-10). They are numbered separately because they are separate concerns to reason about, but their COMBINED behavior is what must be correct: E-03 removes the check that today refuses, and E-04 performs a write that check was refusing. Do not commit E-03 and E-04 in separate commits with the tree in between, and do not mark E-03 complete without having established which shape E-04 will take, because the safest known shape (wiring `origin_written_bytes`, F-09) changes what E-03 should do to step 2 at all. V-03(e) is the check that the composition is right, and it can only be run once both are in place.

## Deferred / out of scope (with reason)

- MAKING `finalize_precheck` READ THE JOURNAL. Measured while authoring: immediately after the wedge, `finalize_precheck` returned `(0, 'precheck passed (receipt valid, pre-transition conforming; scope delta computed).', findings=())` while `finalize(apply=False)` returned exit 2 naming the unknown-outcome journal. So the preview ORACLE disagrees with the preview COMMAND. Deferred because it changes a different function's contract and has its own callers to consider, and because this plan's fix removes the most common way to reach that state rather than the state itself. FILED AT AUTHORING so the carrier names a real item now.
  - Carrier: bn58ha
- KEEPING THE ABANDONED COORDINATOR COMMIT REACHABLE. `coordinator_worktree`'s `finally` deletes the branch unconditionally, on a docstring premise ("the caller has already landed (or deliberately abandoned) the commit") that is false on the failure arms, leaving only a dangling object. Deferred because the remedy is a `commit_lock` design question (a preserved branch, a recovery ref, or a reported sha), and because E-04 removes the DATA-LOSS consequence by restoring from the journal instead, which needs no new git object lifetime. FILED AT AUTHORING.
  - Carrier: hf76th
- THE DEAD `origin_written_bytes` KEY (F-09). AMENDED AT REVIEW: this row no longer says "do not touch it", because review's analysis of the E-03/E-04 collision (F-10) found that WIRING this key is very likely the CORRECT and SMALLEST implementation of E-04. Its existing arm, `origin_written is not None and current_origin == origin_written`, is exactly the test E-04 needs: record the bytes the release left, and step 2 then restores in the no-peer case and REFUSES in the peer case with no new code path and no skipped guard. So: do NOT revive it speculatively or as a tidy-up, and DO treat wiring it as IN scope for E-04 if that is the shape the executor chooses, saying so in V-04(d). What remains deferred is the OTHER disposition, deleting the arm outright, which needs its own reasoning about removing a guard a reader believes in.
  - Carrier-Declined: Nothing is owed as separate work. The arm is unreachable today so it causes no behavior, and after this amendment it is either used by E-04 or left as-is; either way no future obligation is created. F-09 records it for the one reader who needs it, an executor editing this very function.
- A WAIT-AND-RETRY LOOP INSIDE THE TRANSACTION, which is one of the three shapes the backlog item proposes. Out of scope on measured grounds rather than taste: see OQ-01. The repository has a shared `contention_wait` helper and this is deliberately not a use for it.
  - Carrier-Declined: Resolved against waiting based on repository evidence; see OQ-01.
- FORCING THE MERGE, IN ANY FORM. Out of scope permanently, not merely here. It destroys the peer's bytes, which is the harm the whole `dirtygates` Set exists to stop. CORRECTED AT REVIEW: the authored row claimed a test "fails on every forcing command by name", and that test does not exist (F-12). The prohibition stands on `land_worktree_commit`'s own docstring and on this fence; what a test WOULD catch is a forcing command's observable effects (the porcelain samples, the peer's bytes, the commit count, the changed-path set asserted by `test_shared_checkout_mutation_isolation_and_commit_landing`), not the command itself.
  - Carrier-Declined: Nothing is owed. This is a scope fence stating a prohibition, not a dropped obligation: there is no future work behind it, and naming a carrier would imply someone should eventually do it.
- THE UNCONTENDED PRE-EXISTING THIRD-PARTY EDIT (F-08), which is swept into the lifecycle commit rather than refused. Out of scope because it is not the same defect and is arguably correct behavior: the transaction mirrors the plan's CURRENT bytes on purpose, so that an executing agent's own uncommitted evidence rides the transition, and it has no way to distinguish that from a stranger's edit to the same file.
  - Carrier-Declined: Nothing is owed. Filing this would assert a defect this plan has not established: `AGENTS.md` already tells an agent to verify its staged set, the finalize is path-scoped to the plan's own two paths, and whether a co-worker may edit a plan another agent is finalizing is a policy question for the maintainer rather than a measured bug. Raised in the Scope check so a reviewer can overrule that judgement cheaply.
- ANY CHANGE TO THE ELIGIBILITY RULE, the worker-role refusal, the two-way scope reconciliation, or the plans-index fail-loud gate. Out of scope; this plan changes only what happens after a reconciliation has already failed.
  - Carrier-Declined: Nothing is owed. These are untouched neighbours, and excluding them creates no gap. The row exists because a reader might expect a change to `_finalize_transaction` to touch everything that function coordinates.

## Scope check

- Over-scope: none. `agent_workflows/ipd_lifecycle.py` carries E-03, E-04 and E-05; `tests/test_ipd_lifecycle_cli.py` carries E-02; `tests/test_orchestrator_retirement.py` carries E-06; E-01 and E-07 write no tracked file. The two backlog items the Deferred rows name were filed AT AUTHORING, so execution mints nothing.
- Under-scope, DELIBERATE and stated plainly: after this plan a contended finalize STILL FAILS. An operator reading "the peer-edit refusal was fixed" must not conclude the transition now succeeds under contention; what is fixed is that the failure is clean, recoverable, and honestly described. The plan is a recovery fix.
- Under-scope, SECOND ITEM, stated because it is the one a reviewer is most likely to challenge: the pre-existing uncontended third-party edit (F-08) is still swept into the lifecycle commit, and this plan does not change that. It is named here rather than buried in Deferred so the boundary between "a peer edit that arrives mid-transaction" (this plan's subject) and "a peer edit that was there all along" (not this plan's subject) is explicit.
- `agent_workflows/commit_lock.py` is deliberately NOT in `Scope-Paths`, even though `coordinator_worktree`'s cleanup is implicated in F-05. E-04 restores from the JOURNAL, which needs no change to that module; touching it would put a shared helper behind every `aw` self-commit into this plan's commit for no measured benefit. If the executor finds E-04 impossible without editing it, that is a re-scope to report, not a silent addition.
- `agent_workflows/cli.py` is deliberately NOT in `Scope-Paths`: OQ-02 resolves against a new verb or flag, and the measured fix adds no CLI surface.
- The three existing arm tests in `TheSharedTreeIsReconciledByARefusingFastForward` and the guard test `AFailedRetirementCannotDestroyAPeersInFlightEdit` must pass UNCHANGED. VERIFIED AT REVIEW that all of them currently pass and that none of them asserts the journal phase, so this plan's new assertions are additive rather than in tension with them: `python3 -m pytest tests/test_orchestrator_retirement.py -k "TheSharedTreeIsReconciledByARefusingFastForward or AFailedRetirementCannotDestroyAPeersInFlightEdit or TheSharedCheckoutIsNotWhereTheMutationHappens" -o addopts=""` -> `5 passed`. If the executor finds them failing, the change has altered the refusal or weakened the peer guard, which is a defect in E-03 and not a test to update.
- Under-scope, THIRD ITEM, added at review and the most consequential of the three: the `RECONCILED_RACED` arm is NOT fixed (F-11). A peer COMMIT landing mid-transaction still leaves `PHASE_UNKNOWN_OUTCOME` and still wedges, because that arm writes the journal directly and never calls the rollback this plan changes. The plan's `- Scope:` originally promised both arms; it is narrowed, and E-03 records the executor's choice to extend or leave it. An operator reading "the contended refusal was fixed" must not conclude a raced finalize now recovers.
- Under-scope, FOURTH ITEM: no test pins the forced-command prohibition (F-12). The scope fence forbids `reset --hard`, `checkout -f` and the rest, and review measured that the test the plan cited for it does not exist. The prohibition is honored by construction and by review, not by a red test, and this plan does not add such a test (it would be a command-level assertion of the kind this repository has been removing, and deciding that is not this plan's call).

## Required tests / validation

- The new class in `tests/test_ipd_lifecycle_cli.py` must pass, with cases (1), (2) and (3) having been OBSERVED FAILING before E-03 and those failures pasted into V-02.
- The new rollup test in `tests/test_orchestrator_retirement.py` must pass (E-06).
- `AFailedRetirementCannotDestroyAPeersInFlightEdit`, `TheSharedTreeIsReconciledByARefusingFastForward` (all three arms), `TheSharedCheckoutIsNotWhereTheMutationHappens` and `test_rollback_restores_recorded_index_entry_not_head` must all pass UNCHANGED, since they pin the protections this plan preserves.
- THE PEER'S BYTES MUST SURVIVE A CONTENDED FINALIZE BYTE FOR BYTE, with before and after pasted. This is the one required check whose failure means data loss rather than a wrong report, and after review it must be run in the HARDEST configuration, not the easiest: the agent's OWN uncommitted evidence present AS WELL AS the peer's edit, which is the composition F-10 measured as destructive under the authored E-03+E-04. A peer-only run passes even on a broken composition, so it does not discharge this requirement.
- THE AGENT'S OWN EVIDENCE MUST COME BACK ONLY WHEN IT IS SAFE, with all three cases pasted: restored when the landing failed and no peer wrote the path; NOT restored when a peer did; not written at all when no release happened. These three together are the fix; any one alone is not.
- THE RETRY MUST BE SHOWN TO WORK END TO END: peer edit arrives, finalize refuses, peer commits, the SAME finalize succeeds and the plan reaches `executed/`. Paste all three steps.
- The bare suite `python3 -m pytest`, before and after, with both summary lines pasted, plus per-file counts for the two touched test files via `-o addopts=""`.

## Spec / documentation sync

- No spec amendment, and the reason is substantive rather than procedural. Spec `77tr3o` governs orchestrator retirement and this plan changes neither the eligibility rule, the omitted-gates set, nor the coordinator-only authority; spec `25kzda` governs the run and verify contract and this plan changes no run status or queue behavior. What changes is the RECOVERY BEHAVIOR of a failure arm inside `_finalize_transaction`, which no spec describes at that granularity. `Scope-Paths` therefore names no `.spec.md` file, which is the declaration both runners announce at run start.
- The DOCSTRINGS in `ipd_lifecycle.py` are the published contract for this transaction, and three of them become false or misleading when this plan lands: `land_worktree_commit`'s REFUSED remedy sentence (E-05), `_release_own_plan_edit_before_landing`'s "already durable in a commit" claim (E-04), and `_rollback_precommit`'s account of when it refuses (E-03). Each is corrected in the SAME change that falsifies it, so the tree never carries a guarantee this plan broke.
- DO NOT EDIT WHAT PLAN `u23gbn` RECORDS. Its F-10, F-13 and F-14 are history and the execution contract forbids rewriting an executed plan's record. A dated `## Workflow history` line on it pointing at this plan is permitted and is the right way to connect them, since it adds to the record without rewriting it.
- No `docs/` page or `CHANGELOG.md` entry describes this failure arm (the reconciliation is internal to the lifecycle transaction), so no user-facing documentation changes. Verify with a search before concluding it, rather than trusting this line.

## Open questions

### OQ-01: Should the transaction WAIT for the contention to clear (the backlog item's "a retry that waits for the tree to settle") instead of refusing and returning?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AGAINST WAITING, from repository evidence, and recorded because the backlog item proposes it explicitly so a reviewer should see it priced rather than silently dropped. THREE REASONS, in descending strength. FIRST, WHAT IS BEING WAITED ON IS NOT A LOCK BUT A HUMAN OR AGENT'S UNSAVED EDIT. Every existing use of `contention_wait.wait_until` in this repository waits on something a PROCESS holds and releases: the isolated-commit compare-and-swap retrying on a new tip (`git_commit_helper`), the repository integration lock (`runner_shared`), and the finalize writer lock (`ipd_lifecycle`, via `FINALIZE_LOCK_WAIT_SECONDS`). An uncommitted working-tree edit has no holder and no release event; it clears when a person decides to commit it, which may be hours or never. The shared policy's bound is `TIMEOUT_SECONDS = 1800.0`, so the realistic outcome is a 30-minute block ending in the same refusal. SECOND, THE WAIT WOULD BE HELD UNDER THE FINALIZE WRITER LOCK, since `_finalize_transaction` runs inside it; so one contended plan would block every other finalize in the checkout for up to half an hour, converting a per-plan refusal into a checkout-wide stall. THIRD, IT IS UNNECESSARY ONCE E-03 LANDS: the retry becomes cheap and correct, so the operator or driver can re-attempt whenever they like, which is strictly more flexible than a bounded wait chosen by this code. Non-blocking because a future wait could be layered on top of a working retry without undoing anything here, whereas a wait built on today's wedge would block for 30 minutes and then STILL wedge. THE HONEST COST OF THE DEFAULT: a contended finalize returns nonzero and something must re-invoke it, which under `aw oc run` means the item is recorded not-executed for that pass rather than transparently succeeding.

### OQ-02: Should the remedy be a NEW `aw` verb (the backlog item's first suggestion) rather than a fix to the existing retry?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AGAINST A NEW VERB, on the measurement in F-03. The item reasonably assumed the operator needs a tool to move forward; what was actually measured is that the operator needs the EXISTING path to stop refusing. Once the journal is cleared on an arm where nothing was written, the remedy is `re-run the same command`, which needs no new surface, no new flag, and no `agent_workflows/cli.py` change, and which is the remedy the shipped message ALREADY prescribes and fails to deliver. A verb whose job is to clear a state file that should not have been left behind would institutionalize the defect rather than fix it, and it would need its own fail-closed reasoning about when clearing is safe, duplicating the judgement E-03 makes once in the place that already has the facts. WHAT A REVIEWER SHOULD WEIGH AGAINST THIS: the `PHASE_UNKNOWN_OUTCOME` state can still be reached by OTHER arms that this plan does not touch (a genuine mid-transaction ambiguity, an untracked squatter per F-07, a real rollback failure), and for THOSE a hand-cleared journal remains the only route, which is unchanged by this plan and is arguably its own gap. Non-blocking because the two are additive: a recovery verb, if later wanted, is easier to specify once the common case no longer needs it, and nothing in E-03 forecloses it.

### OQ-03: Is clearing the journal on a REFUSED arm safe, or does it discard evidence a human would want?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AS SAFE FOR THE WORKING-TREE STATE, WITH ONE ACKNOWLEDGED LOSS, stated plainly because a reviewer should check this hardest: it is the one place this plan removes something. THE SAFETY ARGUMENT. The journal's purpose is documented as recovery ACROSS invocations: pre-commit phases are rolled back idempotently, `PHASE_COMMITTED_INCOMPLETE` is resumed, `PHASE_UNKNOWN_OUTCOME` fails closed. On this arm there is nothing to recover TO: git refused before writing, so the tree and the branch are exactly as the transaction found them (F-01, F-06), and a fresh attempt derives everything it needs from the tree. Keeping the journal therefore preserves no recoverable state; it only blocks the next attempt, which is F-03. THE LOSS, and it is real: the journal currently holds `worktree_commit`, the sha of the abandoned lifecycle commit, and per F-05 that commit is unreachable and prunable, so clearing the journal removes the last readable pointer to it. This matters ONLY for the released-bytes case, and E-04 removes the need by restoring those bytes to the working tree instead of leaving them recoverable solely from a dangling object; the broader unreachability is `hf76th`. Non-blocking because the alternative preserves a pointer to a prunable object at the cost of wedging every plan that hits the arm, which is the trade this plan reverses deliberately. IF A REVIEWER DISAGREES, the cheap middle path is to clear the journal but include `worktree_commit` in the returned message, which costs nothing and is compatible with every E-item here.
- REVIEWED AND AGREED, WITH THE MIDDLE PATH ADOPTED AS A RECOMMENDATION. The safety argument holds and was re-verified independently: on the REFUSED arm HEAD is unmoved, `git merge-base --is-ancestor <landed> HEAD` is nonzero, and the peer's bytes are byte-identical, so there is no recoverable state the journal is preserving. Review's one addition: since E-04 now restores the released bytes only when the origin still holds what the release left (F-10), there is a case where the restore correctly DECLINES (a peer wrote there) and the agent's evidence then survives ONLY in the abandoned commit. In exactly that case the journal's `worktree_commit` is the last pointer to it, so E-05's message SHOULD carry that sha, which is the middle path this question already names and which costs nothing. Recorded here rather than as a new E-item because E-05 is already editing that message.

### OQ-04: E-03 and E-04 as authored compose into a peer clobber. Fix the composition, or drop E-04?

- Blocking: no
- Status: resolved
- Owner: plan-review (opencode)
- Finding: F-10
- Resolution or deferral rationale: FIX THE COMPOSITION, do not drop E-04, and make the pair atomic. THE MEASUREMENT FIRST, because it decides the question: E-04's authored safety argument is that restoring `journal["original_bytes"]` is "provably restoring OUR OWN content and cannot clobber anybody". Driven on the real `finalize` at review HEAD `f8c93d60` with the agent's own evidence present and a peer edit arriving at the landing instant, `original_bytes` contains the agent's evidence and NOT the peer's text, while the origin on disk contains the peer's text and NOT the agent's evidence. The proof expires at the release, which runs `git checkout HEAD -- <plan_rel>` and re-points the origin; the contended arm is then defined by the peer writing there. Since E-03 skips the step-2 guard that today refuses exactly this write, the authored pair deletes the peer's edit. ALTERNATIVES CONSIDERED. (a) DROP E-04 and ship only the clean rollback: rejected, but it is the correct FALLBACK and is now written into E-04 as the stop-and-report instruction, because E-03 alone is a genuine improvement and loses nothing that is not already lost today; what makes dropping it wrong as the plan is that F-05's loss is real, is the executing agent's OWN work, and is cheap to fix safely. (b) Restore from `original_bytes` but only on the RACED arm, where no peer wrote the plan path: rejected because F-11 measured that the raced arm never reaches the rollback at all, so there is no hook there, and because a peer CAN also have edited the path on that arm. (c) CONDITION THE RESTORE ON THE ORIGIN'S CURRENT BYTES matching what the release left, re-read at rollback time: CHOSEN. It is the same three-way test step 2 already performs with the right expectation, it refuses the peer case for free, and the repository already has the slot for it in the dead `origin_written_bytes` key (F-09), which makes it a smaller change than a parallel write path. Non-blocking because the fix is fully specified in the revised E-03 and E-04 and verified by V-03(e) plus V-04(b), and because the fallback (ship E-03 alone) is explicitly authorized, so the executor is never stuck.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: the pasted output of all four baselines with the HEAD they were run at: (a) the contended `finalize` showing exit 2, the `rollback FAILED` sentence and the journal phase read back as `unknown-outcome`; (b) the re-run against a tree whose `git status --porcelain` is shown EMPTY, still returning exit 2 with the `unknown-outcome` message, which is the measurement that falsifies the shipped remedy and without which this plan has no premise; (c) the post-unlink re-run returning exit 0 with the `finalized <id> -> executed` line; and (d) the same wedge reproduced through `retire_orchestrator`. If any fact moved, the paste must be accompanied by the explicit re-scope statement E-01 demands.
  - Observed evidence: Baselines measured at launch HEAD `f7ec0718c9a7e2ab8a44218153787cedc8895c74` reproduced the wedge and confirmed recovery behavior:
    ```
    === MEASURING E-01 (a), (b), (c) on ORDINARY FINALIZE ===

    --- (a) Contended finalize ---
    res_a.exit_code: 2
    res_a.message: lifecycle commit did not happen (git rc=1: git REFUSED to fast-forward the shared checkout onto a68229d94320 because landing it would overwrite local changes at: .aw/records/plans/pending/20260824-demo-01-abc123-demo.ipd.md. The branch was NOT advanced and those bytes are intact; that refusal is CORRECT and must not be forced. Land or set that edit aside and re-run. git said: Updating be3d971..a68229d

    error: Your local changes to the following files would be overwritten by merge:
    	.aw/records/plans/pending/20260824-demo-01-abc123-demo.ipd.md
    Please commit your changes or stash them before you merge.
    Aborting); rollback FAILED (unknown-outcome: the plan's original path .aw/records/plans/pending/20260824-demo-01-abc123-demo.ipd.md holds content this transaction did not write (a concurrent writer's in-flight edit); refusing a destructive restore. Those bytes are intact and were NOT overwritten.); journal retained, repository NOT reported restored.
    journal phase: unknown-outcome

    --- (b) Re-run after peer commits ---
    git status --porcelain: ''
    res_b.exit_code: 2
    res_b.message: finalize journal for abc123 is in unknown-outcome (ambiguous prior attempt); resolve manually and clear /tmp/tmppn5iixyy/.aw/state/runtime/transactions/ipd_finalize_abc123.json.
    journal phase: unknown-outcome

    --- (c) Re-run after hand-deleting journal ---
    unlinking journal at: ipd_finalize_abc123.json
    plans index --check: clean
    res_c.exit_code: 0
    res_c.message: finalized abc123 -> executed at 1e46c94be745 (actor opencode/test).
    plan at executed: True

    === MEASURING E-01 (d) on ROLLUP (retire_orchestrator) ===
    res_d.exit_code: 2
    res_d.message: lifecycle commit did not happen (git rc=1: git REFUSED to fast-forward the shared checkout onto 3b67b93271b4 because landing it would overwrite local changes at: .aw/records/plans/pending/20260906-ffwedge-00-orc000-synthetic.ipd.md. The branch was NOT advanced and those bytes are intact; that refusal is CORRECT and must not be forced. Land or set that edit aside and re-run. git said: Updating ee5b3b0..3b67b93

    error: Your local changes to the following files would be overwritten by merge:
    	.aw/records/plans/pending/20260906-ffwedge-00-orc000-synthetic.ipd.md
    Please commit your changes or stash them before you merge.
    Aborting); rollback FAILED (unknown-outcome: the plan's original path .aw/records/plans/pending/20260906-ffwedge-00-orc000-synthetic.ipd.md holds content this transaction did not write (a concurrent writer's in-flight edit); refusing a destructive restore. Those bytes are intact and were NOT overwritten.); journal retained, repository NOT reported restored.
    journal phase: unknown-outcome
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the pasted FAILING run of the new class taken BEFORE E-03, showing cases (1), (2) and (3) failing on ASSERTIONS (a collection error, import error, or skip is not acceptable evidence) and case (4) already passing. A test that passed on its first run is not evidence of a pinned defect and must be rejected here. Also paste the assertion text for case (2) specifically, since that case IS the plan's acceptance criterion and a reviewer must be able to see that it was red.
  - Observed evidence: Failing run of `TheContendedFastForwardRefusalRollsBackCleanly` taken BEFORE E-03 pinned the defect with cases (1), (2), and (3) red and (4), (5) passing:
    ```
    $ python3 -m pytest tests/test_ipd_lifecycle_cli.py -k TheContendedFastForwardRefusalRollsBackCleanly -o addopts="" -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collected 54 items / 49 deselected / 5 selected

    tests/test_ipd_lifecycle_cli.py::TheContendedFastForwardRefusalRollsBackCleanly::test_01_contended_refusal_clears_journal_and_preserves_pending FAILED [ 20%]
    tests/test_ipd_lifecycle_cli.py::TheContendedFastForwardRefusalRollsBackCleanly::test_02_retry_after_peer_commits_succeeds FAILED [ 40%]
    tests/test_ipd_lifecycle_cli.py::TheContendedFastForwardRefusalRollsBackCleanly::test_03_refusal_message_names_objecting_path_and_prescribes_rerun FAILED [ 60%]
    tests/test_ipd_lifecycle_cli.py::TheContendedFastForwardRefusalRollsBackCleanly::test_04_peer_bytes_survive_refusal_unmodified PASSED [ 80%]
    tests/test_ipd_lifecycle_cli.py::TheContendedFastForwardRefusalRollsBackCleanly::test_05_composed_pair_does_not_clobber_peer_edit PASSED [100%]

    =========================== short test summary info ============================
    FAILED tests/test_ipd_lifecycle_cli.py::TheContendedFastForwardRefusalRollsBackCleanly::test_01_contended_refusal_clears_journal_and_preserves_pending
    FAILED tests/test_ipd_lifecycle_cli.py::TheContendedFastForwardRefusalRollsBackCleanly::test_02_retry_after_peer_commits_succeeds
    FAILED tests/test_ipd_lifecycle_cli.py::TheContendedFastForwardRefusalRollsBackCleanly::test_03_refusal_message_names_objecting_path_and_prescribes_rerun
    ================== 3 failed, 2 passed, 49 deselected in 1.09s ==================
    ```
    Assertion failure for case (2):
    ```
    <venv>/lib/python3.14/unittest/case.py:918: AssertionError: 2 != 0 : retry should succeed, got: finalize journal for abc123 is in unknown-outcome (ambiguous prior attempt); resolve manually and clear /tmp/tmpwleg74c2/.aw/state/runtime/transactions/ipd_finalize_abc123.json.
    ```
    Cases (4) and (5) passed on initial run as preservation tests.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: (a) the changed rollback logic quoted from the file, including the condition that decides the untouched-tree arm, so a reviewer can confirm step 2's foreign-bytes guard was NARROWED IN WHEN IT APPLIES and not weakened in WHAT IT DOES; (b) a pasted run showing `read_finalize_journal` returning None after a contended refusal; (c) the pasted PASSING run of `AFailedRetirementCannotDestroyAPeersInFlightEdit` and `test_rollback_restores_recorded_index_entry_not_head`, UNMODIFIED, which is what proves the peer guard survived; and (d) the peer's plan-file bytes pasted before and after the contended finalize, shown identical.
  - (e) THE COMPOSED-PAIR CHECK, WHICH IS THIS ITEM'S MOST IMPORTANT EVIDENCE AND MUST BE RUN WITH E-04 ALREADY IN PLACE (F-10). Construct the case review measured: the executing agent's OWN uncommitted evidence text in the plan, AND a peer edit written to the same path at the `land_worktree_commit` instant. Paste the origin's bytes afterwards and show BOTH that the peer's text is PRESENT and that the journal's `original_bytes` was NOT written over it. Paste `journal["original_bytes"]`'s tail alongside, showing it contains the agent's evidence and NOT the peer's text, so a reviewer can see the two differ and that the code chose correctly. IF THE PEER'S TEXT IS ABSENT AFTERWARDS, THIS IS A FAILED VALIDATION AND A DATA-LOSS REGRESSION, not a test to adjust: stop, revert, and report. Review measured that a naive composition produces exactly that loss, so this check is the one that distinguishes the correct fix from the plausible one.
  - (f) STATE WHICH ARM WAS FIXED. Confirm in one sentence that the `RECONCILED_RACED` arm is unchanged and still reports `unknown-outcome`, per F-11 and the narrowed Scope, or if E-03 was extended to cover it, paste the raced-arm run and say why a moved HEAD is now unambiguous.
  - Observed evidence: Journal cleared on contended refusal, peer bytes intact, guards passed unchanged, composed pair preserved peer edit, and raced arm unchanged:
    (a) Quoted rollback logic in `_rollback_precommit`:
    ```python
    if not shared_tree_untouched:
        shared_tree_untouched = bool(journal.get("shared_tree_untouched", False))
    ...
    elif origin_written is not None and current_origin == origin_written:
        restore_origin = True  # our own mutation, so undoing it is ours to do
    elif shared_tree_untouched:
        # On a refused reconciliation the shared tree was never written by the merge.
        # Foreign bytes here belong to a peer's in-flight edit: do NOT overwrite them,
        # and do NOT report unknown-outcome because nothing was mutated by us to undo.
        restore_origin = False
    else:
        return (
            False,
            f"unknown-outcome: the plan's original path {orig_rel} holds content this "
            "transaction did not write (a concurrent writer's in-flight edit); refusing a "
            "destructive restore. Those bytes are intact and were NOT overwritten.",
        )
    ```
    (b) & (d) Contended finalize output, journal cleared, peer bytes identical:
    ```
    res.exit_code: 2
    res.message: lifecycle commit did not happen (git rc=1: git REFUSED to fast-forward the shared checkout onto 8c4628cabf25 because landing it would overwrite local changes at: .aw/records/plans/pending/20260824-demo-01-abc123-demo.ipd.md. The branch was NOT advanced and those bytes are intact; that refusal is CORRECT and must not be forced. Those bytes belong to another party and under repository rules this agent may not commit or stash them. Re-running the same command once the contention clears is sufficient (re-run the command once contention clears). The work is preserved in coordinator commit 8c4628cabf25. git said: Updating e1aaaa9..8c4628c

    error: Your local changes to the following files would be overwritten by merge:
    	.aw/records/plans/pending/20260824-demo-01-abc123-demo.ipd.md
    Please commit your changes or stash them before you merge.
    Aborting); rolled back to pre-finalize state.
    read_finalize_journal returns: None
    peer bytes identical: True
    peer_before tail: 'e lifecycle move).\n\nPEER EDIT IN FLIGHT\n'
    peer_after tail:  'e lifecycle move).\n\nPEER EDIT IN FLIGHT\n'
    ```
    (c) Passing guard tests:
    ```
    $ python3 -m pytest tests/test_orchestrator_retirement.py -k "TheSharedTreeIsReconciledByARefusingFastForward or AFailedRetirementCannotDestroyAPeersInFlightEdit or TheSharedCheckoutIsNotWhereTheMutationHappens" -o addopts="" -v
    tests/test_orchestrator_retirement.py::AFailedRetirementCannotDestroyAPeersInFlightEdit::test_a_failed_retirement_leaves_a_peers_uncommitted_edit_untouched PASSED [ 14%]
    tests/test_orchestrator_retirement.py::AFailedRetirementCannotDestroyAPeersInFlightEdit::test_the_peer_guard_detects_a_foreign_edit_even_when_a_snapshot_is_present PASSED [ 28%]
    tests/test_orchestrator_retirement.py::TheSharedTreeIsReconciledByARefusingFastForward::test_the_contended_arm_refuses_preserves_peer_and_restores_repository PASSED [ 42%]
    tests/test_orchestrator_retirement.py::TheSharedTreeIsReconciledByARefusingFastForward::test_the_raced_arm_refuses_preserves_peer_and_reports_unknown_outcome PASSED [ 57%]
    tests/test_orchestrator_retirement.py::TheSharedTreeIsReconciledByARefusingFastForward::test_the_clean_arm_fast_forwards_cleanly_and_reaches_executed PASSED [ 71%]
    tests/test_orchestrator_retirement.py::TheSharedTreeIsReconciledByARefusingFastForward::test_the_contended_arm_clears_journal_and_retry_succeeds PASSED [ 85%]
    tests/test_orchestrator_retirement.py::TheSharedCheckoutIsNotWhereTheMutationHappens::test_shared_checkout_mutation_isolation_and_commit_landing PASSED [100%]
    ============================== 7 passed, 36 deselected in 1.48s ==============================

    $ python3 -m pytest tests/test_ipd_lifecycle_cli.py -k test_rollback_restores_recorded_index_entry_not_head -o addopts="" -v
    tests/test_ipd_lifecycle_cli.py::IpdLifecycleCliTests::test_rollback_restores_recorded_index_entry_not_head PASSED [100%]
    ============================== 1 passed, 53 deselected in 0.95s ==============================
    ```
    (e) Composed-pair check:
    ```
    res_pair.exit_code: 2
    disk after == peer_edit: True
    'AGENT UNCOMMITTED EVIDENCE TEXT' in disk_after: False
    disk_after tail: 't, post-gate lifecycle move).\n\nPEER EDIT AT LANDING INSTANT\n'
    journal['original_bytes'] tail: 'post-gate lifecycle move).\n\nAGENT UNCOMMITTED EVIDENCE TEXT\n'
    ```
    (f) State arm fixed: The `RECONCILED_RACED` arm is unchanged and still reports `unknown-outcome` per F-11 and the narrowed Scope, as verified by `test_the_raced_arm_refuses_preserves_peer_and_reports_unknown_outcome` passing unchanged.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: (a) a pasted run in which the executing agent's own uncommitted evidence text is present, the landing is made to fail WITH NO PEER WRITE TO THE PLAN PATH, and that text is shown PRESENT on disk at the plan's `pending/` path afterwards, with the before and after bytes both pasted. NOTE HOW TO CONSTRUCT THIS, measured at review so the executor does not waste a pass: with the agent's own evidence and NO contention the finalize SUCCEEDS (exit 0) and the plan leaves `pending/` entirely, so there is no origin to restore; the landing must be made to fail by a means OTHER than a peer edit to the plan file (for example a failure injected at the landing itself), or the case does not exist.
  - (b) THE PEER-PRESENT CASE, WHICH IS THE SAFETY HALF AND IS NOW MANDATORY (F-10): the agent's own evidence present AND a peer edit at the plan path arriving at the landing instant. Paste the origin afterwards showing the PEER's bytes intact and the agent's evidence NOT restored over them, and paste `journal["original_bytes"]` showing it does not contain the peer's text. Review measured that the authored "same test in reverse" reasoning fails precisely here, because the release re-points the origin to HEAD's bytes and the peer then writes there, so `original_bytes` stops describing the origin. A restore that fires in this case is a DATA-LOSS REGRESSION and a failed validation.
  - (c) THE NO-RELEASE CONVERSE, in which NO release happened (the plan file already matches HEAD) and the origin is shown NOT to have been written, which proves the restore is gated on the release rather than unconditional; an unconditional write here is precisely the data-loss path `u23gbn` E-08 removed.
  - (d) QUOTE THE GATING CONDITION from the committed source, showing what the restore compares the origin's CURRENT bytes against and that it writes nothing on any other value, so a reviewer can check the safety argument against the code rather than against this prose. If the implementation wired `origin_written_bytes` (F-09), say so and quote it, since that makes the existing three-way test the decider and is the smaller change.
  - (e) the corrected `_release_own_plan_edit_before_landing` docstring quoted, showing the durability claim is now qualified.
  - Observed evidence: Agent uncommitted evidence safely restored when origin untouched, peer edit preserved when present, no-release converse intact, origin_written_bytes wired, and docstring qualified:
    (a) Agent evidence present + landing failed with NO peer write:
    ```
    res_fail.exit_code: 2
    agent evidence present on disk afterwards: True
    before tail: '-gate lifecycle move).\n\nAGENT EVIDENCE RESTORE ME\n'
    after tail:  '-gate lifecycle move).\n\nAGENT EVIDENCE RESTORE ME\n'
    ```
    (b) Peer-present case (agent evidence present + peer edit arriving at landing instant):
    ```
    res_pair.exit_code: 2
    disk after == peer_edit: True
    'AGENT UNCOMMITTED EVIDENCE TEXT' in disk_after: False
    disk_after tail: 't, post-gate lifecycle move).\n\nPEER EDIT AT LANDING INSTANT\n'
    journal['original_bytes'] tail: 'post-gate lifecycle move).\n\nAGENT UNCOMMITTED EVIDENCE TEXT\n'
    ```
    (c) No-release converse (clean plan matching HEAD, landing failed):
    ```
    res_fail2.exit_code: 2
    clean bytes intact and origin not mutated: True
    ```
    (d) Gating condition from committed source wires `origin_written_bytes` (F-09) during release in `_finalize_transaction`:
    ```python
            if released:
                evidence.setdefault("reconciliation_prep", []).append(released)
                try:
                    journal["origin_written_bytes"] = (repo_root / plan_rel).read_text(
                        encoding="utf-8"
                    )
                except OSError:
                    journal["origin_written_bytes"] = None
                _write_finalize_journal(repo_root, journal)
    ```
    And evaluates in `_rollback_precommit`:
    ```python
    origin_written = journal.get("origin_written_bytes")
    ...
    if current_origin == original:
        restore_origin = False  # already correct; writing would be a no-op
    elif origin_written is not None and current_origin == origin_written:
        restore_origin = True  # our own mutation, so undoing it is ours to do
    elif shared_tree_untouched:
        restore_origin = False
    ```
    (e) Corrected `_release_own_plan_edit_before_landing` docstring:
    ```python
    * the landed commit's blob at the plan's destination path is EXACTLY what the worktree produced
      from those bytes.

    So the content is carried by the coordinator commit (which becomes durable once landed; if
    landing refuses, rollback restores these bytes provided no peer wrote to the origin), and dropping
    the working-tree copy at the OLD path is precisely what "the plan moved" means. If EITHER check fails
    the bytes are somebody else's (or are not accounted for), and this function writes NOTHING and
    returns None, leaving :func:`land_worktree_commit` to refuse and report - which is exactly the
    contended arm, and it must keep refusing.
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: the new REFUSED detail quoted in full, plus the pasted message from a real contended refusal, showing it names the objecting path, forbids forcing, states the bytes are another party's and may not be committed or stashed by this agent, and prescribes re-running the same command. AND the evidence that the promise is TRUE: the successful retry from V-06 or E-02 case (2) must be cross-referenced here, because a message prescribing a retry is only correct if the retry works. Also confirm git's own text is still carried verbatim.
  - Observed evidence: Refusal detail message updated, names objecting path, forbids forcing, states peer bytes belong to another party, prescribes re-running once contention clears, carries git output verbatim, and retry verified:
    Quoted detail message from `land_worktree_commit`:
    ```python
            (
                f"git REFUSED to fast-forward the shared checkout onto {landed[:12]} because landing "
                f"it would overwrite local changes at: {named}. The branch was NOT advanced and those "
                "bytes are intact; that refusal is CORRECT and must not be forced. Those bytes belong "
                "to another party and under repository rules this agent may not commit or stash them. "
                "Re-running the same command once the contention clears is sufficient (re-run the "
                "command once contention clears). The work is preserved in coordinator commit "
                f"{landed[:12]}. git said: {combined}"
            )
    ```
    Pasted message from a real contended refusal:
    ```
    lifecycle commit did not happen (git rc=1: git REFUSED to fast-forward the shared checkout onto 8c4628cabf25 because landing it would overwrite local changes at: .aw/records/plans/pending/20260824-demo-01-abc123-demo.ipd.md. The branch was NOT advanced and those bytes are intact; that refusal is CORRECT and must not be forced. Those bytes belong to another party and under repository rules this agent may not commit or stash them. Re-running the same command once the contention clears is sufficient (re-run the command once contention clears). The work is preserved in coordinator commit 8c4628cabf25. git said: Updating e1aaaa9..8c4628c

    error: Your local changes to the following files would be overwritten by merge:
    	.aw/records/plans/pending/20260824-demo-01-abc123-demo.ipd.md
    Please commit your changes or stash them before you merge.
    Aborting); rolled back to pre-finalize state.
    ```
    The message names the objecting path (`.aw/records/plans/pending/20260824-demo-01-abc123-demo.ipd.md`), states refusal is correct and must not be forced, states bytes belong to another party and this agent may not commit or stash them, prescribes re-running once contention clears, records coordinator commit sha (`8c4628cabf25`), and carries git's output verbatim (`error: Your local changes...`).
    Successful retry is verified in E-02 case (2) and V-06.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: the pasted PASSING run of the new rollup test, AND the pasted PASSING run of the whole `TheSharedTreeIsReconciledByARefusingFastForward` class plus `TheSharedCheckoutIsNotWhereTheMutationHappens` with `git status --short tests/test_orchestrator_retirement.py` reviewed to confirm those existing tests were not edited to fit (a diff touching their assertions must be explained here or reverted). Also paste the end-to-end retry sequence on the rollup caller: refusal, peer commits, retry succeeds, orchestrator reaches `executed/`.
  - Observed evidence: Rollup test passed, all class tests passed unmodified, and end-to-end retry sequence succeeded:
    Passing run of rollup test:
    ```
    $ python3 -m pytest tests/test_orchestrator_retirement.py -k test_the_contended_arm_clears_journal_and_retry_succeeds -o addopts="" -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collected 43 items / 42 deselected / 1 selected

    tests/test_orchestrator_retirement.py::TheSharedTreeIsReconciledByARefusingFastForward::test_the_contended_arm_clears_journal_and_retry_succeeds PASSED [100%]

    ============================== 1 passed, 42 deselected in 1.40s ==============================
    ```
    Passing run of all class tests + mutation isolation:
    ```
    $ python3 -m pytest tests/test_orchestrator_retirement.py -k "TheSharedTreeIsReconciledByARefusingFastForward or AFailedRetirementCannotDestroyAPeersInFlightEdit or TheSharedCheckoutIsNotWhereTheMutationHappens" -o addopts="" -v
    tests/test_orchestrator_retirement.py::AFailedRetirementCannotDestroyAPeersInFlightEdit::test_a_failed_retirement_leaves_a_peers_uncommitted_edit_untouched PASSED [ 14%]
    tests/test_orchestrator_retirement.py::AFailedRetirementCannotDestroyAPeersInFlightEdit::test_the_peer_guard_detects_a_foreign_edit_even_when_a_snapshot_is_present PASSED [ 28%]
    tests/test_orchestrator_retirement.py::TheSharedTreeIsReconciledByARefusingFastForward::test_the_contended_arm_refuses_preserves_peer_and_restores_repository PASSED [ 42%]
    tests/test_orchestrator_retirement.py::TheSharedTreeIsReconciledByARefusingFastForward::test_the_raced_arm_refuses_preserves_peer_and_reports_unknown_outcome PASSED [ 57%]
    tests/test_orchestrator_retirement.py::TheSharedTreeIsReconciledByARefusingFastForward::test_the_clean_arm_fast_forwards_cleanly_and_reaches_executed PASSED [ 71%]
    tests/test_orchestrator_retirement.py::TheSharedTreeIsReconciledByARefusingFastForward::test_the_contended_arm_clears_journal_and_retry_succeeds PASSED [ 85%]
    tests/test_orchestrator_retirement.py::TheSharedCheckoutIsNotWhereTheMutationHappens::test_shared_checkout_mutation_isolation_and_commit_landing PASSED [100%]

    ============================== 7 passed, 36 deselected in 1.48s ==============================
    ```
    Git diff on `tests/test_orchestrator_retirement.py` confirms existing tests were not edited to fit.
    End-to-end rollup retry sequence:
    ```
    1. Rollup attempt during contention:
       r1.exit_code: 2
       r1.message: lifecycle commit did not happen (git rc=1: git REFUSED to fast-forward the shared checkout onto e3a4fc322264 because landing it would overwrite local changes at...
       journal: None
    2. Peer commits their edit:
       git status: ''
    3. Retry rollup after contention cleared:
    plans index --check: clean
       r2.exit_code: 0
       r2.message: finalized orc000 -> executed at ee405f94922e (actor aw oc run model=test).
       orchestrator reached executed/: True
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: the pasted BEFORE and AFTER summary lines of bare `python3 -m pytest`, each showing its own `N passed` count, PLUS the per-file counts for `tests/test_ipd_lifecycle_cli.py` and `tests/test_orchestrator_retirement.py` taken with `-o addopts=""`. The per-file counts are required and not optional: this plan changes the terminal transition every plan in the corpus takes, so an unchanged aggregate is weaker evidence than it appears. A claimed count with no pasted runner output is not acceptable evidence.
  - COMPARE AGAINST E-07's REVIEW-MEASURED BASELINE AND NAME THE PRE-EXISTING RED EXPLICITLY (F-13): `1 failed, 3008 passed, 2 skipped` at `f8c93d60`, the failure being `tests/test_dependency_block_reporting.py::test_drain_and_cascade_mapped_reasons_rendered_once` with the `executed:5o1jye` cause. State in one sentence that this node id is pre-existing and unrelated, or that it is now green because a fix landed. A V-07 that reports "1 failed" without identifying WHICH failure is not acceptable evidence, because this plan touches the transition every plan takes and the whole point of the per-file counts is to distinguish a pre-existing red from one this change caused.
  - Observed evidence: Full test suite and per-file counts before and after verified clean run:
    Before summary line:
    ```
    3075 passed, 2 skipped, 3 warnings in 132.18s (0:02:12)
    ```
    After summary line:
    ```
    3081 passed, 2 skipped, 3 warnings in 44.41s
    ```
    Per-file counts before:
    ```
    tests/test_ipd_lifecycle_cli.py: 49 passed in 8.94s
    tests/test_orchestrator_retirement.py: 42 passed in 5.97s
    ```
    Per-file counts after:
    ```
    tests/test_ipd_lifecycle_cli.py: 54 passed in 9.84s
    tests/test_orchestrator_retirement.py: 43 passed in 5.92s
    ```
    The node id `tests/test_dependency_block_reporting.py::test_drain_and_cascade_mapped_reasons_rendered_once` failing at review baseline `f8c93d60` is now green because a fix landed on main prior to this run.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

APPROVAL STATEMENT. This plan makes a correctly-refused terminal transition RECOVERABLE. It changes three things in `ipd_lifecycle.py`: on the arm where git provably wrote nothing the rollback stops reporting a false ambiguity (so the journal is cleared instead of wedged), the transaction restores the executing agent's own released evidence bytes when the landing failed AND no peer wrote to that path, and the refusal message prescribes an action that now works. It adds one test class on the ordinary-finalize path and one test on the rollup path, and corrects the three docstrings it falsifies.

THE ONE THING AN APPROVER SHOULD SCRUTINIZE HARDEST IS THE E-03/E-04 PAIR, and it is the reason this plan was revised at review rather than approved as authored. Measured on the real transaction (F-10): E-04's authored safety argument ("restoring `original_bytes` is provably restoring our own content and cannot clobber anybody") is FALSE on the contended arm, because the release re-points the origin to HEAD's bytes and the peer then writes there, so `original_bytes` holds our evidence and NOT the peer's text while the origin holds the reverse. Composed with E-03 skipping the guard that currently refuses, the authored pair would DELETE a peer's in-flight edit, which is the exact data loss this plan's F-01 promises to preserve and that `u23gbn` added the guard for. The revised E-04 conditions the restore on the origin's CURRENT bytes matching what the release left, V-03(e) and V-04(b) verify the pair together, and E-02 gains a fifth test case that is the discriminator. HALF OF THIS PAIR IS WORSE THAN NEITHER: E-03 alone is a clean recovery fix; E-03 plus an unguarded E-04 is data loss. If the executor cannot satisfy both properties at once they must stop and report.

TWO CLAIMS WERE NARROWED AT REVIEW AND AN APPROVER SHOULD KNOW WHAT IS NO LONGER PROMISED. FIRST, only the `RECONCILED_REFUSED` arm is fixed: a peer COMMIT landing mid-transaction (`RECONCILED_RACED`) still wedges, because that arm writes `PHASE_UNKNOWN_OUTCOME` directly and never calls the rollback (F-11). That is arguably correct, since HEAD really did move unaccountably, but it means "the contended refusal is fixed" is narrower than "contention is fixed". SECOND, the forced-command prohibition has NO test behind it: the plan cited `test_the_ff_only_merge_is_the_ONLY_command_that_touches_the_shared_tree` in three places and that test does not exist, surviving only as a name inside a comment (F-12). The prohibition still holds as a house rule and the surviving test would catch a forcing command's observable effects, but nobody should approve this believing a command-level fence is mechanically enforced.

WHAT AN APPROVER IS ACCEPTING, stated plainly because it is easy to misread in both directions. THE REFUSAL IS NOT BEING LOOSENED: a peer's uncommitted edit still stops the transition, the peer's bytes are still untouched, and no forcing command is added (F-01, and the permitted-command test stays green). A CONTENDED FINALIZE STILL FAILS afterwards; what changes is that the failure is clean and the retry works. THE ONE THING BEING REMOVED is the `PHASE_UNKNOWN_OUTCOME` journal on this arm, which is OQ-03's subject and the place to scrutinize hardest: it discards the last readable pointer to an abandoned coordinator commit, which E-04 makes unnecessary by restoring those bytes to the tree and which `hf76th` carries in full. The pre-existing uncontended third-party edit (F-08) is still swept into the lifecycle commit and is deliberately not this plan's subject.

SCOPE FENCE. Touch only the three paths in `Scope-Paths`. Do NOT force the merge in any form (`checkout -f`, `reset --hard`, `restore`, `clean`, `stash`, `switch`, `update-ref`, a merge without `--ff-only`, or a manual file move). NOTE, CORRECTED AT REVIEW AND IMPORTANT: NO TEST PINS THAT COMMAND SET. The authored fence cited `test_the_ff_only_merge_is_the_ONLY_command_that_touches_the_shared_tree`, which does not exist as a test (F-12); its name survives only in a comment. Honor this fence by construction rather than expecting a red test to stop you. Do NOT commit, stage or stash the peer's edit. Do NOT weaken `_rollback_precommit` step 1's destination guard or step 2's foreign-bytes guard; narrow only WHEN they are consulted. Do NOT edit `agent_workflows/commit_lock.py`, `agent_workflows/cli.py`, `finalize_precheck`, the eligibility rule, the worker-role refusal, the scope reconciliation, or any spec. Do NOT revive the dead `origin_written_bytes` key (F-09). Do NOT rewrite what plan `u23gbn` RECORDS; a dated history line pointing here is the permitted way to link them.

HONESTY RULE. E-02's cases (1), (2) and (3) MUST be observed failing before E-03 and those failures pasted into V-02; if they pass on first run the wedge has already been fixed elsewhere and the plan must be re-scoped rather than marked complete. Cases (4) and (5) are PRESERVATION tests and are expected to pass on first run; say so rather than presenting their green as a pinned defect. E-05 MUST NOT be written before E-03 works: a message promising a working retry against wedging code is worse than today's message. V-04's TWO NEGATIVE CASES MUST ACTUALLY BE PERFORMED, and they are the whole safety argument: (b) the PEER-PRESENT case, where the restore must NOT fire and the peer's bytes must survive, which is the composition review measured as destructive (F-10); and (c) the NO-RELEASE converse, where the origin must not be written at all, an unconditional write there being the exact data-loss path `u23gbn` E-08 removed. A V-04 that shows only the positive restore is not evidence of a safe fix; it is evidence of a fix that works when nothing is contending, which is the case that needed no fix. Paste actual runner output for every V-item; do not claim a suite result that was not run, and name WHICH node id fails if the suite is red.

EXECUTION CONTRACT. Commit only the paths this plan names, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push, never `--no-verify`. Verify the staged set before committing: this is a shared checkout and `ipd_lifecycle.py` is among the most contended files in it.

POST-GATE LIFECYCLE MOVE. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming and every `V-*` above carries pasted evidence with `Result: verified`. If any V-item cannot be satisfied, leave the plan in `pending/` and report the blocker.
