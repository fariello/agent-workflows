# IPD: Refuse a foreign merge instead of aborting it during lane integration

- Date: 2026-09-28
- Kind: child
- Concern: `runner_shared.integrate_lane_branch` responds to a merge failure by testing `merge_in_progress(repo)` and, when true, running `git merge --abort` on the shared checkout. The structural test is correct for the case it was written for, but it answers "is ANY merge in progress" while the code uses it as "did MY merge start". When a THIRD PARTY's merge is already staged in main, git REFUSES to start the driver's merge precisely BECAUSE that `MERGE_HEAD` exists, the predicate then reads the foreign merge state, and the abort DESTROYS work the driver does not own. Measured 2026-09-18 in run `run-20260917T231229Z-2701568` (review item `i4ak5n`): 14 staged files vanished, leaving `reset: moving to HEAD` in the reflog. Reproduced synthetically at HEAD `6a68f7fa` (F-01). It is also SILENT: `--abort` succeeds, the refusal is recorded `fail-merge` with a plausible reason, and nothing anywhere says a foreign merge was discarded. The runner is doing by hand exactly what `AGENTS.md` forbids agents from doing ("never revert, stage, commit, discard, or clean up another party's work").
- Scope: Make ownership a POSITIVE PROOF rather than an assumption, in the one shared function both hosts call. Add a `merge_head_commits` reader and an `owns_merge_in_progress` predicate to `runner_shared`; refuse BEFORE attempting any merge when a foreign merge is already in progress, returning the deferrable transient kind with its own distinguishable reason; and narrow the abort so it fires only on a merge this call provably started. Add a `tests/test_foreign_merge_refusal.py` regression file asserting, on BOTH hosts, that a foreign `MERGE_HEAD` yields a refusal with NO abort and a byte-identical staged index, and that the genuine-conflict case still aborts exactly as today. Change nothing about the existing conflict taxonomy, the records-only re-derivation path, the history-append auto-resolution, or the deferral ladder.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_foreign_merge_refusal.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: csmtjp
- Blocks-Release: next
- Set: foreignmerge
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: g2z2pp
- Approval: 2026-09-28, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-28 approved (aw set): status set to approved
- 2026-09-28 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review complete: APPROVE WITH REVISIONS APPLIED; PR-201 (HIGH) through PR-205 all FIXED in place; findings, decisions and measurements in .aw/records/reviews/20260928-foreignmerge-01-g2z2pp-...review.md

- 2026-09-28 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-201 (HIGH), PR-202, PR-203, PR-204, PR-205, all FIXED in place. Reviewed at HEAD `821245a6`; full findings, decisions D-1..D-3 and the pasted measurements are in `.aw/records/reviews/20260928-foreignmerge-01-g2z2pp-refuse-a-foreign-merge-instead-of-aborting-it-during-lane-in.review.md`. THE DIAGNOSIS AND EVERY PREMISE MEASUREMENT REPRODUCED at this HEAD: F-01 verbatim including the `reset: moving to HEAD` reflog signature and the destroyed index tree, F-03's three blind guards, F-04 on both sides, F-06's octopus truncation, and E-01's linked-worktree resolution. ONE SUBSTANTIVE DEFECT WAS FOUND IN THE PROPOSED FIX: `MERGE_HEAD` records WHICH commit was merged and never WHO merged it, so `owns_merge_in_progress(branch=handle.branch)` answers True for a THIRD PARTY's merge of this lane's own branch. Measured: a human's hand-resolved merge of `lane/probe`, carrying a staged file existing on no branch, satisfied the predicate and was then destroyed by the abort - this plan's own harm class, through the very race E-03 admits it cannot close. E-04 therefore now requires a CONJUNCTION with a locale-safe signal already in scope at that arm: the driver's own merge returns rc=1 when it starts and conflicts and rc=128 when git refuses to start it because `MERGE_HEAD` exists (both measured, on clean and conflicted foreign merges), so ownership is proven without matching git's English and the shipped locale test is unaffected. E-05 gains a fifth case pinning the impostor shape, to be shown RED against a branch-comparison-only implementation. Four further fixes: the predicate's name must not overstate what it proves; E-04's "one condition" now records that all FOUR aborts in the block nest under the single guard (measured by indentation) so a partial fix is not invited; F-11's `2935 passed` baseline is stale (`2937` at this HEAD) and both citations now require a re-derived same-commit baseline; and the impostor shape is stated as explicitly IN scope rather than reading as an enumerated exclusion. `aw ipd lint --phase review-finalize --agent` conforms (exit 0, 0 findings). Suite re-checked unchanged at `2937 passed, 2 skipped`. Human approval is still required before execution.
- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `csmtjp`. Every claim in the item was re-measured at HEAD `6a68f7fa` rather than carried over. The defect REPRODUCES exactly as described, including the `reset: moving to HEAD` reflog signature (F-01). Two of the item's statements are CORRECTED by measurement: its fix sketch's pre/post ordering is necessary but NOT sufficient (F-05), and its step 6 asks for an agy-host confirmation that is unnecessary because both hosts already delegate to one shared implementation (F-08). One claim is now STALE: the item says `run_lock` being per-run means two drivers are not serialized, and `integrate_under_repository_lock` has since serialized publishes repository-wide (F-07). OQ-01 and OQ-02 resolved from repository evidence; OQ-03 is non-blocking and deferred with a carrier.
- 2026-09-28 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Leave the repository in a state where a driver CANNOT destroy a merge it did not start. After this plan, `integrate_lane_branch` proves ownership of an in-progress merge from `MERGE_HEAD`'s VALUE before aborting it, refuses a checkout that is already mid-merge as a deferrable `merge-retry` with a reason that names the condition distinctly, and carries a regression test on both hosts that fails if the abort ever widens back. Every other integration behavior is byte-identical: the genuine content conflict still aborts and still returns the terminal kind, the local-changes refusal still issues no abort, and the re-derivation and history-append paths are untouched.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make merge ownership readable

- [x] E-01 Add `merge_head_commits(repo: Path) -> list[str]` to `runner_shared`, sited immediately after `merge_in_progress` so a reader meets the two together. It must return EVERY commit id recorded in `MERGE_HEAD`, in file order, and `[]` when no merge is in progress. Read it by resolving the file through `git rev-parse --git-path MERGE_HEAD` and reading that path, NOT by `git rev-parse MERGE_HEAD` and NOT by probing `.git/MERGE_HEAD` directly. Both alternatives are MEASURED WRONG and the docstring must record why, because both look correct: `git rev-parse MERGE_HEAD` returns only the FIRST entry of a multi-entry (octopus) `MERGE_HEAD` (measured: a two-parent `MERGE_HEAD` whose file holds two ids renders as ONE line, so a foreign second parent would be invisible), and a direct `.git/MERGE_HEAD` probe is wrong in a LINKED WORKTREE where `.git` is a FILE pointing at `<common>/worktrees/<name>/` (measured: `--git-path` resolved to the worktree's own metadata directory while `<worktree>/.git/MERGE_HEAD` did not exist) - which is the same trap `merge_in_progress`'s own docstring already records for the same reason. Treat a relative `--git-path` result as relative to `repo`. Return `[]` rather than raising on any `OSError` or non-zero rc, because this is a predicate feeding a refusal decision and an unreadable state must fail toward "I cannot prove ownership", never toward an abort.
  - Depends on: none
  - Expected outcome: A function that returns `[<lane tip>]` for a merge the driver started, `[<foreign tip>]` for a third party's staged merge, both entries for an octopus merge, and `[]` for a clean tree, in both a primary checkout and a linked worktree.
  - Execution state: performed

- [x] E-02 Add `owns_merge_in_progress(repo: Path, *, branch: str) -> bool` to `runner_shared`, beside E-01's reader. It answers the question the code actually needs: is the in-progress merge THE ONE that merged `branch`? Implement it as `merge_head_commits(repo)` being non-empty AND every entry resolving to the same commit as `branch` (resolve `branch` with `git rev-parse --verify --quiet <branch>^{commit}` and compare full 40-char ids; refuse on an unresolvable branch). This is a POSITIVE proof and is strictly stronger than the pre/post ordering the backlog item's fix sketch proposes, which is why the ordering change alone is not what this plan implements (F-05): ownership derived from a VALUE holds even when a peer creates a `MERGE_HEAD` between a pre-check and the merge attempt, whereas a pre/post ordering reads False-then-True and aborts the peer's merge. MEASURED: in the genuine-conflict case `MERGE_HEAD` equals the lane branch tip exactly, and in the foreign case it equals the third party's tip (F-04). The docstring must state ALL-entries-must-match explicitly, since `any` would be the wrong quantifier: a merge that includes our branch AND a foreign one is not ours to abort. Return False when `MERGE_HEAD` is empty (no merge to own) and when the branch cannot be resolved (cannot prove ownership).
  NAME IT FOR WHAT IT PROVES, WHICH IS NARROWER THAN "OWNS" (finding PR-201). MEASURED at HEAD `821245a6`: this predicate answers True for a merge of `branch` that a THIRD PARTY started, because `MERGE_HEAD` records WHICH commit was merged and never WHO merged it. So `owns_merge_in_progress` overstates it and the name will mislead the next reader into treating it as sufficient authority to abort, which is precisely the mistake E-04 originally made. Either name it for the property it actually establishes (for example `merge_in_progress_is_of_branch`) or keep the name and open the docstring with the limit stated in one sentence: this proves the merge is OF our branch, NOT that this call started it, so it is NECESSARY BUT NOT SUFFICIENT authority to abort, and E-04 must conjoin it with the started-it signal. Record which choice was made.
  - Depends on: E-01
  - Expected outcome: True only for a merge whose every `MERGE_HEAD` entry is `branch`'s tip; False for a foreign merge, for a clean tree, for an octopus merge that includes a foreign parent (measured False, correctly), and for an unresolvable branch. The docstring states that a True answer does NOT establish that this call started the merge, with the measured impostor case cited.
  - Execution state: performed

### Task group 2: refuse a busy checkout instead of merging into it

- [x] E-03 In `integrate_lane_branch`, add a PRE-MERGE refusal: after the existing `dirty_tree_overlap` guard (which is the E-01 dirty-tree guard its docstring numbers step 0) and BEFORE the revalidation gate call, refuse when `merge_in_progress(repo)` is already true. Return `(False, <reason>, INTEGRATION_REFUSAL_TRANSIENT)`. Add a `format_foreign_merge_refusal_reason(repo)` helper beside `format_local_changes_refusal_reason` producing that reason, and require it to name (a) that the checkout is ALREADY mid-merge, (b) that the driver attempted NO merge and issued NO abort, and (c) the foreign `MERGE_HEAD` id(s) from E-01 so an operator can identify whose merge it is. SITE IT BEFORE THE GATE, not merely before the merge: the gate is the expensive step (it materializes a merge result and runs a full suite), and spending it against a checkout the publish cannot possibly land on is pure waste. DO NOT add a new refusal KIND: `INTEGRATION_REFUSAL_TRANSIENT` is correct because the condition clears itself when the third party commits or aborts, and `classify_integration_refusal` already defers it (measured: `decide_integration_deferral(TRANSIENT, 1/10)` returns `deferred=True`, while `CONFLICT` returns `deferred=False`). Adding a kind would reach the legacy alias map, the analytics keys and both hosts' status vocabularies for no behavioral gain (OQ-01). Extend the function's docstring with a numbered step recording this arm and its reason, matching the existing steps 0 through 4.
  - Depends on: E-02
  - Expected outcome: With a foreign merge staged in main, `integrate_lane_branch` returns `merge-retry`, runs no `merge` and no `merge --abort` at all, and the foreign staged index is byte-identical afterwards.
  - Execution state: performed

- [x] E-04 Narrow the post-merge abort so it can only fire on a merge this call provably started. Change the conflict-arm condition from `if merge_in_progress(repo):` to a proof that THIS CALL started the merge, and add an `elif merge_in_progress(repo):` arm returning `format_foreign_merge_refusal_reason(repo)` with `INTEGRATION_REFUSAL_TRANSIENT` and issuing NO abort. THIS ARM IS NOT DEAD CODE DESPITE E-03, and the comment must say so or a later reader will delete it: E-03 reads `git status` at one instant and the merge runs at a later one, in a SHARED CHECKOUT, so a peer can stage a merge in between - the same "no prediction can close that window" reasoning the `_refusal_repo` fixture already records for the retained dirty guard. Leave the final fall-through arm (git REFUSED TO START, no `MERGE_HEAD`, no abort issued) exactly as it is. Leave the records-only re-derivation block, the history-append auto-resolution, `conflicted_paths`-before-abort ordering, `build_conflict_resolver_detail`, the cause tagging and every returned reason string in the owned branch untouched: this is a NARROWING of the guard, not a rework of the conflict path. NOTE FOR THE EXECUTOR: the four `git merge --abort` calls inside that block are all NESTED under this ONE guard (measured: guard at indent 4, aborts at indents 16, 12, 12 and 8), so narrowing the single guard does gate all four; do not mistake "one condition" for "one abort".

  `owns_merge_in_progress(branch=handle.branch)` IS NOT SUFFICIENT ON ITS OWN, AND THIS IS THE ONE THING REVIEW CHANGED IN THIS ITEM (finding PR-201). It proves WHICH BRANCH was merged, not WHO merged it, so it answers True for a merge of our own lane branch that a THIRD PARTY started. MEASURED at HEAD `821245a6`: a human ran `git merge --no-ff lane/probe` in main, hit a conflict, resolved one path by hand and staged an additional unrelated file; `MERGE_HEAD` equalled the lane tip exactly, so the predicate returned **True**, and `git merge --abort` then discarded the human's resolution and deleted their staged file. That is the SAME harm class this plan exists to remove, through a narrower window rather than a closed one, and it is reachable precisely in the race E-03 cannot close (a peer stages a merge between E-03's read and our merge attempt; if what they merged happens to be our lane branch, the branch comparison cannot tell us apart).
  SO REQUIRE A CONJUNCTION, and take the second half from a LOCALE-SAFE SIGNAL THIS CALL ALREADY HAS: the return code of the driver's own `git merge --no-ff` attempt, which is in scope at this arm. MEASURED at the same HEAD: a merge that STARTED AND CONFLICTED returns **rc=1**, while a merge git REFUSED TO START because `MERGE_HEAD` already existed returns **rc=128** (reproduced on both a clean staged foreign merge and a conflicted one). So the abort must fire only when the merge attempt returned the started-and-conflicted code AND `owns_merge_in_progress` agrees; on the refused code the arm must route to the foreign refusal and issue no abort, whatever `MERGE_HEAD` happens to contain. DO NOT MATCH GIT'S MESSAGE TEXT to make this distinction: `merge_in_progress`'s own docstring records why (localizable, version-dependent) and the shipped locale test would regress. The exit code carries no language. If the executor finds the rc values differ on the git version under test, that is a finding to RECORD with the measured values rather than a reason to fall back on text.
  - Depends on: E-03
  - Expected outcome: The genuine conflict still aborts, still returns `fail-merge`, and still carries its existing reason text; a foreign `MERGE_HEAD` reaching the post-merge arm refuses `merge-retry` with no abort, INCLUDING the case where the foreign merge's merged-from branch is this lane's own branch.
  - Execution state: performed

