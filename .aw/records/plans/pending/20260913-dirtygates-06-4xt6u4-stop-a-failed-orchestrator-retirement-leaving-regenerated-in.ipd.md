# IPD: Stop a failed orchestrator retirement leaving regenerated index files in the shared checkout

- Date: 2026-09-13
- Kind: child
- Concern: A FAILED orchestrator retirement does not restore the tree it started from, in a rollback whose documented job is to restore it. Measured 2026-09-13 with the repository's own fault injector: the plan was correctly restored to `pending/` with its original bytes, the `executed/` copy was removed, and HEAD was unmoved, but `git status --porcelain` afterwards reported `?? .aw/records/plans/INDEX.json` and `?? .aw/records/plans/INDEX.md`. The rollback regenerates the plans index from the current corpus, which WRITES those files rather than restoring their prior state. The existing fault tests assert plan restoration and HEAD but never tree cleanliness, which is why this went unnoticed.
- Scope: Make a failed retirement leave the shared checkout byte-identical to how it found it, and add the tree-cleanliness assertion the existing fault tests lack. Excludes relocating the retirement mutations into a worktree, which is Order 04 (`u23gbn`) and is gated on that plan's blocking OQ-03 about shared-versus-forked transaction code.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, tests/test_orchestrator_retirement.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: dirtygates
- Order: 6
- Highest E allocated: 02
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: 4xt6u4
- Approval: 2026-09-14, recorded via aw ipd set: status set to approved
- Priority: medium
- Work-Kind: bug

## Workflow history
- 2026-09-16 executed (opencode (its_direct/pt3-claude-opus-5-1m-us)): E-01/E-02 performed, V-01/V-02 verified with pasted evidence. F-1 reproduced first at HEAD `daa48f42` in both prior-state cases, confirming the defect and F-7's narrowing. THE MECHANISM DEVIATES FROM THE PLAN TEXT AND IS FLAGGED FOR HUMAN REVIEW (decision `07-4xt6u4-D1`): the plan prescribed reinstating the `index_json_before`/`index_md_before` journal keys and RESTORING the manifests on rollback; the implementation instead REMOVES the rollback's regeneration entirely, which meets the plan's stated acceptance property exactly. The reason is a new measurement made possible by Order 04 (`u23gbn`) having landed since review: across all three pre-commit fault points x both prior-state cases, the shared manifests are still byte-identical to their pre-attempt state at the instant `_rollback_precommit` is ENTERED, because the mutations happen in a coordinator worktree and the manifests are gitignored. Step 4 was therefore the SOLE creator of the residue, so not-writing and restoring have the same postcondition, and not-writing additionally fixes a measured peer-clobber (pre-fix the regeneration replaced a peer's concurrent manifest write) that a restore would not have. F-8 answered (decision `07-4xt6u4-D2`): the rollback-path fail-loud arm is dropped, the success-path gate is untouched. F-9 confirmed and honored: the midpoint (not end) is where the `before_commit` test's comparison sits. Six of the nine assertions were demonstrated FAILING against the pre-fix code. Full suite bare: 31 failed/7377 passed baseline -> 31 failed/7384 passed after, FAILED-set diff EMPTY (all 31 pre-existing and unrelated).
- 2026-09-14 approved (aw set): status set to approved
- 2026-09-13 reviewed (opencode (its_direct/pt3-claude-opus-5-1m-us)): /plan-review ROUND 1: APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL. PR-601..PR-604, all FIXED, no open questions. F-1 independently reproduced at HEAD 54b6f7ce with identical values, so the plan's central measurement is sound. Four corrections, each measured: F-6 the prescribed journal keys index_json_before/index_md_before were DELIBERATELY deleted (674f2c68) and a standing comment at :2642-2645 forbids them, so the fix must update that comment or strand documentation that tells the next reader to undo it; F-7 regeneration is BYTE-EXACT when the manifests already exist, so the only real defect is create-where-absent and the fix must restore ABSENCE rather than merely snapshot bytes; F-8 replacing step 4 silently drops an untested fail-loud arm; F-9 E-02's second assertion site ends on a SUCCESSFUL retirement, so an emptiness assertion there would be false. No product code changed by this review.

- 2026-09-13 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-09-13 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): CARVED OUT OF ORDER 04 (`u23gbn`) at the maintainer's direction after `/plan-review` raised PR-401. That review found Order 04 had a scoping error (its mechanisms live in shared code reaching every plan's terminal transition, not only the 4 rollup retirements it was scoped against) and correctly observed that Order 04's E-03 and E-04 are NOT gated by that question. Those two items are this plan; they fix a measured bug and need no architecture ruling.

## Goal

A retirement that fails must leave no trace. Today it leaves two untracked index files, so the tree after a failure differs from the tree before it.

THE GOAL IS NARROWER THAN THAT SENTENCE SUGGESTS, corrected at review so the fix is aimed at the real case (F-7). MEASURED: when the manifests ALREADY EXIST, the rollback's regeneration reproduces them BYTE-IDENTICALLY, because by the time step 4 runs the corpus is back to its prior state and the generator is deterministic. So regeneration and restore agree in that case, and the defect is confined to the CREATE-WHERE-ABSENT case: a tree that had no manifests before the attempt has two afterwards. That is the measured residue and it is the whole of the bug. The practical consequence for E-01 is that the fix must be able to restore ABSENCE, not merely to snapshot bytes, and the practical consequence for E-02 is that its assertion must compare against the pre-attempt status rather than assert emptiness.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: leave no residue

