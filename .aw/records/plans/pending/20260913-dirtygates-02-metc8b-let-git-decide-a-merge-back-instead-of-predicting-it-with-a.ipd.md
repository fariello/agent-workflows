# IPD: Let git decide a merge-back instead of predicting it with a dirty-overlap heuristic

- Date: 2026-09-13
- Kind: child
- Concern: Integration refuses BEFORE attempting the merge, based on `dirty_tree_overlap` predicting whether the merge would clobber an un-owned edit. The prediction is not equal to git's own precondition, so it can refuse a merge git would accept, and it is redundant where git would refuse anyway. Git's refusal is more accurate, names the offending files, and is provably non-destructive.
  TWO CORRECTIONS FROM REVIEW, BOTH LOAD-BEARING. FIRST, the plan's strongest-sounding evidence was wrong: F-4 claimed the prediction stranded lanes `bzz5e6` and `f6idxs`, and the run records show both were refused by the REAL `git merge` and recorded `merge-conflict`, with the prediction passing them through. The case for this plan therefore rests on F-1/F-5 (divergence in both directions) and simplicity, NOT on measured stranded work; see the corrected F-4 and the new F-4a. SECOND, this plan CONTRADICTS TWO APPROVED, RELEASE-BLOCKING PLANS that a human has signed off: `fujm0y` is approved to WIDEN this function's input set so refusal becomes MORE accurate, and `51vw4y` is approved to build a non-terminal deferral ladder on top of this exact refusal, stating "THE REFUSAL ITSELF IS CORRECT AND MUST SURVIVE". Deleting the symbol negates both. Do NOT execute this plan until the orchestrator's blocking OQ-02 is answered.
- Scope: Remove the pre-merge overlap PREDICTION from `runner_shared.integrate_lane_branch` and let the real `git merge` attempt be the authority, mapping its refusal onto the existing `integration-blocked` outcome. Excludes the pre-launch gate (Order 01), the backlog close (Order 03), orchestrator retirement (Order 04), and the merge-and-revalidate suite run, which is KEPT.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/lane_containment.py, tests/test_runner_shared.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_lane_clean_base.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: no-go
- Set: dirtygates
- Order: 2
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: metc8b
- Priority: high
- Work-Kind: bug

## Workflow history

- 2026-09-13 reviewed (opencode (its_direct/pt3-claude-opus-5-1m-us)): /plan-review round 1: REVIEWED - OPEN QUESTIONS; PR-201..PR-206; five FIXED, PR-201 (BLOCKER) left OPEN and escalated as blocking OQ-03; review record written; Readiness no-go.
- 2026-09-13 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-09-13 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): authored after measuring git's actual behavior in four scratch repositories (see Findings). The maintainer's question "why not just try to merge and let git tell us if it's OK?" is the origin of this plan, and the measurements support it.

## Goal

Stop guessing what `git merge` will do. Attempt it, and treat its own refusal (which names the files and leaves the tree untouched) as the answer.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: let the merge speak

- [ ] E-01 In `runner_shared.integrate_lane_branch`, delete the pre-gate overlap refusal at `:1003-1013` (`overlap = dirty_tree_overlap(repo, lane.changed_files)` and the `integration-blocked` early return). Keep every later step unchanged: the merge-and-revalidate gate call, the `--ff-only` then controlled `--no-ff` sequence, and the abort-on-conflict path. The function's docstring step 0 (`:971-974`) documents the deleted behavior and must be rewritten in the same edit, not left describing a guard that no longer exists.
  GATED ON OQ-03, like E-04: removing the CALL is the same decision as removing the symbol, so do not perform E-01 before OQ-03 is answered. If OQ-03 answers (b) KEEP AND IMPROVE, skip E-01 and proceed directly to E-02, which needs no change to this call site.
  - Depends on: none
  - Expected outcome: integration proceeds to the real merge even when the main tree holds dirty paths that do not conflict.
  - Execution state: pending