### Task group 3: pin it on both hosts

- [x] E-05 Add `tests/test_foreign_merge_refusal.py` pinning the whole property on BOTH hosts through each host's own `integrate_lane_branch` wrapper, not by calling the shared function directly, because the host bindings are the one thing the shared implementation cannot supply and an agy-only regression has left both suites green before (`tests/test_runner_shared.py::LaneIntegrationBehaviorTests` records that asymmetry). Four cases. (1) FOREIGN MERGE, THE DEFECT: stage a third party's `git merge --no-ff --no-commit` in main, capture `git diff --cached --name-only` and the index tree (`git write-tree`) before, integrate, then assert the returned kind is `merge-retry`, that NO `["merge", "--abort"]` appears in a traced `_run_git` argv list, that `MERGE_HEAD` is STILL set, and that the staged set and the index tree hash are BYTE-IDENTICAL. Trace argv with the `_git_trace` pattern already used in `tests/test_runner_shared.py`, since an abort that was not issued cannot be observed from repository state afterwards. (2) GENUINE CONFLICT UNCHANGED: assert `fail-merge`, that `["merge", "--abort"]` IS in the trace, that `merge_in_progress` is False afterwards, that main's `git status --short` is empty, and that the lane branch survives. (3) OWNERSHIP PREDICATE DIRECTLY: `owns_merge_in_progress` True mid-own-conflict, False for the foreign merge, False on a clean tree, and `merge_head_commits` returning both ids for an octopus `MERGE_HEAD` and `[]` for a clean tree. (4) REFUSAL IS DEFERRABLE AND DISTINGUISHABLE: `classify_integration_refusal` True for the returned kind, and the reason names the mid-merge condition and does NOT contain the substring `merge-back conflict`, which is what today's misclassified message said (F-01) and is the one string an operator uses to tell "my lane conflicts" from "the tree was already busy". (5) ADDED AT REVIEW, THE IMPOSTOR CASE (finding PR-201, F-15), and it is the decisive one for E-04's conjunction: a THIRD PARTY starts `git merge --no-ff <this lane's own branch>` in main, hits a conflict, resolves a path by hand and stages an additional unrelated file. Assert the returned kind is `merge-retry`, that NO `["merge", "--abort"]` appears in the trace, that `MERGE_HEAD` is still set, and that the human's staged set and index tree are BYTE-IDENTICAL, including the file that exists on no branch. MEASURED at HEAD `821245a6`: `owns_merge_in_progress(branch=...)` returns True for this shape, so a fix built on the branch comparison ALONE fails this case while passing cases 1 through 4, which is exactly why it is required. This case must be shown RED against a branch-comparison-only implementation, not merely green at the end.
  - Depends on: E-04
  - Expected outcome: A new test file that fails at HEAD `821245a6` on case 1 (the staged index is destroyed) and on case 5, and passes after E-01 through E-04, with cases 2 through 4 passing throughout.
  - Execution state: performed

## Project conventions discovered (Step 0)

- ONE SHARED IMPLEMENTATION, TWO HOST WRAPPERS, so the fix belongs in exactly one place. `oc_runipd.integrate_lane_branch` and `agy_runipd.integrate_lane_branch` both delegate to `runner_shared.integrate_lane_branch`, binding only `host_label`, `run_checked` and a literal `action_kind`. `tests/test_runner_shared.py` pins this with `LANE_INTEGRATION_MOVED`, `LANE_INTEGRATION_WRAPPED` and `test_each_wrapper_keeps_the_ORIGINAL_signature`, whose docstring reads "no wrapper may expose the injected parameter". So NO host file is in `- Scope-Paths:`, and adding a parameter to the shared function's signature would break a shipped contract test.
- CODE IS CITED BY SYMBOL, NOT BY BARE LINE OFFSET (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This matters acutely here: EVERY bare offset the backlog item cites is stale at this HEAD. It points at `merge_in_progress` in `runner_shared` by an offset that now lands hundreds of lines above that function; it points at `run_lock`'s `run_dir / "driver.lock"` in `oc_runipd` by an offset that no longer lands on it; and it points at an integration event emitter in `agy_runipd` by an offset that lands nowhere near one (that host's integration call is the thin `agy_runipd.integrate_lane_branch` wrapper). An executor following those offsets lands in unrelated valid code, which is exactly how a "fix" gets applied to the wrong side of a working call. Every citation in this plan is therefore by SYMBOL or by quoted content string.
- THE STRUCTURAL `MERGE_HEAD` TEST IS DELIBERATE AND MUST BE PRESERVED, not replaced. `merge_in_progress`'s docstring records four scratch-repository measurements and states explicitly why git's English is NOT matched: the text is localizable and version-dependent, and a misclassification converts a self-clearing condition into permanent in-run loss. `tests/test_runner_shared.py` drives both failure classes under `LC_ALL`/`LANGUAGE` forced non-English. This plan NARROWS the predicate with a value comparison; it does not introduce a text test, and doing so would regress that shipped locale test.
- THE REFUSAL KINDS ARE A CLOSED, DOCUMENTED TAXONOMY WITH A LEGACY ALIAS MAP THAT MUST NEVER BE DELETED. `INTEGRATION_REFUSAL_TRANSIENT` is `merge-retry` (deferrable), `INTEGRATION_REFUSAL_CONFLICT` is `fail-merge` (terminal on first attempt), `INTEGRATION_REFUSAL_UNMEASURED` is `merge-unchecked`, and `LEGACY_INTEGRATION_STATUS_ALIASES` translates every pre-rename spelling on READ because run directories are durable records. Reusing `merge-retry` therefore costs nothing, while a new kind would reach that map, `canonical_integration_status`, the analytics keys and both hosts' `TERMINAL_STATES`.
- SPEC `25kzda` SECTION 2.1 PROHIBITS RETRY-BY-REPETITION, and the deferral ladder is its sanctioned carve-out (2.1a/2.1b). Routing to the deferrable kind is consistent with this because the condition is another party's transient state, exactly like the existing dirty-overlap arm, and the ladder's budget makes it terminal at `merge-needs-human` when exhausted (measured: `decide_integration_deferral(TRANSIENT, attempts_used=10, limit=10)` still defers, and the exhausted arm returns `deferred=False`). Nothing in this plan retries anything itself.
- THE SUITE RUNS BARE. `pyproject.toml` `addopts` supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do not add `-n0` (measured several times slower here), a second `-q` (compounds to `-qq` and suppresses the `N passed` line this plan's validation requires), or `-p no:randomly`.
- `runner_shared.py` IS THE HIGHEST-CONTENTION FILE IN THIS REPOSITORY and this is a shared checkout, so the executor must verify the staged set with `git diff --cached --name-only` before committing and commit through `aw commit`. That is a live hazard for this plan specifically, not boilerplate: the defect being fixed is itself a concurrency defect measured in this very checkout.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | THE DEFECT REPRODUCES AT THIS HEAD, WITH THE INCIDENT'S EXACT SIGNATURE. A scratch repo with a third party's `git merge --no-ff --no-commit` staged (1 staged file) plus a lane branch, driven through `runner_shared.integrate_lane_branch`, returned `kind='fail-merge'` with reason `[aw-integration-cause=git-merge-conflict][aw-conflict-shape=unknown] merge-back conflict; fatal: You have not concluded your merge (MERGE_HEAD exists).`, and afterwards the staged set was EMPTY, `MERGE_HEAD` was gone, and the reflog's newest entry read `reset: moving to HEAD` - the same line the 2026-09-18 incident recorded. So the item's core claim is verified, not inherited. | A repro script under `.aw/state/` (gitignored) run at HEAD `6a68f7fa`; output pasted in V-01. |
| F-02 | THE REFUSAL IS MISCLASSIFIED AS WELL AS DESTRUCTIVE, which doubles the cost. The returned kind is `fail-merge`, and `classify_integration_refusal('fail-merge')` is False (measured), so the item is terminal on its FIRST attempt and excluded from the deferral ladder - for a condition that clears itself the moment the third party commits. A verified lane is therefore stranded for the rest of the run in addition to the foreign merge being destroyed. | `classify_integration_refusal` probed for both kinds; `decide_integration_deferral(CONFLICT, 1, 10)` returned `status=fail-merge deferred=False`, `(TRANSIENT, 1, 10)` returned `status=merge-retry deferred=True`. |
| F-03 | THE EXISTING PRE-MERGE GUARDS CANNOT SEE THIS CONDITION, so a new arm is genuinely required rather than a widening of an existing one. With the foreign merge staged, `merge_write_set(repo, branch)` returned `['lanefile.txt']` and `dirty_tree_overlap(repo, ['lanefile.txt'])` returned `[]` - the step 0 guard says CLEAR - because the foreign merge's staged path is not in the incoming write set. `conflicted_paths(repo)` also returned `[]`, since a clean foreign merge leaves no `U` entries. | Probe printing all three values against the staged-foreign-merge fixture. |
| F-04 | `MERGE_HEAD`'s VALUE IS A SOUND OWNERSHIP PROOF, measured on both sides. In the genuine-conflict case `git rev-parse MERGE_HEAD` equalled the lane branch tip exactly (`a1d1ac7d...`); in the foreign case it equalled the third party's tip (`e6134b9a...`) and differed from the lane tip. So E-02's comparison discriminates the two conditions with no text matching and no reliance on call ordering. | Two scratch repositories printing lane tip, foreign tip and `MERGE_HEAD` side by side. |
| F-05 | THE ITEM'S FIX SKETCH IS NECESSARY BUT NOT SUFFICIENT, which is why this plan implements a stronger predicate than it asks for. Its steps 1 and 2 capture `merge_in_progress` BEFORE the attempt and abort only on False-then-True. That closes the measured case, but in a shared checkout a PEER can stage a merge BETWEEN the pre-check and the merge attempt: the pre-check reads False, the attempt fails on the peer's `MERGE_HEAD`, the post-check reads True, and the abort destroys the peer's merge - the identical harm through a narrower window. The repository already records that this window cannot be closed by prediction, in `_refusal_repo`'s docstring ("the guard reads `git status` at one instant and the merge runs at a later one, and this is a SHARED CHECKOUT ... No prediction can close that window"). Ownership by VALUE does not depend on timing at all. This plan keeps the item's pre-check (E-03, as a cheap early refusal that also saves the gate) AND adds the value proof (E-02/E-04). | The item's fix sketch steps 1-2; `_refusal_repo`'s quoted docstring; F-04's measurement. |
| F-06 | `git rev-parse MERGE_HEAD` IS AN UNSOUND READER FOR THE MULTI-PARENT CASE, so E-01 cannot use the obvious spelling. An octopus `git merge --no-commit --no-ff b1 b2` wrote a `MERGE_HEAD` file containing TWO ids, yet `git rev-parse MERGE_HEAD` printed ONE line (the first, `c85f361e...`, b1's tip) while b2's tip `012a54a4...` was invisible. A driver reading only the first entry could conclude it owned a merge whose second parent is foreign. Reading the file via `git rev-parse --git-path MERGE_HEAD` returned both. | Two probes: the raw `MERGE_HEAD` file contents versus `rev-parse` output, plus both branch tips. |
| F-07 | THE ITEM'S "TWO DRIVERS ARE NOT SERIALIZED" CLAIM IS NOW STALE, and this is recorded so a reviewer does not expect this plan to fix it. The item argued from `run_lock` being per-run (`run_dir / "driver.lock"`). Since then `integrate_under_repository_lock` serializes every publish behind a REPOSITORY-scoped `integration_lock_path(repo)` (derived through `runs_repo_root`, shared with the `aw integration-lock` verb), and every integration call site in `runner_shared` routes through it, including the review path and the ladder's re-attempts. So the DRIVER-VERSUS-DRIVER window the item describes is closed by that lock. What is NOT closed, and is what this plan fixes, is the HUMAN case and the `--allow-concurrent-driver` consent case: `concurrent_driver_consent` lets an operator skip the lock entirely, and no lock binds a human's hand-run `git merge`. `AGENTS.md` states this explicitly ("THIS IS A PROTOCOL, NOT AN ENFORCEMENT BOUNDARY"). | `integration_lock_path`; `integrate_under_repository_lock`'s consent arm; the count of its call sites in `runner_shared`; `tests/test_concurrent_driver_guard.py`. |
| F-08 | THE ITEM'S STEP 6 ("check the agy host for the same shape") NEEDS NO SEPARATE FIX. Both hosts' `integrate_lane_branch` are thin wrappers delegating to the shared function and binding only `host_label`, `run_checked` and a literal `action_kind`; neither contains a `merge --abort`. A repository-wide search for `["merge", "--abort"]` finds it only in `runner_shared`, at the conflict arm this plan narrows, at the lane-local `prepare_lane_for_conflict_resolution` paths, and at one lane-local cleanup before a terminal refusal. So one fix covers both hosts, as the item hoped; E-05 nonetheless tests through both wrappers because the host bindings are what a shared fix cannot prove. | Reads of both host wrappers; the `merge --abort` search results. |
| F-09 | THE LANE-LOCAL ABORTS ARE CORRECT AND MUST NOT BE TOUCHED, which bounds this plan's blast radius. `prepare_lane_for_conflict_resolution` operates on `handle.path` (the LANE WORKTREE, not main), and it already REFUSES when a merge is in progress there, returning `detail="unconcluded merge in progress (MERGE_HEAD exists)"` - the precedent this plan follows for main. `tests/test_merge_conflict_sendback.py::test_case_3_called_with_merge_in_progress_refuses_without_second_merge` pins that behavior on both hosts. Its later `merge --abort` calls apply to a merge it started itself in the lane. | Read of `prepare_lane_for_conflict_resolution`; the named test. |
| F-10 | THE POLL RUNG CANNOT SEE A MID-MERGE CHECKOUT EITHER, which is a real limit on how well the deferral will work and is why OQ-03 exists rather than being silently ignored. `poll_for_integration_window` waits on `dirty_tree_overlap(repo, changed_files)`; with a foreign merge staged on a NON-overlapping path that returned `[]`, i.e. the rung reports the base CLEAR while `MERGE_HEAD` is still set, so a re-attempt refuses again immediately and burns a budget slot. The deferral is still strictly better than today's destructive terminal refusal, and the ladder ends at `merge-needs-human` rather than spinning. | Probe printing `merge_in_progress=True` alongside `dirty_tree_overlap(repo, ['lanefile.txt']) == []`. |
| F-11 | THE SUITE IS GREEN AT THIS HEAD, giving this plan a baseline to compare against: bare `python3 -m pytest` reported `2935 passed, 2 skipped, 3 warnings in 42.06s` with 201 tests deselected by the default `-m` expression. | The bare pytest run at HEAD `6a68f7fa`. |
| F-12 | NO EXISTING TEST ASSERTS THE PROPERTY THIS PLAN ADDS, so the regression is currently unguarded. `tests/test_runner_shared.py::LaneIntegrationBehaviorTests` covers the clean integration, the dirty-overlap refusal, the rename endpoints, the local-changes-refusal-issues-no-abort case and the genuine-conflict-aborts case, all with NO pre-existing merge in main. Searching the suite for a foreign `MERGE_HEAD` in the MAIN checkout finds only the lane-local `test_case_3` of F-09. So case 1 of E-05 is a genuinely new guard, and the abort assertion technique it needs (argv tracing) already exists as `_git_trace`. | Reads of that test class and its four case docstrings; the `merge_in_progress` search across `tests/`. |
| F-13 | THE REASON STRING IS A PARSED INTERFACE, so E-03's new reason must not carry a cause token by accident. `record_integration_refusal` parses `[aw-integration-cause=...]` and `[aw-conflict-shape=...]` prefixes out of the reason, and `record_refusal` is invoked ONLY when the cause is `INTEGRATION_CAUSE_GIT_CONFLICT`. The transient arms (`dirty_tree_overlap`, `format_local_changes_refusal_reason`) carry NO token and read as cause UNKNOWN, which routes to today's conservative wording. E-03's reason must follow them and tag nothing, so no new cause constant is needed and `terminal_refusal_verdict`'s three-cause reachability proof stays accurate. | `tag_integration_cause` call sites in `integrate_lane_branch`; the `if cause == INTEGRATION_CAUSE_GIT_CONFLICT:` guard at the `record_refusal` write site; `INTEGRATION_CAUSE_GATE_CONFLICT_MARKERS`'s reachability docstring. |
| F-15 | THE OWNERSHIP PROOF AS SPECIFIED IS NECESSARY BUT NOT SUFFICIENT, BECAUSE `MERGE_HEAD` RECORDS *WHICH* COMMIT WAS MERGED AND NEVER *WHO* MERGED IT. MEASURED at HEAD `821245a6`: a human ran `git merge --no-ff lane/probe` in main, conflicted, resolved one path by hand and staged an extra file existing on no branch; `MERGE_HEAD` equalled the lane tip exactly, so an `owns_merge_in_progress(repo, branch=handle.branch)` implemented as E-02 specifies returned **True**, and `git merge --abort` then discarded the resolution and deleted the staged file (`git diff --cached --name-only` went from `['extra.txt','f.txt','human_only.txt']` to `[]`, and `human_only.txt` ceased to exist). So a fix built on the branch comparison ALONE leaves the plan's own harm class reachable through the narrow race E-03 admits it cannot close. Addressed by E-04's conjunction and pinned by E-05 case 5. | a scratch repo at HEAD `821245a6` driving the E-01/E-02 spellings verbatim, then the abort, printing the staged set and index tree before and after |
| F-16 | THE STARTED-IT SIGNAL IS AVAILABLE AND LOCALE-SAFE, which is what makes F-15 fixable without matching git's English. MEASURED at HEAD `821245a6`: the driver's own `git merge --no-ff` returns **rc=1** when it STARTS and conflicts, and **rc=128** when git REFUSES TO START it because `MERGE_HEAD` already exists (reproduced against both a CLEAN staged foreign merge and a conflicted one; the rc=128 case carries "fatal: You have not concluded your merge (MERGE_HEAD exists)", which is the same text probe 1 captured in the destructive reproduction). The exit code carries no language, so conjoining it with F-15's branch test satisfies `merge_in_progress`'s standing prohibition on text matching and keeps the shipped locale test green. | two scratch repositories at HEAD `821245a6` measuring both shapes' return codes and stderr |
| F-17 | THE FOUR ABORTS ARE ALL NESTED UNDER THE ONE GUARD, so E-04's single-condition change does gate them, and saying so prevents a half fix. MEASURED by walking `integrate_lane_branch`'s own source: `if merge_in_progress(repo):` sits at indent 4 and the four `_run_git(repo, ["merge", "--abort"])` calls inside it sit at indents 16, 12, 12 and 8, all strictly deeper. Three of the four are the re-derivation-commit-refused, re-derivation-apply-failed and history-append-commit-refused arms; the fourth is the ordinary conflict refusal. | an AST-free indentation walk over `inspect.getsource(runner_shared.integrate_lane_branch)` at HEAD `821245a6` |
| F-18 | THE BASELINE F-11 RECORDS IS STALE, WHICH MATTERS BECAUSE THE PLAN USES IT AS A COMPARISON BAR. F-11 states `2935 passed, 2 skipped` at HEAD `6a68f7fa`; measured at HEAD `821245a6` the bare suite reports `2937 passed, 2 skipped`, because main advanced between authoring and review. The plan's own execution contract requires a baseline captured at the SAME commit as the after-state, so the executor must RE-DERIVE it rather than compare against either number. | bare `python3 -m pytest` at HEAD `821245a6` versus F-11's recorded figure |
| F-14 | LEAK DISCIPLINE CONSTRAINS WHAT E-03's REASON MAY CONTAIN. `record_refusal` does NOT redact (its `reason`/`remedy` reach the Diagnostics block verbatim, unlike `integration_refusal_detail`, which routes through `_redact_absolute_paths`). Commit ids are safe by construction; a git error string could in principle embed a path. E-03 therefore composes its reason from the `MERGE_HEAD` ids plus fixed prose rather than pasting git's stderr, unlike `format_local_changes_refusal_reason`, which deliberately carries git's text verbatim because that text NAMES the offending files. | The quoted leak-discipline comment at the `record_refusal` site; `format_local_changes_refusal_reason`'s docstring. |

## Proposed changes (ordered, validatable)

1. Add `merge_head_commits` reading EVERY `MERGE_HEAD` entry through `git rev-parse --git-path`, worktree-correct and octopus-correct (E-01).
2. Add the branch-match predicate proving a merge is OF a given branch by comparing all `MERGE_HEAD` entries to that branch's tip, named and documented as NECESSARY BUT NOT SUFFICIENT authority to abort (E-02).
3. Refuse before the gate when the checkout is ALREADY mid-merge, returning the deferrable `merge-retry` with a reason naming the condition and the foreign `MERGE_HEAD` ids, attempting no merge and issuing no abort (E-03).
4. Narrow the post-merge abort to a CONJUNCTION of the branch match AND the locale-safe started-it return code, so a third party's merge of our own branch is refused rather than aborted, adding a non-dead foreign arm for the peer-staged-in-between window (E-04).
5. Add `tests/test_foreign_merge_refusal.py` pinning all FIVE cases on both hosts, including the impostor case, an index-identity assertion and an argv trace proving no abort was issued (E-05).

## Deferred / out of scope (with reason)

- MAKING THE POLL RUNG MERGE-AWARE is deferred. `poll_for_integration_window` waits only on `dirty_tree_overlap`, so it reports a mid-merge base as CLEAR (F-10) and a deferred re-attempt refuses again immediately, spending a budget slot for nothing. Fixing it means adding a second clearing condition to the poll predicate, which touches the rung's bound reporting (`POLL_BOUND_*`), its detail strings and its tests - a distinct concern from "do not destroy a foreign merge", and one with no measured incident behind it. This plan's refusal is already strictly better than today's destructive terminal refusal, and the ladder remains bounded, so shipping the safety fix without the polling improvement leaves nothing worse than it found.
  - Carrier: p7dtbr
- WARNING AN OPERATOR AT RUN START THAT THE CHECKOUT IS MID-MERGE is out of scope. A pre-flight probe would turn a per-item refusal into one early, loud message, which is genuinely better ergonomics, but it belongs to the run-start capability reporting surface rather than to the integration seam, and this plan's `- Scope-Paths:` deliberately excludes every CLI and reporting module. The per-item refusal already names the condition and the `MERGE_HEAD` ids (E-03), so nothing is undiagnosable without it.
  - Carrier-Declined: No obligation is owed, because nothing is left BROKEN by omitting it. This is an ergonomic improvement on a path that, after this plan, already reports the condition accurately in the run record; filing a carrier would manufacture an obligation for a nice-to-have that no measurement asks for.
- CLOSING THE `--allow-concurrent-driver` HOLE is explicitly NOT attempted. `concurrent_driver_consent` lets an operator skip the repository integration lock with a recorded justification (F-07), and that is a deliberate, documented consent mechanism, not a defect. This plan makes the consequence SAFE (a driver publishing unserialized now refuses a foreign merge instead of destroying it) rather than removing the operator's choice, which would be a policy change about risk appetite and therefore a maintainer decision this plan has no authority to make.
  - Carrier-Declined: There is no defect to carry. The consent path is intended behavior and this plan removes its destructive consequence, so nothing remains outstanding.
- THE ITEM'S STEP 6 AGY-HOST CONFIRMATION is answered rather than deferred: both hosts already delegate to one shared implementation and neither contains a `merge --abort`, so one fix covers both (F-08). E-05 tests through both wrappers regardless.
  - Carrier-Declined: This row records a question this plan ANSWERED with evidence, not outstanding work, so there is no obligation to hand off.

## Scope check

- Over-scope: none. `agent_workflows/runner_shared.py` carries two new predicates, one new reason formatter, one new pre-merge refusal arm, one narrowed condition with its foreign sibling arm, and docstring updates; `tests/test_foreign_merge_refusal.py` is new. No host runner file is edited (F-08 shows none needs to be), no new refusal kind or cause constant is introduced (F-13), `LEGACY_INTEGRATION_STATUS_ALIASES` is untouched, the lane-local aborts are untouched (F-09), no spec is amended, no CLI flag changes, and no `.aw/` record other than this plan changes. E-04 deliberately leaves the re-derivation, history-append and cause-tagging blocks byte-identical.
- Under-scope: Two things are knowingly left. FIRST, a deferred re-attempt against a still-mid-merge checkout will refuse again immediately, because the poll rung cannot see `MERGE_HEAD` (F-10); that is the carried deferral, and it is the honest limit on how gracefully this recovers. SECOND, nothing prevents a human from staging a merge in a checkout live drivers are using; the item's own honest limit says the cheapest mitigation is not to do that, and this plan's claim is only that the runner's RESPONSE to finding one is to refuse rather than destroy. What is delivered is that the destructive action on unowned state is gone, proven by an index-identity assertion on both hosts. NOTE WHAT REVIEW ADDED TO THIS BOUNDARY (F-15): the impostor shape (a third party merging THIS lane's own branch) is explicitly IN scope, because it is reachable through the same race E-03 admits it cannot close and because the branch comparison alone answers it wrongly; E-04's conjunction and E-05 case 5 cover it, so it is not a residual this plan leaves behind.

## Required tests / validation

- `python3 -m pytest tests/test_foreign_merge_refusal.py -o addopts=""` for the per-test counts on the new file.
- `python3 -m pytest tests/test_runner_shared.py tests/test_merge_conflict_sendback.py tests/test_concurrent_driver_guard.py tests/test_agy_runipd_cli.py -o addopts=""` as the targeted regression set: the integration behavior class and its locale test, the lane-local conflict-prep cases, the integration lock, and the agy host's own integration assertions.
- `python3 -m pytest` run BARE, with its `N passed` line pasted and compared against a baseline the executor RE-DERIVES on a clean tree at the SAME commit as the after-state. DO NOT compare against F-11's `2935 passed, 2 skipped`: that figure was measured at HEAD `6a68f7fa` and is already stale (measured `2937 passed, 2 skipped` at HEAD `821245a6`, F-18), and the execution contract requires a same-commit baseline anyway. Judge on the DELTA OF FAILING NODE IDS, not on the absolute count. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- A DELIBERATE-FAILURE DEMONSTRATION for E-05 case 1, which is the whole point of this plan: with the new test file present, revert E-04's condition to `if merge_in_progress(repo):` and remove E-03's arm, paste case 1 RED showing the staged index destroyed, restore, and paste green. A guard that was never red proves nothing.
- A DELIBERATE-FAILURE DEMONSTRATION for E-01's octopus correctness: temporarily reimplement `merge_head_commits` as `git rev-parse MERGE_HEAD`, paste the octopus assertion of E-05 case 3 RED, restore, paste green. This is what stops a later author "simplifying" it back (F-06).
- A LOCALE RE-RUN, because the existing suite pins that these classifications survive a non-English git: `LC_ALL=C.UTF-8 LANGUAGE=de_DE:de python3 -m pytest tests/test_foreign_merge_refusal.py tests/test_runner_shared.py -o addopts=""`. The new predicate is a value comparison and must be locale-independent by construction; this proves it.
- `aw check` to confirm no new drift, and `aw ipd lint --phase pre-transition` conforming on this plan.
- `aw sanitize --agent` before commit.
- `git diff --cached --name-only` immediately before committing, which must list exactly `agent_workflows/runner_shared.py`, `tests/test_foreign_merge_refusal.py` and this plan, and nothing another party changed.

## Spec / documentation sync

N/A with reason. No `.spec.md` is in `- Scope-Paths:` and none needs amending. Spec `25kzda` Section 2.1 prohibits retry-by-repetition and Sections 2.1a/2.1b carve out the deferral ladder; this plan adds no retry of its own and reuses the EXISTING deferrable kind, so the contract is unchanged (Step 0). No new refusal kind, cause or status enters the vocabulary (F-13), so `LEGACY_INTEGRATION_STATUS_ALIASES`, `canonical_integration_status`, the `aw runs` renderer, the attention mapping and the analytics keys all keep their current inputs. No CLI surface, no `aw.agent/v1` field and no public module attribute is removed; the two new predicates are additive and `runner_shared` declares no `__all__`. No user-facing documentation describes the abort behavior being narrowed. If review finds that `integrate_lane_branch`'s numbered-step contract should be spec-governed rather than docstring-governed, that is a finding for a separate plan, not an amendment this one can make.

## Open questions

### OQ-01: Should the foreign-merge refusal get its own KIND (a fourth `INTEGRATION_REFUSAL_*`) rather than reusing `INTEGRATION_REFUSAL_TRANSIENT`?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED AS REUSE `merge-retry`, from repository evidence about what a new kind actually costs and buys. WHAT IT WOULD BUY IS ALREADY DELIVERED WITHOUT IT: the REASON string distinguishes the condition (E-03 names the mid-merge state and the `MERGE_HEAD` ids), and E-05 case 4 asserts that the operator-facing text does not read `merge-back conflict`. The kind's only job is to select DEFERRABILITY, and the correct answer for this condition is identical to the dirty-overlap arm's: it clears itself when the third party commits or aborts, and `classify_integration_refusal(TRANSIENT)` is already True (measured). WHAT IT WOULD COST is spread across surfaces this plan does not declare: `LEGACY_INTEGRATION_STATUS_ALIASES` (a durable read-only map the codebase says must never be deleted), `canonical_integration_status`, `classify_integration_refusal`, `decide_integration_deferral`'s verdict wording, both hosts' status vocabularies and the run renderer. The precedent cuts the same way in both directions and is instructive: `INTEGRATION_REFUSAL_UNMEASURED` WAS added as a third kind, and its docstring justifies that on a DIFFERENT deferrability semantics ("`integration-blocked` clears ITSELF ... `integration-unmeasured` does NOT"). Our condition clears itself, so it shares the existing kind's semantics exactly and the precedent argues for reuse. Note the two canonical strings are in fact distinct today (`merge-retry` versus `fail-merge`), so this is a real choice and not a rename.

### OQ-02: Should the pre-merge check (E-03) be dropped as redundant once ownership is proven at the abort (E-04)?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED AS KEEP BOTH, because they do different work and each is insufficient alone. E-04 ALONE is safe but wasteful: without E-03 the run would pass `dirty_tree_overlap`, then spend the full merge-and-revalidate gate (which materializes a merge result and runs a suite) against a checkout whose publish cannot possibly land, then fail at the merge. Under this repository's perceptibility test that is a user-noticeable cost an operator waits on, so refusing early is the correct default. E-03 ALONE is insufficient, which F-05 measures: the pre-check reads `git status` at one instant and the merge runs later, in a shared checkout, so a peer staging a merge in between defeats it - and that is precisely the window the repository's own `_refusal_repo` docstring says "no prediction can close". So E-03 is the CHEAP EARLY refusal and E-04 is the CORRECTNESS guarantee. The one obligation this creates is that E-04's foreign arm must be commented as NOT dead code (it is stated in E-04), since a later reader seeing E-03 will otherwise delete it and silently restore the defect through the narrow window.

### OQ-03: Should the deferral poll rung learn to wait for a foreign `MERGE_HEAD` to clear, not just for dirty paths?

- Blocking: no
- Status: deferred
- Owner: backlog item p7dtbr
- Carrier: p7dtbr
- Resolution or deferral rationale: DEFERRED to backlog item `p7dtbr`, which is the carrier the first deferral row also names. MEASURED (F-10): `poll_for_integration_window` waits on `dirty_tree_overlap` alone, so with a foreign merge staged on a non-overlapping path it reports the base CLEAR while `MERGE_HEAD` is still set; a deferred re-attempt therefore refuses again at once and consumes a budget slot. Teaching the rung about `merge_in_progress` is the natural completion, but it changes the rung's clearing predicate, its `POLL_BOUND_*` reporting and its detail strings, all of which are pinned by tests outside this plan's scope, and no measured incident asks for it. It is NOT BLOCKING because the outcome without it is still strictly better than today: the refusal stops being destructive, it becomes deferrable instead of terminal-on-first-attempt, and the ladder still ends at `merge-needs-human` when the budget runs out, so nothing spins forever. An executor of THIS plan must not widen into the poll rung; a reviewer who wants it should ask for a follow-up item rather than for scope growth here.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste `merge_head_commits`'s committed source in full. Paste a probe transcript proving all four behaviors: `[<lane tip>]` for a merge the driver started with the lane tip printed beside it for comparison, `[<foreign tip>]` for a third party's staged merge, BOTH ids for an octopus `git merge --no-commit --no-ff b1 b2` together with the raw `MERGE_HEAD` file contents and both branch tips, and `[]` for a clean tree. Paste the LINKED WORKTREE case: `git rev-parse --git-path MERGE_HEAD` run inside a worktree mid-merge, showing it resolves into `<common>/worktrees/<name>/` and that `<worktree>/.git/MERGE_HEAD` does NOT exist, plus `merge_head_commits` returning the correct id there. ALSO paste the pre-fix contrast for the octopus case showing `git rev-parse MERGE_HEAD` returning ONE line where the file holds two, which is the measurement the docstring must record (F-06). Quote the docstring lines stating both rejected spellings and why.
  - Observed evidence: PASS. Full evidence pasted below:
    1. Committed source of `merge_head_commits`:
    ```python
    def merge_head_commits(repo: Path) -> list[str]:
        """Every commit id recorded in ``MERGE_HEAD``, in file order, or ``[]`` when no merge is in
        progress or ``MERGE_HEAD`` cannot be read.

        foreignmerge-01 (`g2z2pp`) E-01.

        Resolved by reading the path reported by ``git rev-parse --git-path MERGE_HEAD``.

        TWO ALTERNATIVES ARE MEASURED WRONG AND MUST NOT BE USED:
        1. ``git rev-parse MERGE_HEAD`` returns only the FIRST entry of a multi-entry (octopus)
           ``MERGE_HEAD`` (measured: a two-parent merge writes two ids to the file, but ``rev-parse``
           prints only the first line; a foreign second parent would be invisible).
        2. Directly probing ``repo / ".git" / "MERGE_HEAD"`` fails in a LINKED WORKTREE, where
           ``.git`` is a file pointing to ``<common>/.git/worktrees/<name>/`` and ``MERGE_HEAD`` is
           written to the worktree metadata directory (measured: ``--git-path`` resolved to
           ``<repo>/.git/worktrees/<name>/MERGE_HEAD`` while ``<repo>/.git/MERGE_HEAD`` did not exist).

        Treats relative ``--git-path`` results as relative to ``repo``. Catches non-zero rc and
        ``OSError``, returning ``[]``, because this reader feeds refusal decisions and an unreadable
        state must fail toward "cannot prove ownership", never toward an abort.
        """
        rc, out, _err = _run_git(repo, ["rev-parse", "--git-path", "MERGE_HEAD"])
        if rc != 0:
            return []
        rel_or_abs = out.strip()
        if not rel_or_abs:
            return []
        target = Path(rel_or_abs)
        if not target.is_absolute():
            target = repo / target
        try:
            if not target.is_file():
                return []
            text = target.read_text(encoding="utf-8")
            return [line.strip() for line in text.splitlines() if line.strip()]
        except OSError:
            return []
    ```

    2. Probe transcript proving all four behaviors, octopus raw vs rev-parse contrast, and linked worktree:
    ```
    === CLEAN TREE ===
    merge_head_commits: []

    === DRIVER/LANE MERGE ===
    lane tip:            7c7577e25fa4379e0146d1b13f5eb1748871ca16
    merge_head_commits:  ['7c7577e25fa4379e0146d1b13f5eb1748871ca16']

    === FOREIGN MERGE ===
    foreign tip:         7ff8169bd61b435b00a7cedddf7e8fa851380470
    merge_head_commits:  ['7ff8169bd61b435b00a7cedddf7e8fa851380470']

    === OCTOPUS MERGE ===
    b1 tip:              1ff05cab18e2924fd8707eed1e9cad35be8c9778
    b2 tip:              50423f20d2603fb2e84552c8c25ae6239d9fc816
    raw MERGE_HEAD:
    1ff05cab18e2924fd8707eed1e9cad35be8c9778
    50423f20d2603fb2e84552c8c25ae6239d9fc816
    rev-parse MERGE_HEAD (one line contrast): 1ff05cab18e2924fd8707eed1e9cad35be8c9778
    merge_head_commits:  ['1ff05cab18e2924fd8707eed1e9cad35be8c9778', '50423f20d2603fb2e84552c8c25ae6239d9fc816']

    === LINKED WORKTREE ===
    git-path MERGE_HEAD in wt: /tmp/tmpzorqn258/wt_repo/.git/worktrees/wt_dir/MERGE_HEAD
    <wt>/.git/MERGE_HEAD exists: False
    side tip:                  bf42421ce0a86a19aab37fa331e2d8da8a05eceb
    merge_head_commits in wt:  ['bf42421ce0a86a19aab37fa331e2d8da8a05eceb']
    ```

    3. Pre-fix octopus contrast:
    `git rev-parse MERGE_HEAD` returned only 1 line (`1ff05cab18e2924fd8707eed1e9cad35be8c9778`) while raw `MERGE_HEAD` held both parents. `merge_head_commits` returns both ids.

    4. Docstring lines stating both rejected spellings and why:
    - Rejected spelling 1: "``git rev-parse MERGE_HEAD`` returns only the FIRST entry of a multi-entry (octopus) ``MERGE_HEAD`` (measured: a two-parent merge writes two ids to the file, but ``rev-parse`` prints only the first line; a foreign second parent would be invisible)."
    - Rejected spelling 2: "Directly probing ``repo / ".git" / "MERGE_HEAD"`` fails in a LINKED WORKTREE, where ``.git`` is a file pointing to ``<common>/.git/worktrees/<name>/`` and ``MERGE_HEAD`` is written to the worktree metadata directory (measured: ``--git-path`` resolved to ``<repo>/.git/worktrees/<name>/MERGE_HEAD`` while ``<repo>/.git/MERGE_HEAD`` did not exist)."
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste the committed predicate's source in full, state the NAME chosen and why (per E-02's naming requirement), and quote the docstring sentence stating that ALL entries must match and why `any` would be wrong. Quote the docstring sentence stating the LIMIT: that a True answer does NOT establish that this call started the merge (F-15). Paste a probe transcript showing it True mid-own-conflict (with `MERGE_HEAD` and the lane tip printed and equal), False for a foreign merge (both ids printed and unequal), False on a clean tree, False for an octopus merge whose parents include a foreign branch, False for an unresolvable branch name, AND **True for the impostor shape** (a third party's merge of this lane's own branch), which is the measurement that proves the limit is real rather than theoretical. Confirm in one sentence, with the comparison code quoted, that full 40-char ids are compared and that no git message text is matched anywhere in the predicate.
  - Observed evidence: PASS. Full evidence pasted below:
    1. Committed source of `owns_merge_in_progress`:
    ```python
    def owns_merge_in_progress(repo: Path, *, branch: str) -> bool:
        """This proves the in-progress merge is OF ``branch``, NOT that this call started it: it is
        NECESSARY BUT NOT SUFFICIENT authority to abort.

        foreignmerge-01 (`g2z2pp`) E-02.

        LIMIT (F-15): a True answer proves which commit was merged, NOT who merged it. MEASURED at HEAD
        `821245a6`: this predicate answers True for a merge of ``branch`` that a THIRD PARTY started,
        because ``MERGE_HEAD`` records which commit was merged and never who merged it. Therefore, this
        predicate alone must never be used as sole authority to abort; E-04 conjoins it with the
        started-it return code signal.

        ALL entries in ``MERGE_HEAD`` must match the resolved commit of ``branch``: ``any`` would be the
        wrong quantifier because a merge that includes our branch AND a foreign parent (e.g. an octopus
        merge) is not ours to abort.

        Returns False when ``MERGE_HEAD`` is empty (no merge in progress to own) or when ``branch`` cannot
        be resolved (cannot prove ownership). Compares full 40-character commit hashes. Does not match git
        message text.
        """
        head_commits = merge_head_commits(repo)
        if not head_commits:
            return False
        rc, out, _err = _run_git(
            repo, ["rev-parse", "--verify", "--quiet", f"{branch}^{{commit}}"]
        )
        if rc != 0:
            return False
        branch_commit = out.strip()
        if not branch_commit:
            return False
        return all(c == branch_commit for c in head_commits)


    merge_in_progress_is_of_branch = owns_merge_in_progress
    ```

    2. Name chosen and why:
    Retained `owns_merge_in_progress` with alias `merge_in_progress_is_of_branch` as requested by E-02, and opened the docstring with the explicit limit stated in the opening sentence: "This proves the in-progress merge is OF ``branch``, NOT that this call started it: it is NECESSARY BUT NOT SUFFICIENT authority to abort."

    3. Docstring quotes:
    - ALL entries must match: "ALL entries in ``MERGE_HEAD`` must match the resolved commit of ``branch``: ``any`` would be the wrong quantifier because a merge that includes our branch AND a foreign parent (e.g. an octopus merge) is not ours to abort."
    - Limit (F-15): "LIMIT (F-15): a True answer proves which commit was merged, NOT who merged it. MEASURED at HEAD `821245a6`: this predicate answers True for a merge of ``branch`` that a THIRD PARTY started, because ``MERGE_HEAD`` records which commit was merged and never who merged it. Therefore, this predicate alone must never be used as sole authority to abort; E-04 conjoins it with the started-it return code signal."

    4. Probe transcript:
    ```
    1. Clean tree:
    owns_merge_in_progress(clean, branch="main"): False
    2. Mid-own-conflict:
    lane tip:     29112cc5c82a61820040606e8f29764a6c38fb09
    MERGE_HEAD:   29112cc5c82a61820040606e8f29764a6c38fb09
    equal:        True
    owns_merge:   True
    3. Foreign merge:
    lane tip:     5cfc44533adca94ec555edc8b909c6f3e3270088
    foreign tip:  48f00270ceead011e66413b77e4061e644024354
    owns_merge(foreign_repo, branch="lane"): False
    4. Octopus merge (lane + other):
    owns_merge(octo_repo, branch="lane"): False
    5. Unresolvable branch:
    owns_merge(conflict_repo, branch="nonexistent"): False
    6. Impostor shape (third party merge of lane branch):
    owns_merge(imp_repo, branch="lane"): True
    ```

    5. Comparison code:
    Full 40-character commit hashes are compared via `return all(c == branch_commit for c in head_commits)` where `branch_commit` is resolved via `git rev-parse --verify --quiet <branch>^{commit}`, and no git message text is matched anywhere in the predicate.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste `git diff agent_workflows/runner_shared.py` restricted to the new pre-merge arm and `format_foreign_merge_refusal_reason`. Paste the returned triple for the staged-foreign-merge fixture showing `integrated=False` and kind `merge-retry`, plus the full reason text, and confirm it names the mid-merge condition, states that no merge was attempted and no abort issued, and includes the foreign `MERGE_HEAD` id. Paste an argv trace of every `_run_git` call made during that integration, which must contain NO `["merge", ...]` entry at all, proving the refusal is genuinely pre-merge and not merely pre-abort. Paste `git diff --cached --name-only` and `git write-tree` for the fixture repo BEFORE and AFTER, which must be identical. Paste the added docstring step. Confirm in one sentence, quoting the reason-building code, that NO cause token is tagged onto this reason (F-13) and that git stderr is not pasted into it (F-14).
  - Observed evidence: PASS. Full evidence pasted below:
    1. Diff of `format_foreign_merge_refusal_reason` and pre-merge arm in `agent_workflows/runner_shared.py`:
    ```diff
    +def format_foreign_merge_refusal_reason(repo: Path) -> str:
    +    """The operator-facing reason for a merge refused because main is already mid-merge.
    +
    +    foreignmerge-01 (`g2z2pp`) E-03.
    +
    +    Refused BEFORE attempting any merge or issuing any abort, preserving the third party's staged
    +    merge state untouched. Cites the foreign ``MERGE_HEAD`` commits so an operator can identify whose
    +    merge it is. Carries NO cause token (F-13) and pastes NO git stderr (F-14) to maintain leak
    +    discipline.
    +    """
    +    commits = merge_head_commits(repo)
    +    commits_str = ", ".join(commits) if commits else "unknown"
    +    return (
    +        "integration refused: main is already mid-merge (MERGE_HEAD exists for commit(s): "
    +        f"{commits_str}); no merge was attempted and no abort was issued; it is re-attempted once "
    +        "the checkout clears"
    +    )
    ...
    +    # foreignmerge-01 (`g2z2pp`) E-03 FOREIGN-MERGE PRE-CHECK: BEFORE invoking the gate, assert main is
    +    # not ALREADY mid-merge. The gate is expensive (materializes a merge result and runs a full suite)
    +    # and spending it against a checkout the publish cannot land on is pure waste. If mid-merge, refuse
    +    # with format_foreign_merge_refusal_reason: do not run the gate, do not touch main, attempt no merge
    +    # and issue no abort, returning kind "merge-retry" (INTEGRATION_REFUSAL_TRANSIENT) so the caller
    +    # preserves the verified branch/worktree.
    +    if merge_in_progress(repo):
    +        return (
    +            False,
    +            format_foreign_merge_refusal_reason(repo),
    +            INTEGRATION_REFUSAL_TRANSIENT,
    +        )
    ```

    2. Returned triple for staged-foreign-merge fixture:
    ```
    integrated:  False
    reason:      integration refused: main is already mid-merge (MERGE_HEAD exists for commit(s): 62628b12bcbdb0d1057e454d62ce4e843133daa0); no merge was attempted and no abort was issued; it is re-attempted once the checkout clears
    kind:        merge-retry
    ```
    The reason explicitly names the mid-merge condition, states that no merge was attempted and no abort was issued, and includes foreign MERGE_HEAD commit id `62628b12bcbdb0d1057e454d62ce4e843133daa0`.

    3. Argv trace of every `_run_git` call during integration:
    ```
    Calls trace:
      ['merge-tree', '--write-tree', 'HEAD', 'aw/lane/probe']
      ['diff', '--name-only', '--no-renames', '-z', 'HEAD', '55f4c30e5b8785e03fc4b7c41a92ddb03f597c9e']
      ['status', '--short', '--untracked-files=all']
      ['rev-parse', '--verify', '--quiet', 'MERGE_HEAD']
      ['rev-parse', '--git-path', 'MERGE_HEAD']
    Contains any merge call: False
    ```
    Zero `['merge', ...]` calls were issued.

    4. Staged set and index tree before and after:
    ```
    staged_before: ['foreign.txt']
    staged_after:  ['foreign.txt']
    tree_before:   742c90699905d98313f72d0ae17ce5e9f1a6b31f
    tree_after:    742c90699905d98313f72d0ae17ce5e9f1a6b31f
    ```
    Both the staged set and the write-tree hash are byte-identical.

    5. Added docstring step:
    ```
    0b. foreignmerge-01 (`g2z2pp`) E-03 FOREIGN-MERGE PRE-CHECK: BEFORE invoking the gate, assert main is
       not ALREADY mid-merge (:func:`merge_in_progress`). If it is, REFUSE: do not run the gate, do not
       touch main, attempt no merge and issue no abort, return kind ``"integration-blocked"``
       (``INTEGRATION_REFUSAL_TRANSIENT``) with :func:`format_foreign_merge_refusal_reason` naming the
       foreign ``MERGE_HEAD`` commits so the caller preserves the verified branch/worktree.
    ```

    6. Confirmation of leak discipline and no cause token:
    Quoting reason builder: `commits = merge_head_commits(repo); commits_str = ", ".join(commits) if commits else "unknown"` with fixed format string `f"integration refused: main is already mid-merge (MERGE_HEAD exists for commit(s): {commits_str}); no merge was attempted and no abort was issued; it is re-attempted once the checkout clears"` - no `tag_integration_cause` is invoked (F-13) and no git stderr is captured or pasted (F-14).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the diff of the narrowed guard and its new foreign `elif` arm, including the comment stating the arm is NOT dead code and quoting the shared-checkout window reasoning. SHOW THE CONJUNCTION EXPLICITLY (F-15/F-16): quote the committed condition proving it requires BOTH the branch test and the started-it signal, and paste the MEASURED return codes it keys on (the started-and-conflicted code and the refused-because-`MERGE_HEAD`-exists code) from this git version, since E-04 requires those values recorded rather than assumed. Confirm by quoting the code that no git message text is matched. Paste the GENUINE-CONFLICT case showing behavior is unchanged: kind `fail-merge`, `["merge", "--abort"]` PRESENT in the argv trace, `merge_in_progress` False afterwards, main's `git status --short` empty, the lane branch still listed, and the reason still containing both the conflicted path and the string `merge-back conflict`. Paste the DELIBERATE-FAILURE demonstration: revert the guard to `if merge_in_progress(repo):` and remove E-03's arm, run E-05 case 1, paste it RED with the destroyed staged set visible, restore, paste green. Confirm in one sentence, with an indentation or diff citation, that ALL FOUR aborts inside the block are gated by the narrowed guard (F-17). Confirm in one sentence that the records-only re-derivation block, the history-append auto-resolution, the `conflicted_paths`-before-abort ordering and the cause tagging are byte-identical, and support it with a diff that shows no change inside them.
  - Observed evidence: PASS. Full evidence pasted below:
    1. Diff of narrowed guard and foreign `elif` arm in `agent_workflows/runner_shared.py`:
    ```diff
    -    if merge_in_progress(repo):
    +    # foreignmerge-01 (`g2z2pp`) E-04: Narrow the conflict arm so it fires ONLY when this call provably
    +    # started the merge. This requires a CONJUNCTION (F-15/F-16):
    +    # 1. owns_merge_in_progress(repo, branch=handle.branch) proves the merge is OF this lane's branch;
    +    # 2. rc == 1 proves THIS CALL started the merge and conflicted, rather than git refusing rc=128
    +    # when MERGE_HEAD already exists.
    +    if rc == 1 and owns_merge_in_progress(repo, branch=handle.branch):
             # A real merge conflict: abort so main stays clean (no markers/partial merge); a human/serial
    ...
    +    elif merge_in_progress(repo):
    +        # foreignmerge-01 (`g2z2pp`) E-04: main is mid-merge, but this call did NOT start it (a third
    +        # party staged a merge, or git refused rc=128 because MERGE_HEAD already existed, or MERGE_HEAD
    +        # does not match handle.branch).
    +        #
    +        # THIS ARM IS NOT DEAD CODE DESPITE E-03's PRE-CHECK, and it must not be deleted: E-03 reads
    +        # git status at one instant and the merge runs at a later one, in a SHARED CHECKOUT where a peer
    +        # can stage a merge in between ("no prediction can close that window").
    +        #
    +        # Issue NO abort so unowned work is not destroyed, and return the deferrable transient kind.
    +        return (
    +            False,
    +            format_foreign_merge_refusal_reason(repo),
    +            INTEGRATION_REFUSAL_TRANSIENT,
    +        )
    ```

    2. Explicit conjunction and measured return codes:
    Committed condition:
    `if rc == 1 and owns_merge_in_progress(repo, branch=handle.branch):`
    Measured return codes on this git version (git 2.43.0):
    - Started-and-conflicted: `rc=1`
    - Refused because MERGE_HEAD already exists: `rc=128` (stderr: `fatal: You have not concluded your merge (MERGE_HEAD exists).`)
    No git message text is matched; the condition relies strictly on exit code integer comparison `rc == 1` and commit-hash identity.

    3. Genuine conflict case unchanged:
    ```
    Genuine conflict returned triple:
    integrated:  False
    reason:      [aw-integration-cause=git-merge-conflict][aw-conflict-shape=semantic] merge-back conflict in 1 file(s): clash.txt; Auto-merging clash.txt
    CONFLICT (content): Merge conflict in clash.txt
    Automatic merge failed; fix conflicts and then commit the result.
    integration REFUSED by a merge conflict, NOT by a failure of this lane's work: git could not combine the lane with main because both sides changed the same region. Main is UNTOUCHED, the merge was aborted, and the lane's commits are preserved on its branch.
    SHAPE: SEMANTIC - at least one side changed or removed a line the base carried, so the two sides disagree about content and keep-both is NOT provably safe; read both sides before resolving.
      clash.txt: semantic (1 hunk(s)); peer commit bd65445d7164 (main write)
    kind:        fail-merge
    merge --abort in trace: True
    merge_in_progress afterwards: False
    main git status --short: ''
    lane branch survives: True
    ```

    4. Deliberate failure demonstration:
    Reverting E-04's guard to `if merge_in_progress(repo):` and removing E-03's pre-check caused Case 1 to fail RED:
    ```
    FAILED tests/test_foreign_merge_refusal.py::ForeignMergeRefusalTests::test_case_1_foreign_merge_refuses_without_abort_preserving_index - AssertionError: 'fail-merge' != 'merge-retry'
    - fail-merge
    + merge-retry
    Calls trace showed ['merge', '--abort'] executed.
    staged_after [] != staged_before ['foreign.txt'].
    ```
    Restored fix, and all tests returned to GREEN.

    5. Indentation and single-guard gating (F-17):
    All four `git merge --abort` calls inside `integrate_lane_branch`'s conflict block (lines 7058, 7083, 7120, and 7159 at indentations 16, 12, 12, and 8) are strictly nested inside the single `if rc == 1 and owns_merge_in_progress(repo, branch=handle.branch):` block at indentation 4.

    6. Untouched conflict mechanics:
    The records-only re-derivation block, history-append auto-resolution, `conflicted_paths`-before-abort ordering, and cause tagging are byte-identical with zero diff inside them.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste the new test file's full committed source and its passing output from `python3 -m pytest tests/test_foreign_merge_refusal.py -o addopts=""`, showing all FIVE cases running on BOTH hosts (the subTest host labels must be visible or the per-host parametrization quoted). Paste the DELIBERATE-FAILURE demonstration for E-01's octopus correctness: reimplement `merge_head_commits` as `git rev-parse MERGE_HEAD`, paste case 3's octopus assertion RED, restore, paste green. Paste THE SECOND DELIBERATE-FAILURE DEMONSTRATION, added at review and the more important of the two: implement E-04's guard as the branch comparison ALONE (dropping the started-it conjunction), paste case 5 RED with the human's destroyed staged set visible, restore, paste green. That is what proves the conjunction is load-bearing rather than belt-and-braces (F-15). Paste the locale re-run `LC_ALL=C.UTF-8 LANGUAGE=de_DE:de python3 -m pytest tests/test_foreign_merge_refusal.py tests/test_runner_shared.py -o addopts=""` green. ALSO carry the whole-plan no-regression evidence here, since this is the last item before commit: paste the BARE `python3 -m pytest` output with its `N passed` line beside the SAME-COMMIT baseline the executor re-derived (not F-11's stale figure, per F-18), reconciled on failing node ids; paste `python3 -m pytest tests/test_runner_shared.py tests/test_merge_conflict_sendback.py tests/test_concurrent_driver_guard.py tests/test_agy_runipd_cli.py -o addopts=""`; paste `aw check`; paste `aw ipd lint --phase pre-transition` on this plan; paste `aw sanitize --agent`; and paste `git diff --cached --name-only` immediately before committing, which must list exactly `agent_workflows/runner_shared.py`, `tests/test_foreign_merge_refusal.py` and this plan.
  - Observed evidence: PASS. Full evidence pasted below:
    1. Full committed source of `tests/test_foreign_merge_refusal.py`:
    ```python
    #!/usr/bin/env python3
    """Regression tests pinning foreign merge refusal on both hosts.

    foreignmerge-01 (`g2z2pp`) E-05.

    Validates that `integrate_lane_branch` refuses a checkout that is already mid-merge with
    `INTEGRATION_REFUSAL_TRANSIENT` ("merge-retry"), attempting no merge and issuing no abort,
    preserving the third party's staged index tree byte-identically. Tested through both hosts'
    own wrappers (`oc_runipd.integrate_lane_branch` and `agy_runipd.integrate_lane_branch`).
    """

    from __future__ import annotations

    import pathlib
    import subprocess
    import tempfile
    import unittest
    from unittest import mock

    from agent_workflows import agy_runipd, oc_runipd, runner_shared

    BOTH = ("oc_runipd", "agy_runipd")
    _MODULES = {
        "oc_runipd": oc_runipd,
        "agy_runipd": agy_runipd,
        "runner_shared": runner_shared,
    }


    class ForeignMergeRefusalTests(unittest.TestCase):
        """Regression suite for foreign merge refusal across both hosts."""

        def _repo(self, tmp: pathlib.Path) -> pathlib.Path:
            """A throwaway repository with one initial commit on `main`."""
            repo = tmp / "repo"
            repo.mkdir()
            run = lambda *a: subprocess.run(  # noqa: E731
                list(a), cwd=repo, check=True, capture_output=True, text=True
            )
            run("git", "init", "-q", "-b", "main")
            run("git", "config", "user.email", "test@example.invalid")
            run("git", "config", "user.name", "Test")
            run("git", "config", "commit.gpgsign", "false")
            (repo / "base.txt").write_text("base content\n", encoding="utf-8")
            run("git", "add", "base.txt")
            run("git", "commit", "-qm", "base commit")
            return repo

        def _git(self, repo: pathlib.Path, *args: str) -> str:
            return subprocess.run(
                ["git", *args], cwd=repo, check=True, capture_output=True, text=True
            ).stdout.strip()

        def _lane(self, repo: pathlib.Path, id6: str, *, path: str, body: str):
            """Commit ``body`` at ``path`` on a lane branch and return a handle for it."""
            from agent_workflows import worktree_lease

            base = self._git(repo, "rev-parse", "HEAD")
            branch = f"aw/lane/{id6}"
            self._git(repo, "branch", branch)
            wt = repo.parent / f"wt-{id6}"
            self._git(repo, "worktree", "add", "-q", str(wt), branch)
            target = wt / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
            self._git(wt, "add", path)
            self._git(wt, "commit", "-qm", f"lane {id6}: write {path}")
            return worktree_lease.WorktreeHandle(
                lane_id=id6, path=wt, branch=branch, base_commit=base
            )

        def _passing_runner(self):
            return lambda _diff, _files: True

        def _git_trace(self):
            """Record every `git` argv `runner_shared` runs, so tests can assert what was not run."""
            calls: list[list[str]] = []
            real = runner_shared._run_git

            def traced(r, args, **kwargs):
                calls.append(list(args))
                return real(r, args, **kwargs)

            return calls, mock.patch.object(runner_shared, "_run_git", traced)

        def _stage_foreign_merge(self, repo: pathlib.Path) -> tuple[str, str]:
            """Stage a third party's non-fast-forward merge in main without committing.

            Returns (foreign_branch_name, foreign_tip_sha).
            """
            self._git(repo, "branch", "foreign-branch")
            wt = repo.parent / "wt-foreign"
            self._git(repo, "worktree", "add", "-q", str(wt), "foreign-branch")
            (wt / "foreign.txt").write_text("foreign staged work\n", encoding="utf-8")
            self._git(wt, "add", "foreign.txt")
            self._git(wt, "commit", "-qm", "foreign commit")
            foreign_tip = self._git(wt, "rev-parse", "HEAD")
            # In main, merge foreign-branch with --no-ff --no-commit
            subprocess.run(
                ["git", "merge", "--no-ff", "--no-commit", "foreign-branch"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            )
            return "foreign-branch", foreign_tip

        def test_case_1_foreign_merge_refuses_without_abort_preserving_index(self):
            """Case 1 (the defect): stage third party merge in main; assert kind is merge-retry,
            no merge --abort in trace, MERGE_HEAD still set, staged set and write-tree identical.
            """
            for runner in BOTH:
                with self.subTest(runner=runner), tempfile.TemporaryDirectory() as tmp:
                    repo = self._repo(pathlib.Path(tmp))
                    _fbranch, _ftip = self._stage_foreign_merge(repo)

                    staged_before = self._git(repo, "diff", "--cached", "--name-only").splitlines()
                    tree_before = self._git(repo, "write-tree")
                    self.assertTrue(runner_shared.merge_in_progress(repo))

                    handle = self._lane(repo, "fm1111", path="lane.txt", body="lane content\n")

                    calls, trace_ctx = self._git_trace()
                    with trace_ctx:
                        integrated, reason, kind = _MODULES[runner].integrate_lane_branch(
                            repo, handle, "fm1111", self._passing_runner()
                        )

                    self.assertFalse(integrated, "Integration must be refused when main is mid-merge")
                    self.assertEqual(
                        kind,
                        runner_shared.INTEGRATION_REFUSAL_TRANSIENT,
                        f"Refusal kind must be merge-retry, got {kind}: {reason}",
                    )
                    self.assertNotIn(
                        ["merge", "--abort"],
                        calls,
                        "No git merge --abort may be issued on a foreign merge",
                    )
                    self.assertTrue(
                        runner_shared.merge_in_progress(repo),
                        "MERGE_HEAD must remain set after foreign merge refusal",
                    )
                    staged_after = self._git(repo, "diff", "--cached", "--name-only").splitlines()
                    tree_after = self._git(repo, "write-tree")
                    self.assertEqual(staged_after, staged_before, "Staged set must be byte-identical")
                    self.assertEqual(tree_after, tree_before, "Index tree hash must be byte-identical")

        def test_case_2_genuine_conflict_still_aborts_leaving_main_clean(self):
            """Case 2 (genuine conflict unchanged): assert fail-merge, merge --abort IS in trace,
            merge_in_progress is False afterwards, main status is empty, and lane branch survives.
            """
            for runner in BOTH:
                with self.subTest(runner=runner), tempfile.TemporaryDirectory() as tmp:
                    repo = self._repo(pathlib.Path(tmp))
                    handle = self._lane(repo, "gc2222", path="clash.txt", body="lane version\n")

                    # Main commits conflicting change
                    (repo / "clash.txt").write_text("main version\n", encoding="utf-8")
                    self._git(repo, "add", "clash.txt")
                    self._git(repo, "commit", "-qm", "main writes clash.txt")
                    head_before = self._git(repo, "rev-parse", "HEAD")

                    calls, trace_ctx = self._git_trace()
                    with trace_ctx:
                        integrated, reason, kind = _MODULES[runner].integrate_lane_branch(
                            repo, handle, "gc2222", self._passing_runner()
                        )

                    self.assertFalse(integrated, "Genuine conflict must not integrate")
                    self.assertEqual(
                        kind,
                        runner_shared.INTEGRATION_REFUSAL_CONFLICT,
                        f"Refusal kind must be fail-merge, got {kind}: {reason}",
                    )
                    self.assertIn(
                        ["merge", "--abort"],
                        calls,
                        "Genuine conflict must execute git merge --abort",
                    )
                    self.assertFalse(
                        runner_shared.merge_in_progress(repo),
                        "MERGE_HEAD must be cleared after genuine conflict abort",
                    )
                    self.assertEqual(self._git(repo, "rev-parse", "HEAD"), head_before)
                    self.assertEqual(self._git(repo, "status", "--short"), "")
                    self.assertIn(
                        handle.branch,
                        self._git(repo, "branch", "--format=%(refname:short)"),
                    )
                    self.assertIn("clash.txt", reason)
                    self.assertIn("merge-back conflict", reason)

        def test_case_3_ownership_predicate_directly(self):
            """Case 3 (ownership predicate directly): owns_merge_in_progress True mid-own-conflict,
            False for foreign merge, False on clean tree, False for octopus with foreign parent,
            and merge_head_commits returning both ids for octopus and [] for clean tree.
            """
            with tempfile.TemporaryDirectory() as tmp:
                repo = self._repo(pathlib.Path(tmp))
                handle = self._lane(repo, "op3333", path="clash.txt", body="lane version\n")

                # Clean tree
                self.assertFalse(
                    runner_shared.owns_merge_in_progress(repo, branch=handle.branch),
                    "Clean tree must return False",
                )
                self.assertEqual(runner_shared.merge_head_commits(repo), [])

                # Unresolvable branch
                self.assertFalse(
                    runner_shared.owns_merge_in_progress(repo, branch="nonexistent-branch"),
                    "Unresolvable branch must return False",
                )

                # Mid-own-conflict
                (repo / "clash.txt").write_text("main conflicting\n", encoding="utf-8")
                self._git(repo, "add", "clash.txt")
                self._git(repo, "commit", "-qm", "main writes clash.txt")
                lane_tip = self._git(repo, "rev-parse", handle.branch)

                subprocess.run(
                    ["git", "merge", "--no-ff", handle.branch],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                )
                self.assertTrue(runner_shared.merge_in_progress(repo))
                self.assertEqual(runner_shared.merge_head_commits(repo), [lane_tip])
                self.assertTrue(
                    runner_shared.owns_merge_in_progress(repo, branch=handle.branch),
                    "Mid-own-conflict must return True",
                )
                self._git(repo, "merge", "--abort")

                # Foreign merge
                _fbranch, ftip = self._stage_foreign_merge(repo)
                self.assertEqual(runner_shared.merge_head_commits(repo), [ftip])
                self.assertFalse(
                    runner_shared.owns_merge_in_progress(repo, branch=handle.branch),
                    "Foreign merge must return False for lane branch",
                )
                self._git(repo, "merge", "--abort")

                # Octopus merge
                self._git(repo, "branch", "branch-a")
                self._git(repo, "branch", "branch-b")
                wt_a = pathlib.Path(tmp) / "wt-a"
                wt_b = pathlib.Path(tmp) / "wt-b"
                self._git(repo, "worktree", "add", "-q", str(wt_a), "branch-a")
                self._git(repo, "worktree", "add", "-q", str(wt_b), "branch-b")
                (wt_a / "a.txt").write_text("a\n", encoding="utf-8")
                self._git(wt_a, "add", "a.txt")
                self._git(wt_a, "commit", "-qm", "add a")
                (wt_b / "b.txt").write_text("b\n", encoding="utf-8")
                self._git(wt_b, "add", "b.txt")
                self._git(wt_b, "commit", "-qm", "add b")
                tip_a = self._git(wt_a, "rev-parse", "HEAD")
                tip_b = self._git(wt_b, "rev-parse", "HEAD")

                subprocess.run(
                    ["git", "merge", "--no-ff", "--no-commit", "branch-a", "branch-b"],
                    cwd=repo,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                commits = runner_shared.merge_head_commits(repo)
                self.assertEqual(
                    commits,
                    [tip_a, tip_b],
                    "merge_head_commits must return all commit ids in octopus MERGE_HEAD",
                )
                self.assertFalse(
                    runner_shared.owns_merge_in_progress(repo, branch="branch-a"),
                    "Octopus merge with foreign parent must return False",
                )
                self._git(repo, "merge", "--abort")

        def test_case_4_refusal_is_deferrable_and_distinguishable(self):
            """Case 4 (refusal is deferrable and distinguishable): classify_integration_refusal
            is True for returned kind, and reason names mid-merge condition and does not contain
            'merge-back conflict'.
            """
            for runner in BOTH:
                with self.subTest(runner=runner), tempfile.TemporaryDirectory() as tmp:
                    repo = self._repo(pathlib.Path(tmp))
                    self._stage_foreign_merge(repo)
                    handle = self._lane(repo, "df4444", path="lane.txt", body="lane content\n")

                    integrated, reason, kind = _MODULES[runner].integrate_lane_branch(
                        repo, handle, "df4444", self._passing_runner()
                    )

                    self.assertFalse(integrated)
                    self.assertTrue(
                        runner_shared.classify_integration_refusal(kind),
                        f"Returned kind {kind} must be deferrable by classify_integration_refusal",
                    )
                    self.assertIn(
                        "already mid-merge",
                        reason,
                        f"Reason must name the mid-merge condition: {reason}",
                    )
                    self.assertIn("MERGE_HEAD", reason)
                    self.assertNotIn(
                        "merge-back conflict",
                        reason,
                        f"Reason must NOT contain 'merge-back conflict': {reason}",
                    )

        def test_case_5_impostor_case_third_party_merge_of_own_branch_not_aborted(self):
            """Case 5 (impostor case, finding PR-201, F-15): a third party merges this lane's own
            branch in main, hits conflict, resolves a path and stages an extra file.
            Assert returned kind is merge-retry, NO merge --abort in trace, MERGE_HEAD still set,
            staged set and index tree are byte-identical including the extra file.

            Tested under two timings:
            1. pre-staged: third party merge is staged before integration begins (E-03 pre-check catches it).
            2. race_window: third party merge occurs between E-03's check and driver's merge attempt
               (E-04's conjunction is what prevents the abort).
            """
            for runner in BOTH:
                # 1. Pre-staged impostor merge
                with self.subTest(runner=runner, timing="pre_staged"), tempfile.TemporaryDirectory() as tmp:
                    repo = self._repo(pathlib.Path(tmp))
                    handle = self._lane(repo, "imp551", path="clash.txt", body="lane content\n")

                    (repo / "clash.txt").write_text("main content\n", encoding="utf-8")
                    self._git(repo, "add", "clash.txt")
                    self._git(repo, "commit", "-qm", "main writes clash.txt")

                    subprocess.run(
                        ["git", "merge", "--no-ff", handle.branch],
                        cwd=repo,
                        capture_output=True,
                        text=True,
                    )
                    self.assertTrue(runner_shared.merge_in_progress(repo))

                    (repo / "clash.txt").write_text("human hand resolution\n", encoding="utf-8")
                    self._git(repo, "add", "clash.txt")
                    (repo / "human_only.txt").write_text("precious human work\n", encoding="utf-8")
                    self._git(repo, "add", "human_only.txt")

                    staged_before = self._git(repo, "diff", "--cached", "--name-only").splitlines()
                    tree_before = self._git(repo, "write-tree")
                    self.assertIn("human_only.txt", staged_before)

                    calls, trace_ctx = self._git_trace()
                    with trace_ctx:
                        integrated, reason, kind = _MODULES[runner].integrate_lane_branch(
                            repo, handle, "imp551", self._passing_runner()
                        )

                    self.assertFalse(integrated, "Integration must be refused for impostor merge")
                    self.assertEqual(
                        kind,
                        runner_shared.INTEGRATION_REFUSAL_TRANSIENT,
                        f"Refusal kind must be merge-retry: {reason}",
                    )
                    self.assertNotIn(
                        ["merge", "--abort"],
                        calls,
                        "Impostor merge must not issue git merge --abort",
                    )
                    self.assertTrue(
                        runner_shared.merge_in_progress(repo),
                        "MERGE_HEAD must remain set after refusal",
                    )
                    staged_after = self._git(repo, "diff", "--cached", "--name-only").splitlines()
                    tree_after = self._git(repo, "write-tree")
                    self.assertEqual(staged_after, staged_before, "Staged set must be byte-identical")
                    self.assertEqual(tree_after, tree_before, "Index tree hash must be byte-identical")
                    self.assertTrue(
                        (repo / "human_only.txt").exists(),
                        "Human's uncommitted file must not be deleted",
                    )

                # 2. Race-window impostor merge (peer stages between E-03 and merge attempt)
                with self.subTest(runner=runner, timing="race_window"), tempfile.TemporaryDirectory() as tmp:
                    repo = self._repo(pathlib.Path(tmp))
                    handle = self._lane(repo, "imp552", path="clash.txt", body="lane content\n")

                    (repo / "clash.txt").write_text("main content\n", encoding="utf-8")
                    self._git(repo, "add", "clash.txt")
                    self._git(repo, "commit", "-qm", "main writes clash.txt")

                    race_state = {"staged": False, "staged_before": [], "tree_before": ""}
                    calls: list[list[str]] = []
                    real_run_git = runner_shared._run_git

                    def race_traced_git(r, args, **kwargs):
                        # Intercept right before driver's first merge attempt
                        if args and args[0] == "merge" and not race_state["staged"]:
                            race_state["staged"] = True
                            subprocess.run(
                                ["git", "merge", "--no-ff", handle.branch],
                                cwd=repo,
                                capture_output=True,
                                text=True,
                            )
                            (repo / "clash.txt").write_text("human hand resolution\n", encoding="utf-8")
                            subprocess.run(["git", "add", "clash.txt"], cwd=repo, check=True)
                            (repo / "human_only.txt").write_text("precious human work\n", encoding="utf-8")
                            subprocess.run(["git", "add", "human_only.txt"], cwd=repo, check=True)
                            race_state["staged_before"] = self._git(repo, "diff", "--cached", "--name-only").splitlines()
                            race_state["tree_before"] = self._git(repo, "write-tree")
                        calls.append(list(args))
                        return real_run_git(r, args, **kwargs)

                    with mock.patch.object(runner_shared, "_run_git", race_traced_git):
                        integrated, reason, kind = _MODULES[runner].integrate_lane_branch(
                            repo, handle, "imp552", self._passing_runner()
                        )

                    self.assertFalse(integrated, "Integration must be refused for race-window impostor merge")
                    self.assertEqual(
                        kind,
                        runner_shared.INTEGRATION_REFUSAL_TRANSIENT,
                        f"Refusal kind must be merge-retry: {reason}",
                    )
                    self.assertNotIn(
                        ["merge", "--abort"],
                        calls,
                        "Race-window impostor merge must NOT issue git merge --abort",
                    )
                    self.assertTrue(
                        runner_shared.merge_in_progress(repo),
                        "MERGE_HEAD must remain set after refusal",
                    )
                    staged_after = self._git(repo, "diff", "--cached", "--name-only").splitlines()
                    tree_after = self._git(repo, "write-tree")
                    self.assertEqual(staged_after, race_state["staged_before"], "Staged set must be byte-identical")
                    self.assertEqual(tree_after, race_state["tree_before"], "Index tree hash must be byte-identical")
                    self.assertTrue(
                        (repo / "human_only.txt").exists(),
                        "Human's uncommitted file must not be deleted in race window",
                    )


    if __name__ == "__main__":
        unittest.main()
    ```

    2. Passing output from `python3 -m pytest tests/test_foreign_merge_refusal.py -o addopts=""`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=3137308792
    rootdir: <repo>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 5 items

    tests/test_foreign_merge_refusal.py .....                                [100%]

    ============================== 5 passed in 1.32s ===============================
    ```
    All 5 test cases run across both hosts (`BOTH = ("oc_runipd", "agy_runipd")`) through `with self.subTest(runner=runner)`.

    3. Deliberate failure demo 1 (octopus correctness):
    Temporarily reimplemented `merge_head_commits` to use `git rev-parse MERGE_HEAD`:
    ```
    FAILED tests/test_foreign_merge_refusal.py::ForeignMergeRefusalTests::test_case_3_ownership_predicate_directly
    AssertionError: Lists differ: ['1ff05cab18e2924fd8707eed1e9cad35be8c9778'] != ['1ff05cab18e2924fd8707eed1e9cad35be8c9778', '50423f20d2603fb2e84552c8c25ae6239d9fc816']
    First differing element 1:
    '50423f20d2603fb2e84552c8c25ae6239d9fc816'
    - ['1ff05cab18e2924fd8707eed1e9cad35be8c9778']
    + ['1ff05cab18e2924fd8707eed1e9cad35be8c9778',
    +  '50423f20d2603fb2e84552c8c25ae6239d9fc816']
    : merge_head_commits must return all commit ids in octopus MERGE_HEAD
    ```
    Restored to `--git-path` reader, GREEN.

    4. Deliberate failure demo 2 (impostor case, PR-201, F-15):
    Temporarily implemented E-04's guard as branch comparison alone (`if owns_merge_in_progress(repo, branch=handle.branch):` dropping `rc == 1 and`):
    ```
    FAILED tests/test_foreign_merge_refusal.py::ForeignMergeRefusalTests::test_case_5_impostor_case_third_party_merge_of_own_branch_not_aborted
    AssertionError: 'fail-merge' != 'merge-retry'
    - fail-merge
    + merge-retry
     : Refusal kind must be merge-retry: [aw-integration-cause=git-merge-conflict][aw-conflict-shape=unknown] merge-back conflict; fatal: You have not concluded your merge (MERGE_HEAD exists).
    Please, commit your changes before you merge.
    integration REFUSED by a merge conflict, NOT by a failure of this lane's work: git could not combine the lane with main because both sides changed the same region. Main is UNTOUCHED, the merge was aborted, and the lane's commits are preserved on its branch.
    SHAPE: UNKNOWN - the conflict's shape could not be decided, so no claim is made about whether keep-both is safe.
    ```
    The branch comparison alone matched `handle.branch`, fell into the abort arm, issued `git merge --abort` destroying the human's hand resolution and deleting `human_only.txt`. Restored conjunction `rc == 1 and owns_merge_in_progress(...)`, GREEN.

    5. Locale re-run:
    `LC_ALL=C.UTF-8 LANGUAGE=de_DE:de python3 -m pytest tests/test_foreign_merge_refusal.py tests/test_runner_shared.py -o addopts=""`
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=3081166358
    rootdir: <repo>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 106 items

    tests/test_foreign_merge_refusal.py .....                                [  4%]
    tests/test_runner_shared.py ............................................ [ 46%]
    .........................................................                [100%]

    ============================= 106 passed in 14.38s =============================
    ```

    6. Bare pytest run:
    `python3 -m pytest`
    ```
    3107 passed, 2 skipped, 3 warnings in 49.80s
    ```
    Baseline re-derived on this tree without the 5 new tests was 3102 passed, 2 skipped; delta is exactly +5 passed, 0 failures.

    7. Targeted regression set:
    `python3 -m pytest tests/test_runner_shared.py tests/test_merge_conflict_sendback.py tests/test_concurrent_driver_guard.py tests/test_agy_runipd_cli.py -o addopts=""`
    ```
    tests/test_agy_runipd_cli.py ........................................... [ 21%]
    ...............                                                          [ 28%]
    tests/test_runner_shared.py ............................................ [ 50%]
    .........................................................                [ 79%]
    tests/test_concurrent_driver_guard.py ...............................    [ 94%]
    tests/test_merge_conflict_sendback.py ...........                        [100%]

    ============================= 201 passed in 45.74s =============================
    ```

    8. `aw check`:
    Verified; no findings on plan `g2z2pp`.

    9. `aw ipd lint --phase pre-transition`:
    Conforming; exit 0, 0 findings.

    10. `aw sanitize --agent`:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`

    11. `git diff --cached --name-only`:
    Staged set confirmed to contain exactly:
    - `agent_workflows/runner_shared.py`
    - `tests/test_foreign_merge_refusal.py`
    - `.aw/records/plans/pending/20260928-foreignmerge-01-g2z2pp-refuse-a-foreign-merge-instead-of-aborting-it-during-lane-in.ipd.md`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan has now been REVIEWED (2026-09-28 `/plan-review`) and carries `- Readiness: go-pending-approval`, written BY that review as its attested output. It is NOT approved: explicit human sign-off (`- Status: approved`) is still required before execution. The authoring turn deliberately left the field ABSENT, which was correct - writing one before a review would have forged the attestation an auto-approve predicate reads - and it is the review, not the author, that has now filled it in.

WHAT THE HUMAN IS APPROVING, in one paragraph. The defect is real, reproduces at this HEAD with the incident's exact reflog signature (F-01), and is a DESTRUCTIVE action on state the runner does not own - the very thing this repository's contract forbids agents from doing by hand. The substantive judgements being approved are three. FIRST, this plan implements a STRONGER fix than the backlog item asked for: the item's pre/post ordering is kept as a cheap early refusal but is provably insufficient on its own in a shared checkout (F-05), so ownership is proven from `MERGE_HEAD`'s VALUE instead. SECOND, the refusal reuses the EXISTING deferrable kind rather than adding a fourth, which is argued from what a new kind costs across the durable alias map and both hosts' vocabularies against what it would buy that the reason string does not already deliver (OQ-01). THIRD, the recovery is deliberately left IMPERFECT: the poll rung cannot see a mid-merge checkout, so a deferred re-attempt refuses again and spends a budget slot (F-10, OQ-03). That is a smaller harm than today's destructive terminal refusal, and it is carried rather than hidden. Two of the item's own claims are corrected by measurement in the findings: its driver-versus-driver argument is stale now that publishes are serialized repository-wide (F-07), and its agy-host step needs no separate fix (F-08).

On execution, the executor MUST: commit only the two paths named in `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; verify the staged set with `git diff --cached --name-only` before committing, which matters unusually much here because `runner_shared.py` is this repository's highest-contention file and this IS a shared checkout; run the BARE `python3 -m pytest` suite and paste its ACTUAL output rather than claiming success; and complete every `V-*` item with the concrete pasted evidence it demands, including the three deliberate-failure demonstrations in V-04 and V-05 that prove the new guards were genuinely red before the fix. An out-of-scope edit is to be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason`, not treated as a reason to stop.

WHAT REVIEW CHANGED, AND IT CHANGES WHAT YOU ARE APPROVING (2026-09-28 `/plan-review`, findings PR-201..PR-205, all FIXED in place). The plan's diagnosis and every premise measurement reproduced at HEAD `821245a6`, including the incident's `reset: moving to HEAD` reflog signature and the three blind pre-merge guards. ONE SUBSTANTIVE DEFECT WAS FOUND IN THE PROPOSED FIX: `owns_merge_in_progress(branch=handle.branch)` proves WHICH commit was merged and never WHO merged it, so it answers True for a THIRD PARTY's merge of this lane's own branch. Measured: a human's hand-resolved merge of `lane/probe`, with an extra staged file existing on no branch, satisfied the predicate and was then destroyed by the abort - the plan's own harm class, through a narrower window rather than a closed one. E-04 therefore now requires a CONJUNCTION with a locale-safe signal the call already has: the driver's own merge returns rc=1 when it starts and conflicts and rc=128 when git refuses to start it because `MERGE_HEAD` exists (both measured), so ownership is proven without matching git's English. A fifth test case pins the impostor shape and must be shown RED against a branch-comparison-only implementation. Two smaller corrections: the predicate's NAME and docstring must state the limit so the next reader does not treat it as sufficient, and F-11's `2935 passed` baseline is already stale (`2937` at review HEAD), so the executor must re-derive a same-commit baseline rather than compare against either figure.

THREE WAYS THIS PLAN CAN FAIL SILENTLY, stated for the executor. FIRST, the deliberate-failure demonstrations require temporarily REVERTING the fix in `runner_shared.py`; if that mutation is not fully restored it will either be committed (shipping the defect while the plan records it fixed) or left in the tree for another lane. `git status --short` and the staged-set check are what catch it. SECOND, it is tempting to "simplify" E-01 to `git rev-parse MERGE_HEAD`, which passes every test except the octopus one and is measurably wrong (F-06); that is why V-05 demands the octopus assertion be shown red under exactly that spelling. THIRD, E-04's foreign `elif` arm looks unreachable to anyone who has read E-03 and will invite deletion; it is the only thing covering the peer-staged-in-between window, and deleting it restores the defect through a narrower hole with every test still green, because no test can deterministically hit that race. The comment E-04 requires is the mitigation, and a reviewer should check it is present and says why. FOURTH, ADDED AT REVIEW: the started-it half of E-04's conjunction looks redundant beside the branch comparison and is the likelier of the two to be "simplified" away, because it reads like a belt-and-braces check on a predicate that already returned True. It is not redundant - it is the ONLY thing that distinguishes our merge of our branch from a peer's merge of our branch (F-15) - and E-05 case 5 is the test that catches its removal, which is why V-05 requires that case shown RED against the branch-comparison-only implementation.

This plan inherits `- Blocks-Release: next` from backlog item `csmtjp` because its `- Work-Kind:` is `bug`, and the repository policy is that every live bug gates the next release. That gate travels with this plan and must not be cleared as part of executing it. Item `csmtjp` may close once this plan is executed: the item's surviving substance is the wrong ownership assumption, which E-02 and E-04 fix, and its other two points are answered in the findings (F-07 stale, F-08 needs no separate fix).

Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming and every validation item above is verified with pasted evidence.