- [x] E-01 Stop a failed retirement leaving untracked index files in the shared checkout. `_rollback_precommit` (`ipd_lifecycle.py:1874`) step 4 "regenerates the plans index from the CURRENT corpus", which WRITES `.aw/records/plans/INDEX.json` and `INDEX.md` rather than restoring whatever state they were in before the attempt. NOTE WHAT MUST NOT CHANGE: the regeneration on the SUCCESS path is correct and stays, because a successful retirement really does change the corpus. Only the rollback path is wrong. Also preserve the existing `unknown-outcome` classification: if the index files were changed by a concurrent writer since the checkpoint, this must NOT perform a destructive restore, exactly as the destination-changed case already refuses (`:1897-1906`).
  - THE PRESCRIBED MECHANISM REINSTATES TWO JOURNAL KEYS THAT WERE DELIBERATELY DELETED, AND THE PLAN MUST NOT DO THAT SILENTLY. FOUND AT REVIEW (PR-601, F-6). This item said to "capture it in the journal alongside the plan's `original_bytes`". Those exact keys ALREADY EXISTED and were removed ON PURPOSE: `_finalize_transaction` carries an explicit standing comment (`:2642-2645`) reading "the journal deliberately carries no `index_json_before`/`index_md_before` content snapshot. Those keys existed to restore the plans manifests on rollback, but NOTHING ever read them ... so they were dead weight describing a restore that never happened." The deletion was part of commit `674f2c68` (2026-09-07, "stop committing the generated index manifests"), whose message lists it as one of nine deliberate contributor removals and calls it "a content-restore no code performs". So this item proposes to re-add the very keys that comment forbids, which means the comment becomes FALSE the moment the fix lands. TWO OBLIGATIONS FOLLOW. FIRST, UPDATE THAT COMMENT in the same change, saying the keys are back and that they are now READ (which is what makes them not dead weight this time); leaving it would strand a comment that actively tells the next reader not to do what the code does. SECOND, USE THE ORIGINAL KEY NAMES `index_json_before` / `index_md_before` rather than inventing new ones, so the history reads as a reinstatement rather than as an unrelated addition.
  - THE PRIOR STATE MUST DISTINGUISH ABSENT FROM PRESENT, and absent is the case that actually matters (F-7). MEASURED at review: when the manifests ALREADY EXIST, the rollback's regeneration reproduces them BYTE-IDENTICALLY (verified by capturing `INDEX.json` before a `after_move` fault and comparing after: identical, and both correctly naming the plan's `pending/` path). The ONLY case where regeneration and restore differ is when the manifests did NOT exist beforehand, where regeneration CREATES them and restore would leave them absent. That is exactly the measured `?? INDEX.json` / `?? INDEX.md` residue. So the journal value must be a three-state thing (absent / present-with-these-bytes), and "absent" must be restorable by DELETING a file the rollback itself caused to appear. Deleting a manifest is safe here and the repository already says so: an absent manifest is `check.stale-index-missing` at severity `info` (`check_engine.py:333-335`), which does NOT fail the gate, and verified at review `aw index plans --check` returns rc=0 with both manifests absent.
  - SAY WHAT HAPPENS TO THE FAIL-LOUD CHECK, which this item silently drops (F-8). Step 4 does not merely regenerate: it calls `_refresh_plans_index_fail_loud` (`:1656-1695`), which regenerates AND re-runs `--check` and RAISES on non-convergence, and the rollback turns that raise into `(False, "rollback index regeneration failed: ...")`. If regeneration is replaced by a restore, that verification has no subject and the arm disappears. Decide and state which: keep a post-restore consistency check of some kind, or drop the arm and record that a rollback no longer fails on manifest trouble. Note the arm is currently UNTESTED (grepped: the string "rollback index regeneration failed" appears only at `:1936` and in no test), so nothing will catch its removal.
  - Depends on: none
  - Expected outcome: after a failed retirement, the shared checkout is byte-identical to before the attempt, INCLUDING the case where the manifests did not exist beforehand (they are absent again, not created); the standing comment at `:2642-2645` no longer contradicts the code; and the fate of the fail-loud arm is stated rather than left implicit.
  - Execution state: performed
  - MECHANISM DEVIATION, RECORDED AS DECISION `07-4xt6u4-D1` AND FLAGGED FOR HUMAN REVIEW. The acceptance property is met EXACTLY as this item states it; the MECHANISM differs from the one the bullets prescribe, because the repository changed between review (2026-09-13) and execution (2026-09-16): Order 04 (`u23gbn`) LANDED (`82922f5c`, finalized `c146cdb3`), moving the transaction's mutations into a coordinator-owned worktree. THE DECISIVE NEW MEASUREMENT, taken at HEAD `daa48f42` across all three pre-commit fault points x both prior-state cases (6 scenarios): at the instant `_rollback_precommit` is ENTERED, the shared manifests are STILL byte-identical to their pre-attempt state in EVERY case (absent stays absent; present stays byte-identical). It holds structurally, for two independent reasons: the mutations happen in a WORKTREE, and the manifests are GITIGNORED so a fresh worktree never receives them and a regeneration there is discarded with it. Verified by spying `plans_index.run_index` during a faulted retirement: exactly TWO calls, BOTH from `_rollback_precommit` -> `_refresh_plans_index_fail_loud`, and NONE from the mutating phase. CONSEQUENCE: step 4 was the SOLE CREATOR of the residue it is blamed for, so "restore the prior state" and "do not write at all" have the SAME postcondition, and the second needs no journal keys, no three-state absent/present value and no delete-to-restore. So the fix REMOVES the regeneration instead of adding a restore. Two further reasons this is strictly better, both measured: (a) a journal content snapshot of this repo's real manifests is 204,275 bytes (INDEX.json 191,641 + INDEX.md 12,634, 648 plans) rewritten on each of the journal's >=5 phase transitions, ~1.0 MiB of I/O per transition to describe a gitignored generated view; and (b) PRE-FIX the regeneration CLOBBERED a peer's concurrent manifest write (measured: peer bytes `{"peer": "wrote this during the window"}` replaced by regenerated content), whereas a restore-from-journal would ALSO have overwritten them, or would have had to REFUSE with `unknown-outcome` and thereby wedge an otherwise clean rollback over a regenerable file. Not writing leaves the peer's bytes intact AND lets the rollback succeed.
  - F-6 DISCHARGED, BY MAKING THE COMMENT TRUE RATHER THAN BY REINSTATING THE KEYS. The standing comment (now at `ipd_lifecycle.py:3250`) said the journal "deliberately carries no `index_json_before`/`index_md_before` content snapshot" because such keys would be "dead weight describing a restore that never happened". Since this fix adds no restore, that statement stays TRUE; leaving it unchanged would nonetheless have stranded a comment whose REASON had changed, so it was rewritten to say the keys are still not needed, why the reason changed, and precisely WHEN a snapshot WOULD become correct (only if the pre-commit phase ever writes the shared manifests). The original key names are quoted so the history remains searchable.
  - F-8 ANSWERED EXPLICITLY (decision `07-4xt6u4-D2`): the fail-loud arm is DROPPED on the rollback path, and the code says so. `_refresh_plans_index_fail_loud` is no longer called from `_rollback_precommit`, so `(False, "rollback index regeneration failed: ...")` is gone with its subject. Reasons: the arm was UNTESTED (`grep -rn "rollback index regeneration failed" tests/` returned nothing); it made the LAST-RESORT path fail over a GITIGNORED GENERATED VIEW, escalating the journal to `PHASE_UNKNOWN_OUTCOME`, which is operator-blocking; and an absent manifest is only `check.stale-index-missing` at severity `info` (`check_engine.py:333-335`). The SUCCESS path's fail-loud refresh is UNTOUCHED (still after the reconciliation, still raising), so `ROLLUP_SHARED_GATES`'s `plans-index-refresh-fail-loud` still names a live gate and no gate parity is weakened. The rollback's own arms that protect REAL content (destination changed, origin holds a peer's content, cannot remove/restore) are unaffected and still report `unknown-outcome`; one of them is now pinned by a test.
  - EARLY WARNING ADDED so the deviation cannot rot silently: `_pre_commit_phase_leaves_manifests_untouched()` states the invariant the fix rests on, as a named and testable claim, and `test_the_invariant_the_fix_RESTS_on_is_stated_and_holds` verifies it across all six scenarios. If a future change makes the pre-commit phase write the shared manifests, that test FAILS FIRST and its message names the journal-snapshot mechanism as the one that then becomes correct.

### Task group 2: pin it where it broke