- [ ] E-02 Map a REAL git refusal onto the existing `integration-blocked` outcome, preserving the caller contract. NOT GATED ON OQ-03 (F-7): this item touches only the failure branch AFTER the merge attempt, so it is correct and valuable whether or not the prediction is deleted, and its `- Depends on:` is therefore `none` rather than `E-01`. `integrate_lane_branch` returns `(integrated, reason, kind)` with `kind` in `{"integrated", "integration-blocked", "merge-conflict"}` (`:986-988`), and `oc_runipd` branches on exactly those (`:6753-6762`). A refusal caused by local changes ("error: Your local changes to the following files would be overwritten by merge") is NOT a content conflict, so it must land on `integration-blocked` (base contaminated, retry once clean) rather than `merge-conflict` (needs human resolution). The `reason` MUST carry git's own stderr, which already names the files, instead of a re-worded summary.
  THIS IS THE PLAN'S REAL DELIVERABLE, AND IT ALREADY HAS A MEASURED WITNESS, so implement it against that evidence rather than a synthetic case. Today this exact condition is MISCLASSIFIED as `merge-conflict`: lanes `bzz5e6` and `f6idxs` each recorded `status: merge-conflict` with `integration_deferral` = "merge-back conflict; error: Your local changes to the following files would be overwritten by merge: `<backlog path>`. Merge with strategy ort failed." (F-4). Under `51vw4y`'s approved ladder, `merge-conflict` is TERMINAL while `integration-blocked` is deferrable, so this misclassification is exactly what converts a recoverable condition into permanent in-run loss. E-02 therefore delivers value INDEPENDENTLY of E-01/E-04 and is the part of this plan that survives any answer to OQ-03.
  DISTINGUISH BY THE FAILURE MODE, NOT BY STRING-MATCHING GIT'S ENGLISH, because git's message text is localizable and version-dependent. The robust discriminator is measured and available: on a local-changes refusal git NEVER STARTS the merge, so `.git/MERGE_HEAD` is ABSENT and `conflicted_paths` returns `[]`; on a real content conflict `MERGE_HEAD` EXISTS and `conflicted_paths` returns the `U` entries. Verified at review in a scratch repo (main advanced AND dirty on an overlapping path): rc=2, no `MERGE_HEAD`, and `git diff --diff-filter=U` empty. Prefer that structural test; if you also match text, treat it as a secondary hint only and say so in a comment.
  FIX THE UNCONDITIONAL `git merge --abort` WHILE YOU ARE HERE (F-6), because the new branch makes it reachable and wrong. Measured at review: with no merge started, `git merge --abort` exits 128 with "fatal: There is no merge to abort (MERGE_HEAD missing)". Today that return value is discarded so it is silent, but routing this case to a new branch must not carry the pointless abort into it. Abort ONLY when a merge is actually in progress.
  - Depends on: none
  - Expected outcome: the two failure classes stay distinguishable by a structural test rather than by English text, the recorded reason quotes git, and no `git merge --abort` is issued when no merge is in progress.
  - Execution state: pending
- [ ] E-03 Assert the merge attempt is non-destructive on the refusal path. Git aborts and leaves both main and the uncommitted edit intact (F-2), and the existing code already aborts a real conflict "leaving main clean, no markers/partial merge". Verify no new code path can leave a partial merge, and that the lane branch/worktree is still PRESERVED on both failure kinds so the work is recoverable.
  - Depends on: E-02
  - Expected outcome: a refused integration leaves main exactly as found and the lane intact.
  - Execution state: pending

### Task group 2: retire the predicate honestly

