# IPD: Teach the executed-transition gate to recognize a legitimate lane merge

- Date: 2026-09-06
- Kind: child
- Concern: The `ipd-executed-transition-gate` pre-commit hook refuses EVERY integration of a lane on which `aw ipd finalize` genuinely ran, because its only proof of finalize is a journal under `.aw/state/runtime/transactions/ipd_finalize_<id6>.json` and `.aw/state/` is GITIGNORED box-local state. The journal therefore never travels with a lane branch, and the lane worktree that held it is torn down after integration, so the predicate is unsatisfiable by construction for a merge. The hook cannot distinguish the abuse it exists to catch (hand-editing a plan's `- Status:` or `git mv`-ing it into `executed/`) from the legitimate act of merging a finalized lane, and refuses both.
  REPRODUCED 2026-09-06, not inferred: in a throwaway clone, a lane branch was given a plan in `executed/` committed as `lifecycle(zzz999): finalize zzz999 -> executed`, then merged with `--no-ff --no-commit`. With `.git/MERGE_HEAD` present the hook exited 1 and printed "raw plan->executed transition (moved into executed/) with NO matching finalize evidence in .aw/state/". So the hook is blind to merge context.
  THE COST IS ALREADY PAID AND RECORDED. Recovering five lanes stranded by run `run-20260905T050043Z-639569` required `--no-verify` on four of five merges (`eyh1fu`, `txc9l1`, `uyeko5`, `eulhzt`), each with maintainer authorization, each documenting the bypass. Finalize had provably run on every one: commits `c9db21a3`, `43c87af5`, `251b7399`, `dd996d73`, each titled `lifecycle(<id6>): finalize <id6> -> executed`. A gate that must be bypassed as ROUTINE PRACTICE teaches operators and agents that `--no-verify` is normal, which is exactly how a real hand-edit would later pass unremarked. The hook's docstring is honest that it is local best-effort prevention; "skippable" was meant as a limitation, not as the expected workflow.
  THIS CHILD IS ORDER 01, BUT NOT FOR THE REASON FIRST WRITTEN, and the correction matters because the original reason was measurably false. The claim was that children 03 and 04 make integration happen more often so "every one of those integrations would trip this hook". MEASURED FALSE at review 2026-09-07: git runs `pre-merge-commit` (NOT `pre-commit`) for an automated merge, this repository installs only `pre-commit`, and a `--ff-only` merge creates no commit at all, so the runner's own `integrate_lane_branch` path does NOT trip this hook and never did. The four recorded bypasses were all HAND merges (`git merge --no-commit` then `git commit`), which IS a `pre-commit` path. So the honest ordering rationale is narrower: this child is Order 01 because it is the only child that touches NO runner module, so it can land and be verified while siblings 02 through 04 contend over the two driver files, and because it removes the bypass habit from the recovery path a human still uses. See the note above Task group 1, and OQ-03 for the `pre-merge-commit` gap this exposes.
- Scope: Add a MERGE-AWARE evidence path to the hook: during a merge, accept IN-TREE evidence (a `lifecycle(<id6>): finalize` commit reachable from the incoming side) as proof that finalize performed the transition, while keeping the hand-edit case refused exactly as today. Fix nothing else about the hook's behavior.
- Scope-Paths: agent_workflows/hooks/executed_transition_gate.py, .pre-commit-config.yaml, CONTRIBUTING.md, tests/test_executed_transition_gate.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Set: integpath
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 29wvmj
- From-Backlog: rnl3b7

## Workflow history
- 2026-09-07 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-101..PR-106 all FIXED, no unfixed BLOCKER/HIGH; OQ-03 added NON-BLOCKING for the measured pre-merge-commit gap; Readiness go-pending-approval

- 2026-09-07 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): OQ-01 RESOLVED BY MEASUREMENT, correcting this plan's own deferral rationale. Asked what the plan's open question was and, before answering from the plan text, checked whether its stated cost was real: it was not. The deferral claimed the answer needed "archaeology on a five-commit sequence whose lanes are now deleted"; the lane BRANCHES are gone but every relevant COMMIT survives, so the question took minutes. THE ANSWER IS THE JOURNAL'S LIFETIME, not git: `_clear_finalize_journal` DELETES the journal on successful completion (`ipd_lifecycle.py:2649`) and on every rollback path, so it exists only between finalize and its consumption, and `76gsmv` merged 22 minutes BEFORE its three siblings (12:51:00 versus 13:13-13:17) and happened to still have one. Exactly ONE journal survives in the whole repository today. The item's rename explanation is conclusively ruled out: all four merges are identical in diff shape (`R061`, `R063`, `R061`, `R060`, each a rename into `executed/` plus the two INDEX files), and four identical shapes with two different outcomes cannot be explained by the shape. Added F-12 (the journal is EPHEMERAL WITHIN a tree, not merely invisible across trees, which doubles the argument for in-tree evidence) and F-13 (the measured diff shapes). Nothing in the plan's scope changed: E-02 already removes the timing dependence entirely, so this strengthens the premise rather than altering the fix. Lint conforming before and after; both OQs are now resolved.
- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `rnl3b7` on a maintainer ruling to shape the `integdefer` items as one Set with the hook fix FIRST. Every claim in the item was re-verified at HEAD `a4279302` rather than trusted, because the item was filed 2026-09-05 and both runners churned heavily since. The core defect REPRODUCED exactly (see Concern). TWO CORRECTIONS TO THE ITEM, both material enough that a plan built on its text would have chased the wrong fix. FIRST, the item's headline evidence claim is WRONG: it says `76gsmv` passed the hook while the other four failed "because git recorded that plan file as a RENAME rather than an addition, so the hook's staged-change inspection did not classify it as a plan-to-executed transition", and concludes "a gate whose verdict depends on whether git chose rename detection is not gating the property it claims to gate". Measured: ALL FOUR of those commits are `R0xx` renames of identical shape (`443bbed4` R099, `c9db21a3` R099, `43c87af5` R099, `251b7399` R098), and the hook handles `R` EXPLICITLY (`code.startswith("R")` at `:118`, with `-M` passed at `:108`). So there is no rename-vs-add inconsistency to fix; the item's E-item-shaped instruction to "fix the rename-vs-add inconsistency regardless" would have been work against a non-defect. Why `76gsmv` passed is NOT established by this plan and is deliberately left as a non-blocking open question rather than guessed at. SECOND, the four lanes the item cites as live evidence are GONE: all four branches are deleted and all four plans now sit in `.aw/records/plans/executed/`, recovered by hand last session, so that evidence is HISTORICAL and this plan reproduces the defect synthetically instead of pointing at it. Also confirmed still true: the hook has zero references to `MERGE_HEAD` or merges, and `.aw/state/` remains gitignored.