- [x] E-02 Add the assertion the existing fault tests lack, to the test that already exercises the failure. `tests/test_orchestrator_retirement.py:1961-1972` asserts the plan is restored to `pending/`, that its bytes match, that the `executed/` destination is gone, and that HEAD is unmoved, but it never asserts THE TREE IS CLEAN, which is exactly why the residue went unnoticed. Add a `git status --porcelain` comparison to the existing `after_move` case, rather than writing a parallel test, so the property is pinned at the site where the failure actually occurs. DEMONSTRATE THE ASSERTION IS REAL: show it FAILING against the pre-fix behavior (the measured `?? INDEX.json` / `?? INDEX.md`) before the fix is applied, so the test is proven to detect the bug rather than merely passing afterwards.
  - THE SECOND ASSERTION SITE IS WRONG AND IS REMOVED AT REVIEW (PR-602, F-9). This item originally also said to add "a `git status --porcelain` emptiness assertion ... to the `before_commit` case at `:1984`". That test is `test_a_stale_pre_commit_journal_is_ROLLED_BACK_before_a_fresh_attempt`, and its LAST act is a SUCCESSFUL retirement (`second = self.retire(orch, "recov", apply=True)`, asserted `EXIT_OK`), because its subject is crash RECOVERY, not rollback cleanliness. A successful retirement legitimately regenerates the manifests, so the tree is NOT empty when that test ends. MEASURED at review by sampling `git status --porcelain` at all three points of that test's own sequence: `''` before anything, then `?? INDEX.json` + `?? INDEX.md` after the failed attempt, then the SAME two entries after the successful retry. So an emptiness assertion at the end of that test would assert a FALSE property and fail even with E-01 correctly implemented. If a cleanliness assertion is wanted in that test at all, it belongs at the MIDPOINT (after `first`, before `second`), and it must then be the same before/after comparison used in the `after_move` case, not an emptiness claim.
  - ASSERT EQUALITY TO THE PRE-ATTEMPT STATUS, NOT EMPTINESS, for the same reason the sibling Order 04 review established for its own regression: emptiness happens to hold in this fixture (verified: the tree is `''` before the attempt) but it is the wrong property, because it would also pass if the assertion destroyed unrelated state, and it would break the moment a fixture legitimately carries dirt. Capture `git status --porcelain` before the retirement and assert the post-rollback value EQUALS it.
  - Depends on: E-01
  - Expected outcome: the suite fails if a failed retirement leaves any residue, the assertion compares against the pre-attempt status rather than asserting emptiness, the test is proven to detect the original defect, and no assertion is placed where a successful retirement makes it false.
  - Execution state: performed
  - DONE AT THE PRESCRIBED SITE: `test_an_injected_pre_commit_FAULT_rolls_the_rollup_back` (the `after_move` case) now captures `git status --porcelain` before the retirement and asserts the post-rollback value EQUALS it, rather than asserting `""`. PROVEN TO DETECT THE DEFECT: with the product code reverted (`git stash push -- agent_workflows/ipd_lifecycle.py`) and the new tests in place, it FAILED with `AssertionError: '?? .aw/records/plans/INDEX.json\n?? .aw/records/plans/INDEX.md\n' != ''`.
  - THE MIDPOINT ASSERTION WAS ADDED TO THE `before_commit` RECOVERY TEST AFTER ALL, at the position F-9 identified as the only correct one, because post-fix it is now measurably TRUE. F-9's finding is confirmed and is why it is NOT at the end: sampled at all three points of that test's sequence post-fix, `''` before anything, `''` after the failed attempt, and `?? INDEX.json` + `?? INDEX.md` after the SUCCESSFUL retry. So an emptiness (or equality) assertion at the END would still be false; the comparison sits BETWEEN the two retirements, where the subject is the rollback, and it too is an equality against the captured pre-attempt status. It also fails against the pre-fix code (`'?? ...INDEX.json\n?? ...INDEX.md\n' != ''`), so it is a real assertion and not decoration.
  - FIVE FURTHER TESTS PIN WHAT THE PORCELAIN CHECK STRUCTURALLY CANNOT SEE, in the new class `AFailedRetirementLeavesTheManifestsAsItFoundThem`. The reason they are necessary: the manifests are GITIGNORED in the real repository, so `git status --porcelain` there reports NOTHING whether they were created or not (they show as `??` in the fixture only because its `.gitignore` carries `.aw/state/` alone), which means a porcelain-only assertion can be satisfied by a file being INVISIBLE rather than ABSENT. The tests check EXISTENCE and bytes directly: manifests ABSENT beforehand are absent after (the measured defect) with `aw index plans --check` rc=0; manifests PRESENT beforehand are byte-identical after with rc=0 (guarding what the old code got right by accident); a PEER's mid-window manifest write is NOT clobbered; the rollback does not call the refresh AT ALL (pinned as an observed absence of writes, because byte-equality alone cannot distinguish "never written" from "written with identical bytes", and it was the WRITE that produced the defect); the SUCCESS path still regenerates correctly; the rollback STILL fails honestly for a REAL cause; and the invariant E-01 rests on holds across all six scenarios. Four of these seven also fail against the pre-fix code.

## Project conventions discovered (Step 0)