- [ ] E-04 DELETE `dirty_tree_overlap` and update every reference (OQ-01, resolved: option (a)). GATED ON OQ-03: this item, and ONLY this item plus E-05, depend on the maintainer confirming DELETE now that the two approved plans are in view. If OQ-03 answers (b) KEEP AND IMPROVE, SKIP E-04 and E-05 and mark them not-performed with that reason; E-01 through E-03 remain valid and deliver this plan's measured value on their own (F-7). Do not begin E-04 before OQ-03 is answered, because its diff spans seven files and would be discarded wholesale by a (b) ruling.
  THE TEST-SITE COUNT IS VERIFIED AND SLIGHTLY LARGER THAN "FIVE": at review, `dirty_tree_overlap(` is CALLED at 10 test sites across three modules (`tests/test_oc_runipd.py:3176`, `:3181`, `:3185`; `tests/test_agy_runipd_cli.py:686`, `:690`, `:693`; `tests/test_lane_clean_base.py:267`, `:270`, `:272`, `:295`) in addition to the identity pins at `tests/test_oc_runipd.py:3197`, `tests/test_agy_runipd_cli.py:704`, `tests/test_runner_shared.py:97`, `:1751`, and `tests/test_lane_clean_base.py:236`. Note `tests/test_lane_clean_base.py:216-247` is `test_dirty_tree_overlap_no_longer_forks_the_parser`, an ANTI-FORK regression from a prior plan: deleting it removes the pin that stopped a per-host copy reappearing, so if the symbol goes, say in the commit message that the anti-fork property went with it rather than dropping it silently. It is re-exported by BOTH hosts (`oc_runipd.py:173`, `agy_runipd.py:176`) and pinned BY IDENTITY in at least five test sites (`tests/test_oc_runipd.py:3197`, `tests/test_agy_runipd_cli.py:704`, `tests/test_runner_shared.py:97` and `:1751`, `tests/test_lane_clean_base.py:236`), so those `assertIs` pins and the behavior tests around them (`tests/test_oc_runipd.py:3168-3185`, `tests/test_agy_runipd_cli.py:681-693`, `tests/test_lane_clean_base.py:216-295`) must be removed or retargeted in this plan, not left dangling. TWO PROSE REFERENCES ALSO BECOME FALSE and must be fixed in the same edit: `lane_containment.py:2571` describes it as the contrasting integration-time check (Order 02's E-05 owns that paragraph), and `wtiso_gate.py:287-296` cites it as EVIDENCE that a shipped refusal exists ("refusal DID land separately (oc_runipd.integrate_lane_branch, dirty_tree_overlap)"), which after this deletion asserts something untrue. `runner_shutdown.py:333` also names it. Do not leave the symbol exported and unused.
  - Depends on: E-01
  - Expected outcome: `grep -rn dirty_tree_overlap` over the repository returns nothing, and no prose claims a refusal that no longer ships.
  - Execution state: pending
- [ ] E-05 Update the cross-references that describe the two dirty checks as a contrasting pair. `lane_containment.evaluate_clean_base`'s docstring (`:2571-2580`) explains at length how it differs from the integration-time overlap check; Order 01 changes that function and this item changes its counterpart, so the paragraph must be rewritten once both are settled rather than left describing a design neither module implements.
  - Depends on: E-01, E-04
  - Expected outcome: the prose in both modules matches the shipped behavior.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The integration implementation is SHARED (`runner_shared.integrate_lane_branch`); each host wraps it only to bind its own `run_checked` and `host_label`. Change the shared function; do not fork it.
- `host_label` has no default deliberately, because it lands in a merge-commit subject on main and a wrong default misattributes history.
- Several tests pin shared symbols BY IDENTITY (`assertIs`) specifically to prevent a second copy appearing per host. Expect those to be the tests that fail first if a symbol is removed.

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | `merge-tree` is NOT a valid predictor of the real merge, so a predict-first design is inherently divergent. Measured: lane changed `a.txt` and `b.txt`, `b.txt` dirty locally; `git merge-tree --write-tree` returned rc=0 ("clean") while the real `git merge` REFUSED. | reproduced in a scratch repo during authoring |
| F-2 | The real merge FAILS SAFELY, which is what makes attempting it acceptable. On refusal it prints `error: Your local changes to the following files would be overwritten by merge: b.txt`, aborts, leaves main clean, and leaves the uncommitted edit intact (verified: the local content survived). | same session |
| F-3 | The real merge SUCCEEDS when dirty paths do not conflict, including the `--no-ff` case after main advanced, preserving the unrelated dirty file. So attempting the merge is strictly more permissive AND strictly more accurate than the prediction. | same session |
| F-4 | CORRECTED AT REVIEW, AND THE CORRECTION MATTERS: the two stranded lanes were NOT stranded by this prediction. Lanes `bzz5e6` and `f6idxs` each finalized verified work and failed to integrate, but both were recorded as `merge-conflict`, not `integration-blocked`, and both `integration_deferral` strings are GIT'S OWN text ("error: Your local changes to the following files would be overwritten by merge: `.aw/records/backlog/graduated/...`. Merge with strategy ort failed."). So the REAL `git merge` is what refused them; `dirty_tree_overlap` returned `[]` and passed them through, because the dirty backlog file was outside each lane's `changed_files`. Read from each run's `state.json` at review, per-item. THE CONSEQUENCE FOR THIS PLAN IS THE OPPOSITE OF WHAT F-4 CLAIMED: attempting the merge is exactly what already happened, and it FAILED here. Deleting the prediction would not have saved these two lanes; it would only have changed their recorded `kind` from `merge-conflict` to `integration-blocked`, which is precisely the reclassification approved plan `fujm0y` exists to deliver by WIDENING the guard rather than deleting it. The $30 recovered by hand (`51cb5d7a`, `50d71d05`) is real and was recovered only after commit `acde2496` committed the straggling deletion, i.e. after the DIRT was cleared, not after any guard changed. | `run-20260913T032416Z-2009920` and `run-20260913T031521Z-1774617` `state.json` per-item `status` and `integration_deferral`; commits `acde2496`, `51cb5d7a`, `50d71d05` |
| F-4a | So the honest case for this plan is NARROWER than F-4 asserted, and rests on F-1/F-5 (the prediction and git can disagree in both directions) plus simplicity, NOT on measured stranded work. No run record in this repository shows a lane stranded by `dirty_tree_overlap`. State that plainly rather than inheriting F-4's original claim, and note the earlier measured incident that DID strand four lanes on this guard (`run-20260905T050043Z-639569`, cited by approved plan `51vw4y`) is the case FOR a recovery ladder, since those four merged clean later. | verified at review: the only `integration-blocked` statuses in the four 2026-09-13 runs are zero; all integration failures that night were `merge-conflict` from real git |
| F-5 | The guard and git can disagree in BOTH directions, which is the general argument against predicting. F-1 shows predict-clean while git refuses; the overlap rule is also narrower than git's precondition, so a dirty path git would object to can pass the overlap test when it is outside `changed_files`. | `runner_shared.dirty_tree_overlap` (`:888-917`) intersects with `changed_files` only |
| F-6 | THE UNCONDITIONAL `git merge --abort` IS WRONG ON THE LOCAL-CHANGES PATH, and E-02 makes that path reachable as its own branch. Measured at review: on a local-changes refusal git never starts the merge, so `.git/MERGE_HEAD` is ABSENT, `git diff --name-only --diff-filter=U` is EMPTY, and `git merge --abort` exits 128 with "fatal: There is no merge to abort (MERGE_HEAD missing)". The existing code calls `conflicted_paths` then `_run_git(repo, ["merge", "--abort"])` unconditionally and DISCARDS the result, so today it fails silently and harmlessly. Two consequences: the `MERGE_HEAD`/empty-`U` pair is the ROBUST structural discriminator E-02 should key on instead of git's localizable English, and the abort must become conditional rather than being inherited into the new branch. | measured in a scratch repo at review (main advanced + overlapping dirty path): rc=2, no `MERGE_HEAD`, empty `--diff-filter=U`, `merge --abort` rc=128; `runner_shared.py:1055-1057` calls abort unconditionally; `conflicted_paths` docstring (`:393-402`) already documents the empty-return case for "a refusal to start" |
| F-7 | E-02 IS SEPARABLE FROM E-01/E-04 AND IS THE PART THAT SURVIVES ANY RULING, which matters because OQ-03 may forbid the deletion. Reclassifying a local-changes refusal from `merge-conflict` to `integration-blocked` requires NO change to `dirty_tree_overlap` and no spec motion: it edits only the failure branch after the merge attempt. It also has the measured witness (F-4) that the deletion lacks (F-4a). Under `51vw4y`'s approved ladder the reclassification is what makes the condition deferrable instead of terminal, so E-02 is complementary to that approved plan rather than in conflict with it. | this plan's E-02 touches only the post-merge branch in `integrate_lane_branch`; `51vw4y` E-01 scopes its ladder to the `integration-blocked` arm only |

## Proposed changes (ordered, validatable)

1. Delete the pre-merge overlap refusal and rewrite the docstring's step 0 (E-01).
2. Map git's own refusal onto `integration-blocked`, carrying git's stderr as the reason (E-02).
3. Confirm non-destructiveness and lane preservation on both failure kinds (E-03).
4. Decide `dirty_tree_overlap`'s fate, delete-or-demote, and update every reference (E-04).
5. Rewrite the paired-cross-reference prose in `lane_containment` (E-05).

## Deferred / out of scope (with reason)

- The merge-and-revalidate suite run is KEPT deliberately. It is the check that does real work: it re-runs validation against the combined result, which is where a genuine stale base surfaces as a test failure rather than a guess. Order 01's F-3/F-4 depend on this remaining in place.
- Using `git merge-tree` as a cheaper pre-check. Rejected by F-1: it answered "clean" where the real merge refused, so it would reintroduce exactly the divergence this plan removes.
- Auto-resolving a genuine content conflict. Out of scope and undesirable; conflict RESOLUTION stays a human/serial ordering, as the existing docstring already states.

## Scope check

- Over-scope: E-04 may touch several test files that are not otherwise part of this change. That breadth is caused by the identity-pinning convention, not by scope creep, and it is unavoidable under option (a). If review prefers a narrower diff, choose option (b). MEASURED AT REVIEW: the breadth is 10 call sites plus 5 identity pins across four test modules, plus two prose sites, so a (b) ruling on OQ-03 removes roughly the whole diff. That is why E-01 and E-04 are now explicitly gated on OQ-03 rather than merely flagged.
- Under-scope: this plan does not add a pre-merge report of dirty paths. Order 01 already reports them at launch, so adding a second report here would duplicate the signal. Say so at review if a merge-time report is wanted.
- SPLIT ADDED AT REVIEW: this plan holds two separable changes, and only one is contested. E-02/E-03 (reclassify a local-changes refusal as `integration-blocked`, prove non-destructiveness) have a MEASURED witness in F-4, need no spec motion, and complement approved plan `51vw4y`. E-01/E-04/E-05 (delete the prediction) rest on F-1/F-5 plus simplicity with no run record behind them (F-4a) and contradict two approved plans. If OQ-03 rules (b), execute the first pair and retire the second as not-performed rather than treating the whole plan as blocked.

## Required tests / validation

- A test proving integration SUCCEEDS with a dirty tracked path in main that does not conflict with the lane's changes. This is the direct regression for F-4.
- A test proving integration is refused, recorded as `integration-blocked`, with git's own message in the reason, when a dirty path DOES conflict; and proving main and the local edit are untouched afterwards.
- A test proving a genuine content conflict still yields `merge-conflict` and a preserved lane, so the two classes remain distinguishable.
- Both hosts exercised, since both re-export the symbol and both branch on `kind`.
- The full suite run bare, with the failure set compared against a baseline from the same commit; paste both counts and the FAILED-set diff.

## Spec / documentation sync

- No spec requirement mandates the pre-merge overlap prediction, so no spec amendment is expected. VERIFY THIS BEFORE EXECUTING: search the specs tree for the requirement behind `driverfin-03 (7kbtkw) E-01`, which introduced the guard, and if a requirement does mandate it, amend that spec in this plan and add the spec file to `Scope-Paths` first.
- `wtiso_gate.py:287-296` describes the refusal in prose as a shipped fact; update that text if E-04 removes the symbol.

## Open questions

### OQ-01: Delete `dirty_tree_overlap`, or keep it as a reporting-only helper?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-13 by the maintainer: DELETE it and update every reference (option (a)), so E-04 takes that branch. The maintainer's instruction was conditional, and the condition was tested rather than assumed. They asked to KEEP the gate if it could be OFF for the runner while still warning humans and agents (who "usually are not" as rigorous), with an override that does not disable every gate. MEASURED ANSWER: the condition cannot be met, because `dirty_tree_overlap` has EXACTLY ONE caller and that caller is the runner (`runner_shared.py:1003`); nothing in `cli.py`, `work_cmd.py` or `ipd_lifecycle.py` calls it. So disabling it for the runner disables it for everything and leaves a zero-caller symbol, and the maintainer's stated fallback was "if no, delete it". CRUCIALLY, THE PROTECTION THEY WANTED ALREADY EXISTS ELSEWHERE and is untouched by this Set: the human/agent path through `aw ipd begin` is guarded by `run_evidence.dirty_within` via `ipd_lifecycle.py:894-897`, which is the SCOPED check that refuses an uncommitted path inside the plan's `Scope-Paths` while deliberately ignoring disjoint work. That is precisely the warn-the-less-rigorous-actor behavior requested, on the path where it belongs, so deletion costs humans and agents nothing.

### OQ-03: The maintainer's OQ-01 answer was given without the two approved plans in view. Does DELETE still stand?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-201
- Resolution or deferral rationale: OQ-01 IS GENUINELY ANSWERED and this question does NOT reopen its reasoning; it asks whether the answer was given on complete information. The measured premises behind OQ-01 all hold, re-verified at review: `dirty_tree_overlap` has EXACTLY ONE non-test caller and it is the runner (`runner_shared.py:1003`); the `aw ipd begin` scoped protection is intact via `run_evidence.dirty_within` (`ipd_lifecycle.py:894-897`); so "off for the runner" really would leave a zero-caller symbol. What the answer did not have in front of it is that TWO APPROVED, `Blocks-Release: next` PLANS ARE SIGNED OFF TO KEEP AND IMPROVE THIS EXACT SYMBOL: `fujm0y` WIDENS its input from `lane.changed_files` to the `merge-tree` result diffed against HEAD, and `51vw4y` builds a non-terminal deferral ladder on its `integration-blocked` arm while stating "THE REFUSAL ITSELF IS CORRECT AND MUST SURVIVE". Neither is mentioned anywhere in this plan or in OQ-01's rationale.
  WHY THIS CHANGES THE CALCULUS RATHER THAN JUST ADDING CONTEXT: OQ-01's fallback logic was "if the gate cannot be kept usefully, delete it". `fujm0y` is a concrete, reviewed, approved design for keeping it usefully, which is the option OQ-01 assumed did not exist. Note also that `fujm0y`'s widening would make F-5's "narrower than git's precondition" complaint FALSE by construction, since the widened input is derived from the merge result itself.
  THREE COHERENT ANSWERS. (a) DELETE, as OQ-01 says: then `fujm0y` and `51vw4y` must be retired to `superseded/` with a reason, and E-04's full breadth applies. (b) KEEP AND IMPROVE: execute `51vw4y` then `fujm0y`; this plan reduces to E-02 plus E-03 (the reclassification and the non-destructiveness proof), which is where its measured evidence actually points (F-4, F-7). (c) DEMOTE to a reporting-only helper: satisfies nobody's approved design and leaves a symbol with no gate behind it; not recommended. REVIEW RECOMMENDS (b), because E-02 delivers this plan's real, witnessed value under any ruling, while the deletion rests on F-1/F-5 plus simplicity with no run record behind it (F-4a).

### OQ-02: After the deletion, should the runner still report dirty paths before attempting the merge?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-13 by the maintainer: NO pre-merge report. Git's own refusal names the offending files and the run records that reason (E-02), and Order 01 already reports dirty paths at launch, so a third signal would add a second place that can drift from git's actual behavior. Avoiding exactly that drift is the point of this plan.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the test output for an integration that SUCCEEDS with a non-conflicting dirty tracked path in main, plus `git log --oneline -1` on main showing the merge landed. Paste the rewritten docstring step 0.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the recorded `(integrated, reason, kind)` for a conflicting-dirty-path case, showing `kind == "integration-blocked"` and git's own "Your local changes" text inside `reason`. Also paste a genuine content-conflict case showing `kind == "merge-conflict"`, proving the two are not collapsed. PASTE THE DISCRIMINATOR ITSELF, not only its outcome: show that the two branches are chosen by the structural test (`MERGE_HEAD` present/absent, `--diff-filter=U` non-empty/empty) and NOT by matching git's English, since a text match would silently break under a localized or newer git. Paste evidence that NO `git merge --abort` is issued on the local-changes branch (F-6: it exits 128 there), for example the recorded git invocations for that case.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: for a refused integration, paste `git status --porcelain` and the content of the dirty file BEFORE and AFTER, proving both unchanged, plus `git rev-parse HEAD` unchanged and the lane branch still present.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: IF OQ-03 RULED (b), this V-item is satisfied by pasting the OQ-03 answer plus the not-performed marks on E-04/E-05; a skipped item must be recorded as skipped with its reason, never marked verified. OTHERWISE: paste a repo-wide `grep -rn dirty_tree_overlap` returning ZERO hits (excluding `.git` and caches). Paste the updated `wtiso_gate.py` text proving it no longer cites the deleted symbol as evidence of a shipped refusal. Confirm the human/agent guard is untouched by pasting a passing test for the `aw ipd begin` in-scope-dirty refusal, which is the protection OQ-01 relies on remaining in place.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the rewritten paragraph from `lane_containment.py` and confirm it describes the behavior Orders 01 and 02 actually shipped, naming neither a refusal that no longer happens nor a symbol that no longer exists.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit only files this plan changed, path-scoped, never `git add -A`, never push. Paste actual runner output for every test claim. OQ-01 is answered (DELETE), and OQ-03 is BLOCKING: it asks whether that answer stands now that two approved `Blocks-Release: next` plans are known to depend on the symbol. E-01, E-04 and E-05 MUST NOT be started before OQ-03 is answered. E-02 and E-03 are NOT gated and may be executed on their own; if OQ-03 rules (b), record E-01/E-04/E-05 as not-performed with that reason rather than leaving the plan stalled.

Post-gate lifecycle move: this plan reaches `executed/` only when every V-item above carries pasted evidence and `aw ipd lint --phase pre-transition` reports conforming.