## Goal

Stop refusing legitimate lane integrations, without weakening the hand-edit refusal the hook exists for. After this child, merging a finalized lane needs no `--no-verify`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: recognize a merge, and accept in-tree evidence

READ THIS BEFORE E-01, because it changes what "during a merge" means and was MEASURED at review 2026-09-07. GIT DOES NOT RUN `pre-commit` FOR AN AUTOMATED MERGE. It runs `pre-merge-commit`, and this repository installs ONLY `pre-commit` (`ls .git/hooks/` shows `pre-commit` alone; `.pre-commit-config.yaml` declares no `default_install_hook_types`). Measured in a throwaway repo with both hooks installed: `git merge --no-ff -m ... lane` fired `pre-merge-commit` ONLY, and `MERGE_HEAD` was ABSENT when it ran; `git merge --ff-only` created NO commit at all and fired NOTHING; only the HAND sequence (`git merge --no-ff --no-commit` then a separate `git commit`) fired `pre-commit` WITH `MERGE_HEAD` present. Three consequences the plan must own rather than discover at execution: (1) the runner's own integration path (`integrate_lane_branch` does `merge --ff-only`, falling back to `merge --no-ff --no-edit -m ...`) NEVER trips this hook today, so children 03 and 04 will not multiply the bypass through THIS hook and E-01's stated urgency is weaker than the Concern claims; (2) the case this plan actually fixes is the HAND recovery sequence, which is exactly where all four measured `--no-verify` bypasses happened, so the plan is still worth doing and its evidence is real; (3) the fix is INCOMPLETE against a future `pre-merge-commit` installation unless the predicate ALSO works when `MERGE_HEAD` is absent but a merge is being committed. Handle that by treating the detector's negative answer as "not a merge" and refusing, which is fail-closed and is today's behavior, and by recording the `pre-merge-commit` gap as OQ-03 rather than silently widening scope to install a second hook type.

- [ ] E-01 Add a merge-context detector to `agent_workflows/hooks/executed_transition_gate.py`. A commit is a merge in progress when `MERGE_HEAD` exists in the repository's git dir; RESOLVE THE GIT DIR PROPERLY rather than assuming `<root>/.git` is a directory, because in a WORKTREE `.git` is a FILE pointing elsewhere and this repository uses lane worktrees routinely (`git worktree list` shows them). Use `git rev-parse --git-dir` (the hook already shells out through its `_git` helper) so the check works from a worktree, a submodule, and a normal clone alike. VERIFIED AT REVIEW that this hazard is real and the remedy works: in a lane worktree `.git` is a FILE (`ls -la` confirms) and `git rev-parse --git-dir` returns `.../.git/worktrees/<name>`, so a hardcoded `<root>/.git/MERGE_HEAD` would silently never match there.
  RESOLVE `MERGE_HEAD` RELATIVE TO THE RESOLVED GIT DIR, not to the worktree root, since `git rev-parse --git-dir` may return a RELATIVE path (it returns a bare `.git` in a normal clone); join it against the directory the command was run in before testing existence.
  RETURN THE INCOMING COMMIT, NOT JUST A BOOLEAN, because E-02 needs it: read `MERGE_HEAD`'s contents (a commit sha) rather than only testing existence. A detector that returns `bool` would force E-02 to re-read the same file, and the two could then disagree about which side is incoming.
  - Depends on: none
  - Expected outcome: a helper returns the incoming merge commit sha during a merge and `None` otherwise; it resolves the git dir via git rather than a hardcoded `.git/` path, so it is correct inside a lane worktree.
  - Execution state: pending