- The finalize transaction is journalled with explicit phases (`PHASE_PREPARED` -> `PHASE_MUTATING` -> `PHASE_READY_TO_COMMIT` -> `PHASE_COMMITTED_INCOMPLETE`/`PHASE_COMPLETE`, `:132-147`), and `_rollback_precommit` is driven entirely by that journal. Anything the rollback must restore has to be RECORDED in the journal first; that is the existing pattern for `original_bytes` and `git_index_entries`, and it is the pattern this fix follows.
- The rollback deliberately refuses a destructive restore when a concurrent writer changed a path since the checkpoint, classifying it `unknown-outcome` instead. That fail-closed posture is load-bearing in a shared checkout and must extend to the index files.
- The index manifests are GITIGNORED in this repository (`.aw/.gitignore:45-46`, verified with `git check-ignore`), not merely untracked. That is a stronger statement than "untracked" and it lowers the severity further: the clean-base check excludes untracked paths, and a gitignored path is additionally invisible to a normal `git status`. The measured residue was observed with an explicit porcelain call in a test fixture, not in a run. The defect is real (a rollback that claims to restore does not) but it is a correctness defect, not an outage risk in this repository.

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | A failed retirement leaves the shared checkout altered. Measured with `fault_injection="after_move"`: tree before was EMPTY; after the failure it held `?? .aw/records/plans/INDEX.json` and `?? .aw/records/plans/INDEX.md`, while the plan itself was correctly restored and HEAD unmoved. INDEPENDENTLY REPRODUCED AT REVIEW at HEAD `54b6f7ce`, values identical: exit code 2, message "fault-injected finalize failure (after_move); rolled back to pre-finalize state.", status before `''` and after `'?? .aw/records/plans/INDEX.json\n?? .aw/records/plans/INDEX.md\n'`, plan restored True, destination gone True, HEAD unmoved True. So the plan's central measurement is sound and is not merely inherited. READ THIS ROW WITH F-7, which measures that the residue appears only because the fixture began with NO manifests; the same fault against a tree that already has them leaves them byte-identical. | reproduced through the repository's own test harness during the session that authored Order 04; re-reproduced at review by patching nothing and driving `retire_orchestrator(apply=True, fault_injection="after_move")` in the repo's own fixture |
| F-2 | The existing fault tests cannot catch it. They assert plan restoration, destination removal and HEAD, and never tree cleanliness. | `tests/test_orchestrator_retirement.py:1961-1972` |
| F-3 | The cause is in the rollback, not the mutation: step 4 regenerates the index from the current corpus rather than restoring its prior state. | `_rollback_precommit` docstring and body (`ipd_lifecycle.py:1874-1925`) |
| F-4 | Severity is low but real, and LOWER than first stated. The manifests are GITIGNORED, not merely untracked: `.aw/.gitignore:45-46` lists both, confirmed with `git check-ignore -v` (rc=0). So they are invisible to a normal `git status`, the clean-base check would not see them even if it included untracked paths, and no run has been observed to fail because of this residue. It is a correctness defect in a rollback that claims to restore, not an outage risk. | `.aw/.gitignore:45-46`; `git check-ignore -v` on both paths returns rc=0 |
| F-6 | THE PRESCRIBED FIX REINSTATES TWO JOURNAL KEYS THAT WERE DELIBERATELY DELETED, AND A STANDING COMMENT FORBIDS THEM. FOUND AT REVIEW. `_finalize_transaction` carries an explicit note (`:2642-2645`): "the journal deliberately carries no `index_json_before`/`index_md_before` content snapshot. Those keys existed to restore the plans manifests on rollback, but NOTHING ever read them (rollback regenerates the manifests from the corpus instead, in step 4 of `_rollback_precommit`), so they were dead weight describing a restore that never happened." The removal was commit `674f2c68` (2026-09-07, "stop committing the generated index manifests"), which lists it among nine deliberate contributor removals and describes it as "a content-restore no code performs". So E-01 as authored re-adds exactly what that comment tells the next reader not to add, and the comment becomes FALSE on landing. The fix is still right; what was missing is the obligation to update that comment in the same change and to reuse the original key names so the history reads as a reinstatement. Note nothing pins the journal's key set (grepped: neither key name appears in any test), so no test would catch the contradiction. | `agent_workflows/ipd_lifecycle.py:2642-2645`; `git log -S index_json_before` -> `674f2c68`, whose message names the removal; `grep -rn "index_json_before\|index_md_before" tests/` returns nothing |
| F-7 | THE DEFECT IS NARROWER THAN THE PLAN'S FRAMING: REGENERATION IS BYTE-EXACT WHEN THE MANIFESTS ALREADY EXIST, SO THE ONLY REAL CASE IS CREATE-WHERE-ABSENT. FOUND AT REVIEW BY MEASUREMENT. Generating the manifests first (as a real repository has them), then driving an `after_move` fault, then comparing: `INDEX.json` was BYTE-IDENTICAL before and after, and both copies correctly named the plan's `pending/` path. So by the time step 4 runs the corpus is already restored and the deterministic generator reproduces the prior bytes exactly; restore-from-journal and regenerate-from-corpus agree in that case. They differ ONLY when the manifests did not exist beforehand, where regeneration CREATES them, which is precisely the measured `?? INDEX.json` / `?? INDEX.md`. CONSEQUENCE: OQ-01's resolution hedged that regeneration matches "only if the corpus is byte-identical AND the generator is deterministic"; both conditions measured TRUE. The Concern, Goal and F-1 all present the residue as the general shape of the bug, which overstates it, and the fix must therefore make "absent" a restorable state rather than merely snapshotting bytes. Restoring absent is safe: an absent manifest is `check.stale-index-missing` at severity `info` (`check_engine.py:333-335`) and verified `aw index plans --check` returns rc=0 with both absent. | measured at review in the repository's own fixture: pre-generated manifests, `fault_injection="after_move"`, byte comparison identical; separately `plans_index.check_drift` with both manifests absent -> two `check.stale-index-missing` findings at `info`, `run_index(check=True)` rc=0 |
| F-8 | REPLACING STEP 4's REGENERATION SILENTLY DROPS A FAIL-LOUD ARM, AND THAT ARM IS UNTESTED. FOUND AT REVIEW. Step 4 calls `_refresh_plans_index_fail_loud` (`:1656-1695`), which regenerates AND re-runs `--check` and RAISES on non-convergence; the rollback converts that raise into `(False, "rollback index regeneration failed: ...")` at `:1936`, which is what makes a rollback report failure rather than a false success. If regeneration becomes a restore, the verification has no subject and the arm disappears. The plan does not mention it. Nothing will catch the removal either: the string appears only at `:1936` and in no test. Addressed by an added E-01 bullet requiring the fate of the arm be stated. | `agent_workflows/ipd_lifecycle.py:1932-1936` and `:1656-1695`; `grep -rn "rollback index regeneration failed" tests/` returns nothing |
| F-9 | E-02's SECOND ASSERTION SITE WOULD PIN A FALSE PROPERTY. FOUND AT REVIEW. E-02 said to add a `git status --porcelain` EMPTINESS assertion to "the `before_commit` case at `:1984`". That test is `test_a_stale_pre_commit_journal_is_ROLLED_BACK_before_a_fresh_attempt`, whose subject is crash RECOVERY and whose last act is a SUCCESSFUL retirement asserted `EXIT_OK`. A successful retirement legitimately regenerates the manifests, so the tree is not empty when it ends. MEASURED at all three points of that test's own sequence: `''` before anything, `?? INDEX.json` + `?? INDEX.md` after the failed first attempt, and the SAME two entries after the successful retry. So the assertion would fail even with E-01 correctly implemented. E-02 corrected to drop that site and, if a check is wanted there at all, to place it at the midpoint as a before/after comparison. | measured at review by sampling `git status --porcelain` before, between and after the two retirements in that test's sequence |
| F-5 | This fix is INDEPENDENT of the worktree relocation. `/plan-review` established that Order 04's E-03 and E-04 are not gated by its blocking OQ-03, which is why they are carved here. | Order 04 (`u23gbn`) OQ-03: "E-03 and E-04 are NOT gated and may be executed on their own" |

## Proposed changes (ordered, validatable)

1. Record the index manifests' prior state in the journal (reinstating `index_json_before` / `index_md_before` and updating the standing comment that currently forbids them, per F-6) and restore it on the rollback path, including restoring ABSENCE (F-7), preserving the `unknown-outcome` refusal for a concurrent change, and stating the fate of the fail-loud arm (F-8) (E-01).
2. Add a tree-state assertion to the ONE existing fault-injection test whose subject is the rollback, comparing against the pre-attempt status rather than asserting emptiness, and proven to fail against the pre-fix behavior (E-02). NOT to the `:1984` recovery test, which ends on a successful retirement and where an emptiness assertion would be false (F-9).

## Deferred / out of scope (with reason)

- Relocating the retirement mutations into a coordinator-owned worktree. That is Order 04 (`u23gbn`) and is gated on its blocking OQ-03, which asks whether the change belongs in the SHARED `_finalize_transaction` (two callers, reaching every plan's terminal transition) or in a forked rollup-specific body. This plan needs no answer to that question.
- Making the index manifests tracked, or changing how they are generated. Out of scope; only the rollback path's behavior is wrong.
- The success path's regeneration. Correct as it stands: a successful retirement really does change the corpus.

## Scope check

- Over-scope: none. Two files, one rollback path, one existing test extended (was "two existing tests"; F-9 removes the second site).
- Under-scope: this plan fixes the index manifests specifically, and does not audit `_rollback_precommit` for other paths it may write rather than restore. If review wants that audit it should be its own plan; state so rather than widening this one. REVIEW'S ANSWER: it should be its own plan, and it is NOT widened here. But one instance is worth naming because a sibling plan already depends on it: `_rollback_precommit` step 2 (`:1910-1920`) writes `original_bytes` over `original_path` UNCONDITIONALLY, guarded by nothing, while step 1 does guard the destination against `moved_bytes`. That is correct TODAY only because this transaction is the party that moved the file away. Order 04 (`u23gbn`) E-08 now owns making that write safe, because Order 04's relocation is what turns it into an overwrite of a peer's edit. Recorded here so the two plans do not both edit that function blindly: this plan touches step 4 only, Order 04 touches step 2 only, and both declare `agent_workflows/ipd_lifecycle.py`.
- SEQUENCING NOTE WITH ORDER 04, added at review. Both plans modify `_rollback_precommit`. This plan is UNGATED and Order 04 is gated on two blocking questions (its OQ-03 answered, its OQ-04 open), so this plan will almost certainly land first. That is the right order: it is the smaller change, it fixes a measured defect, and Order 04's E-08 is written against the function as it stands. If this plan lands first, Order 04's executor should re-read step 4 before assuming the shape its plan describes.

## Required tests / validation

- The `after_move` fault case extended with a tree-STATE assertion (equality to the pre-attempt `git status --porcelain`, not emptiness), passing. CORRECTED AT REVIEW: this line previously required the assertion in BOTH fault cases; F-9 measures that the `:1984` `before_commit` test ends on a SUCCESSFUL retirement, so an emptiness assertion there is false. If that test gains a check at all it belongs at the midpoint, as a comparison.
- The new assertion demonstrated FAILING against the pre-fix behavior, so it is proven to detect the defect.
- BOTH PRIOR-STATE CASES, since F-7 shows only one of them is actually broken and a test covering only the broken one would not prove the fix is safe: (a) manifests ABSENT before the attempt (the measured defect; they must be absent again afterwards, not created), and (b) manifests PRESENT before the attempt (they must be byte-identical afterwards, which the pre-fix code already achieves, so this case guards against the fix REGRESSING it).
- `aw index plans --check` clean after a failed retirement in BOTH prior-state cases, proving that restoring absence does not leave the repository in a state its own gate rejects. Verified at review that absent manifests are `check.stale-index-missing` at `info` and return rc=0, so this should pass; paste it rather than assuming.
- A concurrent-change case: if the index manifests changed since the checkpoint, the rollback refuses a destructive restore and classifies `unknown-outcome` rather than clobbering them.
- A successful retirement still regenerates the index correctly (the success path is unchanged).
- WHATEVER REPLACES THE FAIL-LOUD ARM (F-8), exercised. If a post-restore check is kept, show it failing on a genuine inconsistency; if the arm is dropped, state that a rollback no longer fails on manifest trouble and show the rollback still reports honestly. The arm is currently untested, so its behavior after this change must be pinned rather than assumed.
- Full suite run bare, with the failure set diffed against a baseline from the same commit; paste both counts and the diff.

## Spec / documentation sync

- No spec amendment expected, and this was VERIFIED AT REVIEW rather than left as an instruction: grepping spec `77tr3o` for `rollback` and `restore` returns NO hits, so no requirement speaks to rollback completeness and none is contradicted by this change. R-4/R-5/R-6 govern what the transition MEANS. Do not add the spec file to `Scope-Paths`.
- Update `_rollback_precommit`'s docstring, which currently says it "regenerates the plans index from the CURRENT corpus" as a description of correct behavior.
- ALSO UPDATE THE STANDING COMMENT AT `ipd_lifecycle.py:2642-2645` (F-6), which is a second and more dangerous piece of stale documentation than the docstring: it states that the journal "deliberately carries no `index_json_before`/`index_md_before` content snapshot" because such keys would be "dead weight describing a restore that never happened". This fix makes that restore happen, so the comment becomes false and, left in place, actively instructs the next reader to undo this change. It must say the keys are back and that they are now READ.

## Open questions

### OQ-01: Restore the index manifests from the journal, or regenerate them from the restored corpus?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED at authoring from the requirement itself, so no human decision is needed. The acceptance property is observable and stated in E-01: after a failure the tree must be byte-identical to before the attempt. RESTORING FROM THE JOURNAL satisfies that directly. Regenerating from the restored corpus would usually produce the same bytes, but only if the corpus is byte-identical AND the generator is deterministic, and it would still CREATE the files in a tree where they may not have existed at all before the attempt, which is exactly the observed defect. So restore, and record the prior state (including "absent") in the journal. Non-blocking and resolved because the plan's own acceptance criterion decides it; recorded so the implementer does not re-open it.
  CONFIRMED AT REVIEW, AND THE HEDGE IS NOW MEASURED RATHER THAN ASSUMED (F-7). The two conditions this rationale hedges on were both tested and both hold: with the manifests pre-generated, an `after_move` fault left `INDEX.json` BYTE-IDENTICAL to its pre-attempt content, so the corpus IS restored by the time step 4 runs and the generator IS deterministic. That STRENGTHENS the conclusion rather than weakening it, but it also relocates the whole defect: since regeneration and restore agree whenever the manifests already exist, the ONLY case the fix actually changes is create-where-absent. So the decisive half of this resolution is the clause about creating files "in a tree where they may not have existed at all", and the implementable requirement is that the journal record ABSENCE as a first-class prior state and the rollback be able to restore it by deleting. Restoring absence was verified safe: an absent manifest is `check.stale-index-missing` at `info` (`check_engine.py:333-335`) and `aw index plans --check` returns rc=0 with both absent.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste `git status --porcelain` immediately BEFORE and immediately AFTER a `fault_injection="after_move"` retirement, and show them EQUAL. The pre-fix measurement showed `?? .aw/records/plans/INDEX.json` and `?? .aw/records/plans/INDEX.md` where before was `''`; the after must show neither. Also paste the concurrent-change case showing `unknown-outcome` and no destructive restore, and a successful retirement showing the index still regenerated.
  - PASTE BOTH PRIOR-STATE CASES, per F-7, because a single case cannot distinguish the fix from the bug. (a) MANIFESTS ABSENT beforehand: after the failed retirement they must be ABSENT again, so show the files do not exist rather than only that porcelain is empty (they are gitignored, so an emptiness check alone cannot tell created-and-ignored from absent -- and note the fixture's `.gitignore` does NOT carry the manifest rules, which is why they show as `??` there at all). (b) MANIFESTS PRESENT beforehand: paste the byte comparison showing them unchanged, which is the case the pre-fix code already handled and which this fix must not regress.
  - PASTE `aw index plans --check` after the failed retirement in BOTH cases, showing it clean, so restoring absence is proven not to leave the repository in a state its own gate rejects.
  - STATE AND SHOW THE FATE OF THE FAIL-LOUD ARM (F-8): quote the code that replaced step 4's `_refresh_plans_index_fail_loud` call and say whether a verification survives. If one does, paste it failing on a genuine inconsistency; if not, paste the rollback still reporting failure honestly for some other cause, and say plainly that manifest trouble no longer fails a rollback.
  - PASTE THE UPDATED COMMENT AT `:2642-2645` (F-6), showing it no longer says the journal deliberately carries no such keys, since the fix makes that statement false.
  - Observed evidence: VERIFIED. Both prior-state cases show `git status --porcelain` EQUAL before/after a faulted retirement, with the ABSENT case (the measured defect) now leaving both manifests genuinely non-existent where pre-fix it created them; `aw index plans --check` returns rc=0 in both cases; a peer's mid-window manifest write survives verbatim where pre-fix it was clobbered; a successful retirement still regenerates the index; the rollback-path fail-loud arm is dropped by decision `07-4xt6u4-D2` with the success-path gate untouched and the rollback still failing honestly for a real cause; and the standing comment plus the docstring are updated. All six items pasted below.

    (1) BOTH PRIOR-STATE CASES, driven through the repository's own fixture with `fault_injection="after_move"`, POST-FIX. `status BEFORE`/`status AFTER` are `git status --porcelain` in the shared tree; the digests are sha256 prefixes of each manifest, with `ABSENT` meaning the file does not exist (so ABSENT is distinguishable from PRESENT, per F-7):

    ```text
    --- prior state: manifests ABSENT ---
    exit: 2
    msg: fault-injected finalize failure (after_move); rolled back to pre-finalize state.
    status BEFORE: ''
    status AFTER : ''
    equal: True
    INDEX.json/INDEX.md before: ('ABSENT', 'ABSENT')
    INDEX.json/INDEX.md after : ('ABSENT', 'ABSENT')
    plan restored: True

    --- prior state: manifests PRESENT ---
    exit: 2
    msg: fault-injected finalize failure (after_move); rolled back to pre-finalize state.
    status BEFORE: '?? .aw/records/plans/INDEX.json\n?? .aw/records/plans/INDEX.md\n'
    status AFTER : '?? .aw/records/plans/INDEX.json\n?? .aw/records/plans/INDEX.md\n'
    equal: True
    INDEX.json/INDEX.md before: ('67e4003e1a074805', '2dfb45a20809ccb0')
    INDEX.json/INDEX.md after : ('67e4003e1a074805', '2dfb45a20809ccb0')
    plan restored: True
    ```

    The ABSENT case is the measured defect and is FIXED: before was `''` and after is `''`, where the PRE-FIX run at this same HEAD produced `'?? .aw/records/plans/INDEX.json\n?? .aw/records/plans/INDEX.md\n'` (reproduced first, see the run under V-02). The PRESENT case is byte-identical, so the fix does not regress what the old code got right. Note the ABSENT case shows the files DO NOT EXIST (`ABSENT`, not merely absent-from-porcelain), which is the check F-7 demands because a gitignored file could otherwise be created and invisible.

    (2) `aw index plans --check` AFTER the failed retirement, in BOTH cases, showing rc=0:

    ```text
    === manifests ABSENT beforehand; retire rc=2
        INDEX.json exists after: False   INDEX.md exists after: False
        aw index plans --check -> rc=INDEX.json: check.stale-index-missing: INDEX.json has not been generated; run 'aw index plans'
    INDEX.md: check.stale-index-missing: INDEX.md has not been generated; run 'aw index plans'
    0
    === manifests PRESENT beforehand; retire rc=2
        INDEX.json exists after: True   INDEX.md exists after: True
        aw index plans --check -> rc=plans index --check: clean
        0
    ```

    So leaving the manifests ABSENT does not leave the repository in a state its own gate rejects: the two findings are `check.stale-index-missing`, registered at severity `info` (`check_engine.py:333-335`), and the exit code is 0.

    (3) THE CONCURRENT-CHANGE CASE, showing no destructive write. A peer writes `INDEX.json` inside the transaction window (after the checkpoint, immediately before the rollback runs):

    ```text
    peer wrote INDEX.json just before rollback
    rc: 2
    msg: fault-injected finalize failure (after_move); rolled back to pre-finalize state.
    peer bytes SURVIVED: True
    INDEX.json now: {"peer": "wrote this during the window"}
    ```

    PRE-FIX the identical scenario reported `peer bytes SURVIVED: False` with the peer's content replaced by regenerated manifest JSON. This is an IMPROVEMENT over the mechanism the plan prescribed, not merely a preservation of the status quo: a restore-from-journal would have overwritten these bytes too, or would have had to REFUSE (`unknown-outcome`) and wedge an otherwise clean rollback over a regenerable generated view. Pinned by `test_a_PEERS_manifest_write_inside_the_window_is_NOT_clobbered`.

    (4) A SUCCESSFUL RETIREMENT STILL REGENERATES THE INDEX (the success path is untouched), pinned by `test_the_SUCCESS_path_still_regenerates_the_index`, which asserts the manifest names the `executed/` path, does NOT name the `pending/` path, and that `--check` is rc=0. It passes, and the pre-existing class `TheIndexGateIsStillLiveUnderTheNewOrdering` (4 tests, including the ordering and genuine-non-convergence gates) also still passes:

    ```text
    tests/test_orchestrator_retirement.py::AFailedRetirementLeavesTheManifestsAsItFoundThem::test_the_SUCCESS_path_still_regenerates_the_index PASSED
    18 passed, 119 deselected in 2.13s
    ```

    (5) THE FATE OF THE FAIL-LOUD ARM (F-8): the arm is DROPPED on the rollback path, deliberately, and manifest trouble NO LONGER FAILS A ROLLBACK. Step 4's `_refresh_plans_index_fail_loud` call and its `except` arm are replaced by no write at all:

    ```python
        # 4. The plans manifests are DELIBERATELY NOT TOUCHED. See this function's docstring for the
        #    measurement: nothing in the pre-commit phase writes the shared `INDEX.json`/`INDEX.md`, so
        #    they are already in their pre-attempt state by the time we get here, and regenerating them
        #    (which is what this step used to do) is the ONLY thing that made a failed transition leave
        #    `?? INDEX.json` / `?? INDEX.md` behind in a tree that had none. Do not "helpfully" restore
        #    the refresh here: a rollback that writes a generated view cannot leave the tree as it found
        #    it, and on the ABSENT path it cannot even tell created-and-ignored from never-existed.
        #    The success path's fail-loud refresh is the one that matters and is untouched.
        return (
            True,
            "pre-commit state restored (plan bytes/path + owned Git-index; plans manifests left "
            "untouched, so the tree is as it was found).",
        )
    ```

    NO verification survives on the rollback path, and that is the recorded decision (`07-4xt6u4-D2`), for three reasons: the arm was UNTESTED (`grep -rn "rollback index regeneration failed" tests/` returned nothing); it made the LAST-RESORT path fail over a gitignored generated view, escalating the journal to `PHASE_UNKNOWN_OUTCOME`, which blocks an operator; and the SUCCESS path's fail-loud gate is untouched, so `ROLLUP_SHARED_GATES`'s `plans-index-refresh-fail-loud` still names a live gate. As required, here is the rollback STILL REPORTING FAILURE HONESTLY for a real cause (a concurrent destination change), from `test_the_rollback_STILL_reports_failure_honestly_for_a_REAL_cause`, which asserts `ok is False`, `"unknown-outcome" in msg`, and that the peer's destination bytes are intact:

    ```text
    tests/test_orchestrator_retirement.py::AFailedRetirementLeavesTheManifestsAsItFoundThem::test_the_rollback_STILL_reports_failure_honestly_for_a_REAL_cause PASSED
    ```

    (6) THE UPDATED STANDING COMMENT (F-6), now at `agent_workflows/ipd_lifecycle.py:3250`. NOTE THE DIVERGENCE FROM WHAT THIS BULLET ANTICIPATED: it expected the comment to stop saying the journal carries no such keys, because the prescribed fix would have made that FALSE. Since the implemented fix adds no restore, the statement remains TRUE, so the comment still says it -- but its REASON changed, so it was rewritten to record the new reason and to state exactly when a snapshot WOULD become correct, rather than being left as a comment whose justification had silently expired:

    ```python
        # NOTE: the journal deliberately carries no `index_json_before`/`index_md_before` content
        # snapshot, and it STILL does not need one after plan `4xt6u4` - but the REASON changed, so read
        # this before reinstating them. Those keys once existed to restore the plans manifests on
        # rollback and nothing read them, because rollback regenerated the manifests from the corpus
        # instead; they were dead weight describing a restore that never happened, and they were removed
        # in `674f2c68`. `4xt6u4` then measured that the REGENERATION was itself the bug: it left
        # `?? INDEX.json` / `?? INDEX.md` in a tree that had none, so a failed transition did not leave
        # the tree as it found it. The fix removed the regeneration rather than adding a restore, because
        # NOTHING in the pre-commit phase writes the shared manifests (they are gitignored and the
        # mutations happen in a coordinator worktree - see
        # `_pre_commit_phase_leaves_manifests_untouched`), so there is nothing to restore and a snapshot
        # would be ~200 KB rewritten on every one of the journal's phase transitions.
        # WHEN A SNAPSHOT WOULD BECOME CORRECT: only if that invariant is broken, i.e. if some future
        # step writes the shared manifests BEFORE the commit. The test pinning the invariant is designed
        # to fail first in that case; do not add the keys back without breaking it.
    ```

    `_rollback_precommit`'s docstring was also updated: it no longer describes regenerating the index as correct behavior, and it now carries the measurement, the reason not-writing is complete, and the plainly-stated consequence that a rollback no longer fails on manifest trouble.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste the extended `after_move` fault test output, and paste the assertion FAILING against the pre-fix behavior (or state precisely why that demonstration is impossible). A test that only passes after the fix is not evidence that it detects the bug. Paste the bare full-suite counts before and after with the FAILED-set diff.
  - CORRECTED AT REVIEW (F-9): this item previously demanded output for "both the `after_move` and `before_commit` cases". The `:1984` `before_commit` test ends on a SUCCESSFUL retirement, so an emptiness assertion there is false and must not be added. If a midpoint comparison was added to that test instead, paste it and state that it samples BETWEEN the two retirements; if it was left alone, say so. Either is acceptable; silently asserting emptiness at its end is not.
  - PASTE THE ASSERTION'S FORM, showing it compares against a captured pre-attempt status rather than asserting `""`. An emptiness assertion happens to pass in this fixture and is the wrong property: it would also pass if the test destroyed unrelated state, and it breaks the moment a fixture legitimately carries dirt.
  - Observed evidence: VERIFIED. The extended `after_move` assertion compares against a CAPTURED pre-attempt status (form pasted below), not `""`; the module passes 137/137; six of the nine assertions are demonstrated FAILING against the pre-fix code with the product file reverted and the new tests in place; the `before_commit` recovery test gained a MIDPOINT comparison (not an end-of-test emptiness claim), per F-9, and it too fails pre-fix; and the bare full-suite comparison is 31 failed/7377 passed baseline -> 31 failed/7384 passed after with an EMPTY FAILED-set diff. All six items pasted below.

    (1) THE ASSERTION'S FORM, in the extended `after_move` test, comparing against a CAPTURED pre-attempt status rather than asserting `""`:

    ```python
            orch = self.make_set("faulty", [("aaa111", 1, "executed", "executed")])
            before = orch.read_text(encoding="utf-8")
            head = _git(self.root, "rev-parse", "HEAD").strip()
            status_before = _git(self.root, "status", "--porcelain")
            res = self.retire(orch, "faulty", apply=True, fault_injection="after_move")
            ...
            self.assertEqual(
                _git(self.root, "status", "--porcelain"),
                status_before,
                "a FAILED retirement changed the shared checkout: the rollback must leave the tree "
                "exactly as it found it (plan 4xt6u4 measured it leaving ?? INDEX.json / ?? INDEX.md "
                "behind, because its step 4 regenerated the manifests instead of not touching them)",
            )
    ```

    (2) THE EXTENDED TEST PASSING, post-fix, together with the whole module:

    ```text
    tests/test_orchestrator_retirement.py::AFailedRetirementLeavesTheManifestsAsItFoundThem::test_a_PEERS_manifest_write_inside_the_window_is_NOT_clobbered PASSED [ 11%]
    tests/test_orchestrator_retirement.py::AFailedRetirementLeavesTheManifestsAsItFoundThem::test_manifests_ABSENT_before_a_failed_retirement_are_ABSENT_after PASSED [ 22%]
    tests/test_orchestrator_retirement.py::AFailedRetirementLeavesTheManifestsAsItFoundThem::test_the_rollback_STILL_reports_failure_honestly_for_a_REAL_cause PASSED [ 33%]
    tests/test_orchestrator_retirement.py::AFailedRetirementLeavesTheManifestsAsItFoundThem::test_manifests_PRESENT_before_a_failed_retirement_are_BYTE_IDENTICAL_after PASSED [ 44%]
    tests/test_orchestrator_retirement.py::AFailedRetirementLeavesTheManifestsAsItFoundThem::test_the_rollback_does_NOT_write_the_shared_manifests_at_all PASSED [ 55%]
    tests/test_orchestrator_retirement.py::AFailedRetirementLeavesTheManifestsAsItFoundThem::test_the_invariant_the_fix_RESTS_on_is_stated_and_holds PASSED [ 66%]
    tests/test_orchestrator_retirement.py::AFailedRetirementLeavesTheManifestsAsItFoundThem::test_the_SUCCESS_path_still_regenerates_the_index PASSED [ 77%]
    tests/test_orchestrator_retirement.py::TheSharedGatesActuallyFireOnTheRollupPath::test_a_stale_pre_commit_journal_is_ROLLED_BACK_before_a_fresh_attempt PASSED [ 88%]
    tests/test_orchestrator_retirement.py::TheSharedGatesActuallyFireOnTheRollupPath::test_an_injected_pre_commit_FAULT_rolls_the_rollup_back PASSED [100%]
    ====================== 9 passed, 128 deselected in 1.50s =======================
    ```

    ```text
    $ python3 -m pytest tests/test_orchestrator_retirement.py -o addopts="" -q
    ........................................................................ [ 52%]
    .................................................................        [100%]
    137 passed in 7.51s
    ```

    (3) THE ASSERTIONS FAILING AGAINST THE PRE-FIX BEHAVIOR, which is what proves they detect the bug. Product code only was reverted (`git stash push -- agent_workflows/ipd_lifecycle.py`), leaving the NEW tests in place:

    ```text
    E       AssertionError: '?? .aw/records/plans/INDEX.json\n?? .aw/records/plans/INDEX.md\n' != ''
    E       - ?? .aw/records/plans/INDEX.json
    E       - ?? .aw/records/plans/INDEX.md
    E        : a FAILED retirement changed the shared checkout: the rollback must leave the tree exactly as it found it (plan 4xt6u4 measured it leaving ?? INDEX.json / ?? INDEX.md behind, because its step 4 regenerated the manifests instead of not touching them)

    FAILED tests/test_orchestrator_retirement.py::AFailedRetirementLeavesTheManifestsAsItFoundThem::test_the_rollback_does_NOT_write_the_shared_manifests_at_all
    FAILED tests/test_orchestrator_retirement.py::AFailedRetirementLeavesTheManifestsAsItFoundThem::test_a_PEERS_manifest_write_inside_the_window_is_NOT_clobbered
    FAILED tests/test_orchestrator_retirement.py::AFailedRetirementLeavesTheManifestsAsItFoundThem::test_manifests_ABSENT_before_a_failed_retirement_are_ABSENT_after
    FAILED tests/test_orchestrator_retirement.py::AFailedRetirementLeavesTheManifestsAsItFoundThem::test_the_invariant_the_fix_RESTS_on_is_stated_and_holds
    FAILED tests/test_orchestrator_retirement.py::TheSharedGatesActuallyFireOnTheRollupPath::test_an_injected_pre_commit_FAULT_rolls_the_rollup_back
    5 failed, 3 passed, 129 deselected in 1.01s
    ```

    The individual pre-fix failure messages, each naming the defect it caught:

    ```text
    E   AssertionError: True is not false : a FAILED retirement CREATED INDEX.json: the rollback regenerated the manifests instead of leaving the tree as it found it (plan 4xt6u4 F-1)
    E   AssertionError: '[\n  {\n    "date": "2026-09-06",\n    "d[473 chars]n]\n' != '{"peer": "wrote this during the window"}\n' : the rollback clobbered a peer's manifest write
    E   AssertionError: Lists differ: ['/tmp/tmpy1elx71g'] != [] : the rollback path refreshed the plans index; step 4 must not write a generated view
    E   AttributeError: module 'agent_workflows.ipd_lifecycle' has no attribute '_pre_commit_phase_leaves_manifests_untouched'
    ```

    (Note the two PRESENT-state tests correctly PASS pre-fix, which is exactly F-7's point: regeneration was already byte-exact in that case, so those two guard against regression rather than detecting the original defect.)

    (4) THE `before_commit` RECOVERY TEST (F-9): a midpoint comparison WAS added, sampling BETWEEN the two retirements, NOT at the end. F-9's measurement is confirmed post-fix at all three points of that test's sequence -- `''` before anything, `''` after the failed attempt, `?? INDEX.json` + `?? INDEX.md` after the SUCCESSFUL retry -- so an assertion at the END would still be false, while the midpoint is now true and is the position whose subject is the rollback. Its form is the same equality against a captured status:

    ```python
            status_before = _git(self.root, "status", "--porcelain")
            first = self.retire(orch, "recov", apply=True, fault_injection="before_commit")
            self.assertEqual(first.exit_code, LC.EXIT_CANNOT_RUN, first.message)
            self.assertTrue(orch.is_file())
            # MIDPOINT: the failed attempt rolled back, so the tree must be as it was found. Sampled HERE
            # and not at the end, because the successful retry below legitimately changes the manifests.
            self.assertEqual(
                _git(self.root, "status", "--porcelain"),
                status_before,
                "the rolled-back first attempt left residue in the shared checkout",
            )
    ```

    It also fails against the pre-fix code, so it is a real assertion:

    ```text
    E       AssertionError: '?? .aw/records/plans/INDEX.json\n?? .aw/records/plans/INDEX.md\n' != ''
    E        : the rolled-back first attempt left residue in the shared checkout
    FAILED tests/test_orchestrator_retirement.py::TheSharedGatesActuallyFireOnTheRollupPath::test_a_stale_pre_commit_journal_is_ROLLED_BACK_before_a_fresh_attempt
    1 failed, 136 deselected in 0.35s
    ```

    (5) BARE FULL-SUITE COUNTS BEFORE AND AFTER, WITH THE FAILED-SET DIFF. The baseline was taken at the SAME commit with both of this plan's files stashed to their HEAD state, so the comparison isolates this change. HONEST STATEMENT UP FRONT: this repository has 31 PRE-EXISTING failures at HEAD `daa48f42`, none of them caused by or related to this plan.

    ```text
    BASELINE (HEAD daa48f42, this plan's two files reverted):
    31 failed, 7377 passed, 3 skipped, 2 xfailed in 83.03s (0:01:23)

    AFTER (this plan's changes applied):
    31 failed, 7384 passed, 3 skipped, 2 xfailed in 82.73s (0:01:22)
    ```

    FAILED-set diff, which is the load-bearing comparison:

    ```text
    $ diff baseline_failed.txt after_failed.txt
    (no differences: identical failure sets)
    ```

    So the failure SET is byte-identical (31 -> 31, same tests) and passes rose by exactly 7, which is the 7 new tests (the extended `after_move` and `before_commit` tests were already counted). The 31 pre-existing failures are concentrated in runner-harness modules that never reference `_rollback_precommit` (`grep -l` over them returns nothing): 10 in `test_runner_backlog_close_in_lane.py`, 9 in `test_oc_runipd.py`, 8 in `test_agy_runipd_cli.py`, 2 in `test_ipd_lifecycle_cli.py`, 1 each in `test_worker_role_refusal.py` and `test_novalnomerge_integration.py`; a sampled one fails with `KeyError: 'main_status_during_turn'`, a harness-key error unrelated to manifests or rollback.

    (6) LINT AND LEAK GATES. `ruff format --check` reports both files formatted; `ruff check` error count on the test file is UNCHANGED at 18 before and after, so this change introduces no new lint findings; `aw sanitize --agent` is clean:

    ```text
    $ python3 -m ruff format --check agent_workflows/ipd_lifecycle.py tests/test_orchestrator_retirement.py
    2 files already formatted

    $ aw sanitize --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one measured defect in one rollback path, plus the assertion that pins it. Carved from Order 04 precisely so it carries no architecture decision.

Execution contract: commit only files this plan changed, path-scoped, never `git add -A`, never push. Paste actual runner output for every test claim. Do not weaken the rollback's `unknown-outcome` refusal in the course of this change.

Post-gate lifecycle move: this plan reaches `executed/` only when every V-item above carries pasted evidence and `aw ipd lint --phase pre-transition` reports conforming.