- [ ] E-02 Add the IN-TREE finalize-evidence predicate: for a plan arriving in `executed/` during a merge, accept the transition when a commit reachable from the INCOMING side (and NOT from `HEAD`) carries a `lifecycle(<id6>): finalize` subject naming THAT plan's id6. In-tree is the whole point: unlike the gitignored journal, a commit survives the branch, which is what makes the evidence portable (the item's own second option, "make the evidence portable", is the same insight arrived at from the other direction).
  BIND THE EVIDENCE TO THE SPECIFIC PLAN, exactly as `_finalize_evidence_ok` already binds the journal to the staged destination path (`:167-171`). A merge that carries a finalize commit for plan A must NOT authorize plan B arriving in `executed/` in the same merge. Match the id6 from the subject line and require it to equal the staged plan's `- Id:`.
  SCOPE THE SEARCH TO THE INCOMING SIDE ONLY, using the range `HEAD..<MERGE_HEAD>`, so a finalize commit that was already on main long ago cannot be replayed as evidence for a different plan arriving now.
  DO NOT REPLACE THE JOURNAL PATH. Keep `_finalize_evidence_ok` as-is and consult it FIRST; the new predicate is an additional accepting path used only when the journal is absent AND a merge is in progress. A non-merge commit therefore behaves byte-identically to today, which is what keeps the hand-edit case refused.
  - Depends on: E-01
  - Expected outcome: during a merge, a plan whose id6 has a `lifecycle(<id6>): finalize` commit on the incoming side passes; the same plan without such a commit still refuses; a finalize commit for a DIFFERENT id6 does not authorize it; outside a merge nothing changes.
  - Execution state: pending

### Task group 2: keep the abuse refused

- [ ] E-03 Prove and preserve the refusals, which is the half of this change that must not regress. FOUR cases must still be refused, and each is a distinct way the fix could be made too permissive:
  (a) a hand-edited `- Status: executed` with NO merge in progress (today's behavior, unchanged);
  (b) a `git mv` into `executed/` with no merge in progress;
  (c) a plan staged into `executed/` DURING a merge with NO finalize commit anywhere on the incoming side. This is the case the item explicitly warns about: "a fix that simply exempts all merges would let someone stage a hand-edit inside a merge commit". A merge must not be a blanket exemption;
  (d) a plan with no readable `- Id:`, which the hook already refuses separately (`:186-191`) and which must keep refusing, since without an id6 the new predicate has nothing to bind to.
  DO NOT WEAKEN THE MESSAGE for the non-merge cases. Operators and agents have learned the current wording; keep it and ADD merge-specific wording only where a merge was detected.
  - Depends on: E-02
  - Expected outcome: all four refusal cases refuse, with (c) refusing specifically because no matching finalize commit exists on the incoming side rather than because a merge was detected.
  - Execution state: pending

- [ ] E-04 Make the refusal ACTIONABLE in the merge case, because a refusal an operator cannot act on becomes another `--no-verify`. When a merge is detected and the incoming side carries no matching finalize commit, say so explicitly: name the plan, state that the merge carries no `lifecycle(<id6>): finalize` commit for it, and point at the real remedy (finalize on the lane, or `aw ipd finalize` if the plan legitimately has not been finalized).
  DO NOT TELL THE OPERATOR TO COMMIT, STASH, RESET, OR CLEAN ANYTHING. Executed plan `z2isfg` is prior art for a begin-time dirty gate AND for the lesson that a refusal message must not instruct the operator to touch work `AGENTS.md` forbids them to touch; reuse that wording discipline. Do not suggest `--no-verify` either: naming the bypass in the refusal is how it becomes routine.
  - Depends on: E-03
  - Expected outcome: the merge-case refusal names the plan, the missing evidence, and a remedy that does not involve bypassing the hook or mutating a co-worker's tree.
  - Execution state: pending

### Task group 3: prove it end to end

- [ ] E-05 Test through a REAL GIT MERGE, not by mocking the detector, because the defect is precisely that real merge state was never consulted. Build the fixture the way this plan's reproduction did: a throwaway repository, a lane branch carrying a plan in `executed/` committed with a `lifecycle(<id6>): finalize <id6> -> executed` subject, then `git merge --no-ff --no-commit`, then invoke the hook's `check()`/`main()` with `MERGE_HEAD` genuinely present.
  COVER BOTH DIRECTIONS AND THE BINDING. Assert: the merge with matching finalize evidence now PASSES (exit 0); the same merge WITHOUT that commit still REFUSES (exit 1); a merge whose finalize commit names a DIFFERENT id6 still refuses for the plan in question; and each of E-03's four non-merge refusals still refuses.
  ASSERT THE WORKTREE CASE, since E-01 exists because of it: run the hook from a `git worktree` where `.git` is a FILE, and show the git-dir resolution finds `MERGE_HEAD`. A test that only ever runs in a normal clone would pass even if E-01 hardcoded `<root>/.git`, leaving the bug live in exactly the lane worktrees this Set is about.
  Run the suite BARE (`python3 -m pytest`) and state before/after counts.
  - Depends on: E-04
  - Expected outcome: a test that FAILS on today's hook and passes after; both merge directions, the id6 binding, the four non-merge refusals, and the worktree case all pinned; bare suite green with counts stated.
  - Execution state: pending

- [ ] E-06 INSTALL THE GATE ON THE `pre-merge-commit` STAGE TOO, closing the automated-merge hole F-14 measured (OQ-03, resolved 2026-09-08 to option (b)). Add `default_install_hook_types: [pre-commit, pre-merge-commit]` to `.pre-commit-config.yaml` and register `ipd-executed-transition-gate` for BOTH stages, so an automated merge carrying a plan into `executed/` is gated exactly as a hand commit is. Today the repo installs ONLY `pre-commit`, so every automated merge bypasses this gate entirely.
  DOCUMENT THE STALE-CLONE CONSEQUENCE IN `CONTRIBUTING.md`, because it cannot be fixed by config alone: `pre-commit install` writes one hook script per installed type, so an EXISTING clone has only `.git/hooks/pre-commit` and will not run the new stage until its owner re-runs `pre-commit install`. Adding the key changes what a FRESH install does and cannot retrofit an existing one. State the required command explicitly where hook setup is already documented.
  DO NOT WEAKEN THE FAIL-CLOSED RULE while widening the stage. Absent `MERGE_HEAD` still means not-a-merge, hence refuse. This item may only ever make the gate fire in MORE places, never fewer, and must not add a path where an unclassifiable merge is waved through.
  - Depends on: E-05
  - Expected outcome: `.pre-commit-config.yaml` declares both hook types and registers the gate for both stages; `CONTRIBUTING.md` states the re-install requirement for existing clones; the fail-closed behavior is unchanged.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE HOOK ALREADY HANDLES RENAMES, contrary to the backlog item. `_staged_plan_executed_transitions` passes `-M` (`:108`) and branches on `code.startswith("R")` (`:118`), extracting both old and new paths. So the item's "fix the rename-vs-add inconsistency" instruction targets a non-defect and is deliberately NOT in this plan.
- THE JOURNAL PREDICATE IS ALREADY PLAN-BOUND, and that discipline is the model for E-02: `_finalize_evidence_ok` checks the journal's phase, its `plan_id`, AND that its `dest_path` matches the staged path (`:152-172`), so evidence for one plan cannot authorize another. The in-tree predicate must bind equally tightly.
- `.aw/state/` IS GITIGNORED BY DESIGN, which is why the fix is in-tree evidence rather than committing the journal. The item offered committing it as an alternative; that would trade a local-state-leak decision for a hook fix, so this plan takes the narrower path and leaves the journal untouched.
- THE HOOK IS HONEST ABOUT BEING LOCAL AND SKIPPABLE, with `aw check`/`aw doctor` as the deterministic backstop. This plan does not change that posture; it removes the reason to reach for the bypass.
- `.git` IS A FILE, NOT A DIRECTORY, INSIDE A WORKTREE, and this repository uses lane worktrees as the normal execution mode (`.aw/worktrees/<id6>`), so any merge-state check must resolve the git dir through git.
- Run the suite BARE: `python3 -m pytest`. The configured `addopts` already supply quiet, parallel, and the fast subset; do not add `-n0` (measurably several times slower here) or a second `-q` (compounds to `-qq` and suppresses the `N passed` line this plan requires pasted).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | **THE DEFECT, REPRODUCED SYNTHETICALLY.** A throwaway clone, a lane branch carrying a plan in `executed/` committed as `lifecycle(zzz999): finalize zzz999 -> executed`, merged with `--no-ff --no-commit`: with `.git/MERGE_HEAD` present the hook exited 1 and refused with "NO matching finalize evidence in .aw/state/". | live reproduction 2026-09-06 at HEAD `a4279302` |
| F-2 | The hook has ZERO merge awareness: `grep -n "MERGE_HEAD\|merge"` over `executed_transition_gate.py` returns nothing. | measured 2026-09-06, re-verified 2026-09-07 (223-line module, no match) |
| F-14 | **WHICH HOOK GIT ACTUALLY RUNS, measured at review and load-bearing for E-01's premise.** For an AUTOMATED merge git runs `pre-merge-commit`, NOT `pre-commit`, and `MERGE_HEAD` is ABSENT when it runs. A `--ff-only` merge creates no commit and runs no hook at all. ONLY the hand sequence (`git merge --no-ff --no-commit` then a separate `git commit`) runs `pre-commit` with `MERGE_HEAD` present. This repository installs ONLY `pre-commit`. So the runner's integration path never trips this gate, and the case this plan fixes is the HAND recovery path, which is precisely where all four measured bypasses occurred. | throwaway repo with both hook types installed, 2026-09-07: automated `merge --no-ff -m` fired `pre-merge-commit` only (`MERGE_HEAD present: no`); `merge --ff-only` fired nothing; `--no-commit` + `git commit` fired `pre-commit` (`HOOK SEES MERGE_HEAD`); `ls .git/hooks/` shows `pre-commit` alone; `oc_runipd.py:2039`, `:2044-2052` |
| F-15 | The DEFECT AND THE FIX'S MECHANISM ARE BOTH INDEPENDENTLY REPRODUCED at review, not merely inherited from the plan. In a throwaway repo a lane carrying `lifecycle(zzz999): finalize zzz999 -> executed`, merged `--no-ff --no-commit`, made the hook exit 1 with "NO matching finalize evidence in .aw/state/". `git log HEAD..$MERGE_HEAD` correctly lists ONLY the incoming finalize commit, so E-02's `HEAD..MERGE_HEAD` scoping is implementable exactly as specified. AND case (c) refuses today: a plan `git mv`-ed into `executed/` inside a merge whose incoming side carries NO finalize commit exits 1. | live reproduction 2026-09-07 at HEAD `01b0b150` |
| F-3 | The evidence predicate is unsatisfiable across trees BY CONSTRUCTION: it reads a journal under `.aw/state/runtime/transactions/`, and `.aw/state/` is gitignored, so the journal cannot travel with a lane branch. | `executed_transition_gate.py:152-172`; `.gitignore` |
| F-4 | **THE ITEM'S RENAME EXPLANATION IS FALSE, and this correction is why the plan omits a whole instruction the item gave.** All four recovery commits are `R0xx` renames of identical shape (`443bbed4` R099, `c9db21a3` R099, `43c87af5` R099, `251b7399` R098), and the hook branches on `R` explicitly with `-M` enabled. There is no rename-vs-add inconsistency to fix. | `git log --diff-filter=R --name-status` per id6; `executed_transition_gate.py:108`, `:118` |
| F-5 | **THE ITEM'S LIVE EVIDENCE IS NOW HISTORICAL.** All four cited lane branches (`aw/lane/76gsmv`, `eyh1fu`, `txc9l1`, `uyeko5`) are DELETED and all four plans are in `.aw/records/plans/executed/`, recovered by hand last session. So the defect must be reproduced synthetically, which E-05 does. NOTE the branches are gone but every relevant COMMIT survives, which is what made OQ-01 answerable after all; this plan's first draft wrongly called that archaeology. | `git rev-parse --verify` fails for all four; `ls .aw/records/plans/executed/`; all five finalize commits resolve by sha |
| F-12 | **THE JOURNAL IS EPHEMERAL WITHIN A TREE, not merely invisible across trees**, which doubles the argument for in-tree evidence. `_clear_finalize_journal` DELETES it on successful completion (`ipd_lifecycle.py:2649`) and on every rollback path (`:2430`, `:2445`, `:2500`), so it exists only between finalize and its consumption. TODAY exactly ONE journal survives in the whole repository (`ipd_finalize_v58bvy.json`). This is the mechanism behind OQ-01: `76gsmv` merged 22 minutes before its siblings and happened to still have one. | `ipd_lifecycle.py:284`, `:2649`; `ls .aw/state/runtime/transactions/`; merge timestamps 12:51:00 versus 13:13-13:17 |
| F-13 | **THE FOUR MERGES ARE IDENTICAL IN DIFF SHAPE**, which conclusively rules out the backlog item's rename explanation: `git diff --name-status -M <merge>^1 <merge>` gives `R061`, `R063`, `R061`, `R060` respectively, each a rename into `executed/` plus the two INDEX files. Four identical shapes with two different outcomes cannot be explained by the shape. | measured per merge commit `7e157380`, `0d80fef4`, `6608c877`, `eaf19dd0` |
| F-6 | The bypass cost is documented in git history, so this is a measured habit rather than a hypothetical: four of five recovery merges used `--no-verify`, each with a real finalize commit on the lane (`c9db21a3`, `43c87af5`, `251b7399`, `dd996d73`). | backlog `rnl3b7`; those four commit subjects |
| F-7 | The journal predicate binds evidence to ONE plan via `plan_id` and `dest_path`, which is the discipline E-02 must match so a merge carrying finalize for plan A cannot authorize plan B. | `executed_transition_gate.py:167-171` |
| F-8 | A plan with no readable `- Id:` is already refused on its own branch (`:186-191`), which must keep refusing because the new in-tree predicate has no id6 to bind to. | `executed_transition_gate.py:186-191` |

## Proposed changes (ordered, validatable)

1. Add a merge detector that resolves the git dir through git and returns the incoming commit (E-01).
2. Add a plan-bound, incoming-side-only in-tree finalize-evidence predicate, consulted only when the journal is absent during a merge (E-02).
3. Prove the four refusal cases still refuse, including a hand-edit staged inside a merge (E-03).
4. Make the merge-case refusal actionable without naming the bypass or telling the operator to mutate a tree (E-04).
5. Test through a real git merge, both directions, the id6 binding, and from a worktree where `.git` is a file (E-05).

## Deferred / out of scope (with reason)

- COMMITTING THE FINALIZE JOURNAL (or a redacted attestation) to make the evidence portable. The item offers this as an alternative; it is rejected here as the wider change, because it turns a hook fix into a decision about why `.aw/state/` is gitignored and what may leave the box. In-tree commit evidence achieves the same portability with no new tracked state.
- THE "RENAME-VS-ADD INCONSISTENCY" the item instructs be fixed regardless. Measured non-existent (F-4). Fixing a non-defect would be change without cause.
- ESTABLISHING WHY `76gsmv` PASSED the hook when the other three did not. The item's explanation is disproved (F-4) and this plan does not substitute a guess; recorded as OQ-01, non-blocking, because the fix does not depend on the answer.
- WEAKENING OR REMOVING THE GATE. Explicitly counter to the goal: the point is to stop refusing legitimate merges, not to stop refusing hand-edits.
- THE OTHER THREE `integdefer` CONCERNS. Children 02, 03 and 04 of this Set own the shared extraction, the deferral ladder, and the `integrate` verb; this child deliberately stays inside one hook file so it can land and be verified first.

## Scope check

- Over-scope: none. One hook module plus its test file.
- Scope-Paths justification: `agent_workflows/hooks/executed_transition_gate.py` holds the detector, both predicates, and the refusal messages (E-01..E-04); `tests/test_executed_transition_gate.py` holds every new assertion (E-05). No runner module is touched, which is what lets this child land while the two high-contention driver files are being changed by the rest of the Set.
- Under-scope, stated rather than left as `none`: this child does not make the evidence portable by committing the journal, does not touch the `aw check`/`aw doctor` backstop, and does not address the three sibling concerns. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, with the `N passed` summary line pasted and counts stated. MEASURE YOUR OWN BEFORE-BASELINE and judge on the DELTA: the suite is NOT green at HEAD. Measured at review 2026-09-07 (HEAD `01b0b150`): `1 failed, 5613 passed, 3 skipped, 2 xfailed`, the failure being the pre-existing `tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows`, confirmed present with this plan's changes stashed. Do NOT report it as yours. The authoring-time note of `5536 passed` at HEAD `3d239cfa` is stale and superseded by this measurement.
  NOTE A CORPUS TRAP THIS REVIEW HIT, because the executor will edit plan history lines too: `tests/test_plan_readiness.py::ApprovalGateRealCorpusTests` reads the REAL `pending/` tree, and `plan_readiness.newest_verdict` classifies a review history record with NO verdict token by scanning for a negative READINESS token. A history line that says `Readiness no-go` without an explicit verdict token (`APPROVE`, `REVIEWED - OPEN QUESTIONS`, `REJECT - NEEDS REPLAN`) therefore reads as NEGATIVE and fails that test. State the verdict token explicitly in any history line you write.
- Targeted: `tests/test_executed_transition_gate.py`, plus any test module that exercises `aw ipd finalize` end to end.
- A REAL-MERGE demonstration in a throwaway repository, pasted before and after: the same merge refusing today and passing after the fix. A mocked `MERGE_HEAD` is NOT sufficient evidence, because the defect is that real merge state was never read.
- A WORKTREE demonstration: the hook invoked from a `git worktree` (where `.git` is a file), showing merge state is still found.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`). A pipe through `head` reports the pipe's status, which has already produced one false finding in this repository.
- `aw sanitize --agent` clean.

## Spec / documentation sync

The hook's MODULE DOCSTRING states the evidence rule ("a transaction JOURNAL under `.aw/state/runtime/transactions/ipd_finalize_<id6>.json`", `:18`) and must be updated to describe the second, in-tree accepting path and when it applies, since that docstring is the only prose statement of what the gate accepts.

If `CONTRIBUTING.md` or `AGENTS.md` documents this hook or tells a reader that a lane merge requires `--no-verify`, correct it in the same change and say so in the commit; a doc that still prescribes the bypass would keep the habit alive after the reason is gone. MEASURED AT REVIEW 2026-09-07: neither file mentions `executed_transition_gate` or `executed-transition` at all, and `AGENTS.md`'s single `--no-verify` mention (`:175`) is the honest general statement that local hooks are skippable, which is CORRECT and must NOT be edited. So expect this to be a no-op; re-grep at execution time and, if it is still a no-op, SAY SO rather than inventing a doc change. Write no em or en dashes in user-facing prose.

No SPEC change is authorized here: the gate is local tooling, not a specified contract surface.

## Open questions

### OQ-01: Why did `76gsmv` pass the hook when the other three merges did not?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED 2026-09-07 by measurement, correcting this plan's OWN earlier claim that the answer would require archaeology on deleted lanes. It does not: the lane BRANCHES are gone but every relevant COMMIT survives, so the question was answerable in minutes and the deferral was wrong to assert otherwise.
  THE ANSWER IS THE JOURNAL'S LIFETIME, not anything about git. `76gsmv` was merged at 12:51:00 on 2026-09-05, TWENTY-TWO MINUTES before the other three (13:13:11, 13:14:28, 13:17:57), and it was the FIRST of the four. The finalize journal is per-plan (`ipd_finalize_<id6>.json`, `ipd_lifecycle.py:284`) so the four do not overwrite each other, but `_clear_finalize_journal` DELETES it on successful completion (`:2649`, and on rollback at `:2430`, `:2445`, `:2500`). So a journal exists ONLY between finalize and its consumption; whether the hook sees one is a question of TIMING, not of the merge's shape.
  THE DIFF SHAPES ARE IDENTICAL, which rules out the item's explanation conclusively. Measured on each merge commit with `git diff --name-status -M <merge>^1 <merge>`: `76gsmv` `R061`, `eyh1fu` `R063`, `txc9l1` `R061`, `uyeko5` `R060`, every one a rename into `executed/` plus the two INDEX files. Four identical shapes with two different outcomes cannot be explained by the shape.
  IT REMAINS NON-BLOCKING AND CHANGES NOTHING IN THIS PLAN, which is why it stays a note rather than becoming an E-item: E-02 makes every legitimate merge pass on positive IN-TREE evidence that survives the branch, so the fix removes the timing dependence entirely rather than accommodating it. The finding does STRENGTHEN the plan's premise, though: it confirms the journal is not merely invisible across trees (F-3) but also EPHEMERAL WITHIN one, so a gate resting on it is doubly unreliable. E-05's fixture must still be observed FAILING before the fix (per its own instruction), and if it passes, the executor should suspect a journal left over from an earlier test rather than the mystery this question once named.

### OQ-02: Should the in-tree predicate accept any commit subject naming the plan, or only the exact `lifecycle(<id6>): finalize` form?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ONLY THE EXACT FORM. That subject is written by `aw ipd finalize` itself, so requiring it keeps the evidence tied to the tool that ran the gates rather than to prose anyone can type; a looser match (any commit mentioning the id6) would let an ordinary work commit that happens to name the plan authorize the transition, which is the hand-edit case wearing a different hat. The narrow form is also what the four recorded recovery commits actually carry (`c9db21a3`, `43c87af5`, `251b7399`, `dd996d73`), so it is evidenced rather than invented. If a future finalize changes its subject format, this predicate must change with it, which is a coupling worth having because the alternative is a gate that accepts strings no tool emits.

### OQ-03: Should this child also install the gate as a `pre-merge-commit` hook, closing the automated-merge hole F-14 exposes?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-08 BY MAINTAINER RULING: OPTION (b), WIDEN THIS CHILD TO INSTALL THE SECOND HOOK TYPE. Close the automated-merge hole here rather than deferring it: add `default_install_hook_types: [pre-commit, pre-merge-commit]` to `.pre-commit-config.yaml` and register the `ipd-executed-transition-gate` hook for BOTH stages, so an automated merge that carries a plan into `executed/` is gated exactly as a hand commit is.
  SCOPE IS WIDENED DELIBERATELY, AND THE FENCE MUST BE UPDATED TO MATCH. `- Scope-Paths:` now carries `.pre-commit-config.yaml` in addition to the hook module and its test. That was the stated reason for NOT doing this (the file sits outside the original two-file fence), and the maintainer has overridden it, so the fence follows the decision rather than the reverse. Do not treat the added path as out-of-scope drift at finalize time.
  THE CONTRIBUTOR-SETUP CONSEQUENCE IS REAL AND MUST BE STATED, NOT DISCOVERED. `pre-commit install` writes ONE hook script per installed type, so an existing clone has only `.git/hooks/pre-commit` and will NOT run the new stage until its owner re-runs `pre-commit install` (or `pre-commit install --install-hooks`). Adding `default_install_hook_types` changes what a FRESH install does; it cannot retrofit an existing clone. So this item MUST also: (1) say so in `CONTRIBUTING.md` where the hook setup is documented, and (2) make the run-time behavior fail-closed-and-visible rather than silently absent, since a stale clone is now the difference between a gated and an ungated automated merge.
  VERIFY THE STAGE ACTUALLY FIRES, DO NOT ASSUME IT. `pre-merge-commit` runs only for an automated merge that creates a commit WITHOUT opening an editor; git skips it when the merge is fast-forward (no commit at all) and runs `prepare-commit-msg`/`commit-msg` on the conflicted-then-resolved path instead. The V-item for this work must paste a real automated merge that carries a plan into `executed/` being REFUSED, and a legitimate evidenced one being ACCEPTED, on the `pre-merge-commit` stage specifically. A test that only asserts the YAML contains the string is NOT evidence the gate runs.
  FAIL-CLOSED BEHAVIOR IS UNCHANGED AND MUST STAY THAT WAY: absent `MERGE_HEAD` means not-a-merge, hence refuse. Widening the stage TIGHTENS the gate; it must not introduce a path where a merge is waved through because the hook could not classify it.
  ORIGINAL ESCALATION RATIONALE, retained for the record: raised at review from a MEASUREMENT (F-14), and left OPEN because it was a scope decision, not a fact. THE HOLE IS REAL AND PRE-EXISTING: git runs `pre-merge-commit` for an automated merge and this repository installs only `pre-commit`, so ANY automated merge that carries a plan into `executed/` bypasses this gate entirely today, with or without this plan. That is a wider hole than the one this child fixes, and it was NOT introduced by this child.
  WHY IT IS NOT SIMPLY PULLED IN: adding a second hook type means `default_install_hook_types` in `.pre-commit-config.yaml` plus a re-`pre-commit install` on every existing clone, which changes contributor setup for everyone and is exactly the kind of environment change a hook fix should not smuggle in. It also touches a path outside this plan's two-file `Scope-Paths`.
  WHY IT IS NON-BLOCKING: this child is a strict improvement without it. It converts the hand recovery path from "always refuses, so always bypassed" to "accepts real evidence, still refuses hand-edits", and the automated path is no worse than today. NOTHING IN THIS PLAN DEPENDS ON THE ANSWER, and the fix must fail CLOSED when it cannot tell (absent `MERGE_HEAD` means not-a-merge, hence refuse), so a later `pre-merge-commit` installation would tighten the gate rather than break it.
  THE DECISION NEEDED: (a) file the `pre-merge-commit` gap as its own backlog item and leave this child as-is (recommended, since it keeps this child's two-file scope and lets the environment change be reviewed on its own merits); (b) widen this child to install the second hook type; or (c) accept the automated-merge hole permanently and record why. If (a), the executor should file the item and cite it here rather than leaving the measurement only in this plan's findings.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the detector and show it returning the incoming commit sha during a real merge and `None` outside one. Paste the git-dir resolution line and confirm in one sentence that it does not hardcode `<root>/.git`. Paste output from inside a `git worktree` (where `.git` is a FILE, show that with `ls -la`) proving `MERGE_HEAD` is still found.
    ALSO paste the F-14 hook-type evidence, since E-01's premise depends on it: show WHICH git hook fires for (a) `git merge --ff-only`, (b) an automated `git merge --no-ff -m ...`, and (c) `git merge --no-ff --no-commit` followed by a separate `git commit`, and whether `MERGE_HEAD` is present in each. State plainly that this repository installs only `pre-commit`, so case (b) does not reach this gate, and confirm the detector FAILS CLOSED (absent `MERGE_HEAD` means not-a-merge, hence refuse) rather than treating an unknown state as a merge.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the predicate. Show FOUR probes during a real merge: matching finalize commit for the staged plan (accept); no finalize commit (refuse); a finalize commit naming a DIFFERENT id6 (refuse for the staged plan); and a finalize commit that exists on `HEAD` but not the incoming side (refuse, proving the `HEAD..MERGE_HEAD` scoping). Confirm the journal path is still consulted first and unmodified.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the exit code (UNPIPED) and message for each of the four refusal cases: hand-edited status outside a merge; `git mv` outside a merge; a plan staged into `executed/` DURING a merge with no finalize commit on the incoming side; and a plan with no readable `- Id:`. Case (c) is the one that matters most: confirm the message attributes the refusal to missing evidence, NOT to the presence of a merge, and state in one sentence why a blanket merge exemption would have been wrong.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the merge-case refusal text verbatim. Confirm it names the plan, names the missing `lifecycle(<id6>): finalize` evidence, and offers a remedy. Confirm by inspection that it does NOT mention `--no-verify` and does NOT instruct the operator to commit, stash, reset, or clean anything, citing the `z2isfg` wording discipline. Paste the non-merge refusal text and confirm it is unchanged from today.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new test and PROOF IT IS FALSIFIABLE: run it against the pre-fix hook (stash or revert E-01/E-02) and paste the FAILURE, then paste the pass after. A test never observed to fail is not evidence it detects the bug. Paste the real-merge before/after demonstration, the worktree case, and the BARE `python3 -m pytest` summary line with before/after counts. Confirm no test mocks `MERGE_HEAD` in place of performing a real merge.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: PROVE THE STAGE ACTUALLY FIRES; a test asserting the YAML contains the string is NOT evidence. Paste a REAL automated merge that carries a plan into `executed/` being REFUSED on the `pre-merge-commit` stage, and a legitimate evidenced one being ACCEPTED, both with the hook installed via `pre-commit install --hook-type pre-merge-commit` (or `default_install_hook_types`) in a throwaway repository. Paste the `.git/hooks/` listing showing BOTH hook scripts present, since that is the artifact `default_install_hook_types` actually produces.
    NAME THE STAGES GIT SKIPS, so a passing test is not mistaken for full coverage: `pre-merge-commit` does NOT run for a fast-forward merge (no commit is created) and does NOT run on the conflicted-then-resolved path (git runs `prepare-commit-msg`/`commit-msg` instead). State which of those this Set's own integration path takes, since `integrate_lane_branch` attempts `--ff-only` FIRST and only falls back to `--no-ff`; if the common case is fast-forward, say plainly that this item does not gate it and why that is acceptable.
    Paste the `CONTRIBUTING.md` diff stating the re-install requirement for existing clones, and confirm the fail-closed rule is untouched: an absent `MERGE_HEAD` still refuses (paste it).
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). OQ-01 and OQ-02 are RESOLVED (OQ-01 was resolved by measurement 2026-09-07, so the earlier "deferred" wording here was stale). OQ-03 is OPEN and NON-BLOCKING: it records the `pre-merge-commit` hole F-14 measured, which is pre-existing and not made worse by this child, and nothing in this plan depends on its answer. No BLOCKING question remains, so this plan is approvable.

Scope fence: touch ONLY the two paths in `Scope-Paths`. Do NOT modify `oc_runipd.py`, `agy_runipd.py`, or `runner_shared.py`; this child is deliberately runner-free so it can land while siblings 02 through 04 change those files. Do NOT commit the finalize journal or change `.gitignore`. Do NOT weaken any existing refusal. Do NOT change `_finalize_evidence_ok`'s journal logic. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since a rejected commit can leave another party's paths staged. THIS IS A SHARED CHECKOUT with concurrent agents: run `aw runs` before starting.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

THE ITEM THAT MATTERS MOST IS V-03 CASE (c). The tempting fix is to exempt merges wholesale, which would pass every test about legitimate integration while opening the exact hole the gate exists to close: a hand-edited plan staged inside a merge commit. The refusal must come from ABSENT EVIDENCE, never from the absence of a merge. If you find yourself writing `if merging: return 0`, stop and reconsider.

YOU WILL BE TESTING A HOOK THAT GOVERNS YOUR OWN COMMITS. Expect to hit it while working, and do NOT reach for `--no-verify` to get your own work in; if it refuses something you believe is legitimate, that is either a finding or a bug in your change, and either way it is the information this plan exists to produce.

On completion, close backlog `rnl3b7`, which this plan carries as `- From-Backlog:`. That item carries NO release gate, so no `Blocks-Release` is inherited here; the three release-blocking siblings carry theirs on children 02 through 04.
