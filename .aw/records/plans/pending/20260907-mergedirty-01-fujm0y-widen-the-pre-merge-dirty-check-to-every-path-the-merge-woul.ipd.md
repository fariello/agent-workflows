# IPD: Widen the pre-merge dirty check to every path the merge would write, after the shared extraction

- Date: 2026-09-07
- Kind: child
- Concern: The pre-merge dirty guard checks the wrong set of paths. `dirty_tree_overlap(repo, changed_files)` is called with `lane.changed_files`, so it compares main's dirty paths only against files THE LANE changed. A non-fast-forward merge can also write files the lane never touched (commits that landed on main since the lane base, and renames of lane-touched files), and those are outside the check. The guard reports "clear" and the merge then fails anyway.
  REPRODUCED 2026-09-07, so this is measured rather than argued: lane changed only `a.txt`; main renamed `a.txt` to `renamed.txt` and was dirty there; `dirty_tree_overlap(repo, ["a.txt"])` returned `[]` (guard says clear) and `git merge --no-ff` then failed with "Your local changes to the following files would be overwritten by merge: renamed.txt". The guard passed and the merge died.
  TODAY THE COST IS ONLY A WORSE MESSAGE. Both mis-dispositions are terminal, so the operator gets `merge-conflict` plus git's raw stderr instead of the accurate `integration-blocked` ("main tree has un-owned dirty paths overlapping the incoming change: <paths>"). Verified that git fails closed on its own in every dangerous case and the driver's only recovery is `git merge --abort`, with no `reset`, `checkout -f`, `stash`, or `clean` anywhere. It is NOT a data-safety bug and must not be described as one.
  BUT THE LADDER BREAKS THAT SYMMETRY, WHICH IS WHY THIS MATTERS NOW. Sibling `51vw4y` makes the dirty-overlap refusal (`integration-blocked`) NON-TERMINAL via a defer/poll/ask ladder, while a real conflict (`merge-conflict`) stays terminal, correctly. Once that lands, misclassifying transient co-worker dirt as `merge-conflict` converts a recoverable deferral into permanent in-run loss plus a dependency cascade. The diagnostic defect becomes a functional one.
- Scope: Compute the pre-merge dirty check against every path the merge would actually write (the `git merge-tree --write-tree` result diffed against HEAD; NOT the merge-base-to-both-tips union, which review disproved as F-7), not just the lane's changed files, so transient dirt on a path the merge touches is classified `integration-blocked` rather than `merge-conflict`. ONE implementation in shared code. Change no refusal into an acceptance AND refuse nothing that previously integrated: this plan makes refusal MORE ACCURATE, in both directions.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/lane_containment.py, tests/test_runner_shared.py, tests/test_merge_dirty_scope.py
- Item-Dependencies: executed:6sb3yu, executed:51vw4y
- Status: approved
- Readiness: go-pending-approval
- Priority: high
- Work-Kind: bug
- Set: mergedirty
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: fujm0y
- Approval: 2026-09-11, human ("approved"): Approved by the maintainer 2026-09-10 during an /askme round ('We can approve AND resolve'). OQ-02 resolved as already-enforced: the executed:51vw4y edge is re-checked at dispatch with no bypass, so this plan will correctly report dependency-blocked until 51vw4y executes. Priority: high, Work-Kind: bug, Blocks-Release: next. Its prerequisite 51vw4y was approved in the same round.
- From-Backlog: h1ksy6
- Blocks-Release: next

## Workflow history
- 2026-09-11 approved (aw set, --by-human): Approved by the maintainer 2026-09-10 during an /askme round ('We can approve AND resolve'). OQ-02 resolved as already-enforced: the executed:51vw4y edge is re-checked at dispatch with no bypass, so this plan will correctly report dependency-blocked until 51vw4y executes. Priority: high, Work-Kind: bug, Blocks-Release: next. Its prerequisite 51vw4y was approved in the same round.

- 2026-09-10 readiness re-check (opencode its_direct/pt3-claude-opus-5-1m-us): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW. The three `no-go` conditions were RECOMPUTED and each found clear: `has_unresolved_blocking_question` -> False; `subject_gating_blocks` -> empty (PR-002 closed in review round 2); `newest_verdict` polarity -> neutral (not negative). Specifically, OQ-02 is resolved AND corrected to `Blocking: no`: it requested an approval-ordering PREFERENCE while marked blocking, which held a `Priority: high` release blocker at `no-go` for a constraint the runner already enforces at dispatch (`edge_satisfied`, no bypass flag, `dependency-blocked` terminal). The maintainer challenged the question and it did not survive measurement. The `executed:51vw4y` edge STAYS: the sequencing rationale is sound and dropping it remains refused, so this plan will correctly report `dependency-blocked` until `51vw4y` executes. HUMAN APPROVAL IS STILL REQUIRED.
- 2026-09-10 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review REVIEWED - OPEN QUESTIONS; NO-GO; PR-001..PR-006. `aw ipd lint` CONFORMING at `--phase author` before semantic review and at `--phase review-finalize` after. NO-GO is NOT a criticism of the plan: its own E-01 stop condition is met because prerequisite `51vw4y` has not executed (F-8), so the correct state is not-yet-runnable, and the declared `executed:51vw4y` edge already makes the runner mark it `dependency-blocked`. THE DEFECT THIS PLAN FIXES IS REAL AND WAS REPRODUCED INDEPENDENTLY, not taken on trust: built base/lane/main-rename in a throwaway repo, and `dirty_tree_overlap(repo, ['a.txt'])` returned `[]` (guard says clear) while `git merge --no-ff` then failed with "Your local changes to the following files would be overwritten by merge: renamed.txt", exit 2. The call site is confirmed at `runner_shared.py:1003` passing `lane.changed_files`. THE FINDING THAT RESHAPES THE PLAN IS THAT ITS PRESCRIBED ALGORITHM CAUSES THE REGRESSION ITS OWN V-03 FORBIDS (PR-001, F-7). E-02 specified the merge-base-to-both-tips UNION. Measured: base `a.txt`+`b.txt`, lane changes `a.txt`, main advances AND dirties `b.txt`; the union is `['a.txt','b.txt']` so the guard returns `['b.txt']` and REFUSES, yet the real merge exits 0 ("Merge made by the 'ort' strategy", touching only `a.txt`) and the co-worker's dirty `b.txt` survives intact. So the union refuses a previously-integrating case, which V-03 defines as a FAILED validation; the plan would have failed its own acceptance bar at execution. The corrected algorithm is `git merge-tree --write-tree HEAD <lane>` diffed against HEAD, measured to yield `['renamed.txt']` on the rename fixture (correctly blocks, and the real merge does fail) and `[]` on the union-disproof fixture (correctly allows, and the real merge does succeed). E-02 now prescribes it, E-03 and V-02/V-03 carry the disproving fixture as MANDATORY evidence that the corrected algorithm was implemented, and E-02 also handles `merge-tree`'s conflict exit so a conflicting merge cannot pass the guard on a fabricated empty set. TWO PREREQUISITE FACTS WERE VERIFIED RATHER THAN ASSUMED, AND THEY DIVERGE. `6sb3yu` HAS landed: `dirty_tree_overlap` now has exactly ONE definition (`runner_shared.py:888`), so E-01's two-copy stop will not fire (F-2 resolved). `51vw4y` has NOT: it is `reviewed` in `pending/`, and `integration-blocked` is still terminal in both drivers (`oc_runipd.py:6754-6767`, `agy_runipd.py:3813`), the only `integration_deferred` occurrences being an attempt-record field holding a reason string rather than a non-terminal status (F-8). A TRIPWIRE IN E-01 WAS DEFUSED (PR-003, F-9): `grep "def integrate_lane_branch"` returns THREE hits, but the two driver hits are thin wrappers delegating to the shared implementation and binding only `host_label`/`run_checked`, so an executor applying the "more than one means stop" rule to that symbol would have wrongly refused to proceed; the stop rule now explicitly keys on `dirty_tree_overlap` definitions only. ALSO FIXED: the plan omitted `Priority` and `Work-Kind` while inheriting `Blocks-Release: next` from source item `h1ksy6`, which is `Priority: high`/`Work-Kind: bug`, and the gate resolves to the single `planned` release `f33nrj` (2.0.0) (PR-004, F-10); `lane_containment.py` is declared in `Scope-Paths` but this review found no change it needs, which `aw ipd finalize` will refuse without a `--scope-ack`, so a justification is now demanded (PR-005); `dirty_tree_overlap`'s docstring still describes the input as the lane's `changed_files` and becomes FALSE when E-02 lands, so spec-sync now requires updating it in the same change plus recording why a union is wrong (PR-006); and the suite baseline is stated as measured (`1 failed, 5958 passed, 3 skipped, 2 xfailed`) with the failure identified as the environmental `test_reporting_contract` parity case caused by the gitignored local `opencode-recovery/` tree. Verified sound and unchanged: F-4's severity honesty (no `reset`/`checkout -f`/`stash`/`clean` anywhere in `runner_shared.py`, so today's cost really is a worse message and not lost work), F-5 (`2c122z` is indeed in `superseded/`), F-6's rename endpoint handling, OQ-01's refusal to reclassify conflict-resolution paths, the no-dirt-resolution rule, and the fixtures-must-drive-real-git rule, which this review's own reproduction independently confirms is the right call. No product code was modified by this review.
- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `h1ksy6` with its SEQUENCING CORRECTED, which is the whole reason this plan is not a transcription of the item. The item says `dirty_tree_overlap` "is still in `main`, in TWO copies" and cites `oc_runipd.py:1923` plus `agy_runipd.py:1156`. Both facts are about to stop being true: approved plan `6sb3yu` is queued RIGHT NOW to extract both copies into `runner_shared.py` as ONE implementation. Verified at authoring: two copies still exist (`oc_runipd.py:1951`, `agy_runipd.py:1241`), `runner_shared.py` defines none, and every line number the item cites has already drifted. So this plan declares `executed:6sb3yu` and instructs the executor to fix ONE function, not two. It also declares `executed:51vw4y` because `5wdoze` line 113 states these two "must be reconciled, not stacked blindly": widening the input set makes refusal MORE reachable, and doing that while refusal is still TERMINAL would make things worse, not better.

## Goal

A transient dirty path that the merge would actually write is reported as `integration-blocked` (deferrable) rather than `merge-conflict` (terminal), so the ladder can recover it and the operator gets an accurate reason.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the post-extraction ground truth

- [ ] E-01 RE-LOCATE THE FUNCTION AND CONFIRM THERE IS EXACTLY ONE, before changing anything. This plan was authored against a tree with TWO copies and is sequenced to execute against a tree with ONE, after `6sb3yu`. Locate `dirty_tree_overlap` and `integrate_lane_branch` BY SYMBOL and record where each now lives.
  THE EXTRACTION HAS LANDED, verified at review 2026-09-10: `6sb3yu` is `executed`, `dirty_tree_overlap` has EXACTLY ONE definition at `runner_shared.py:888`, and its call site is `runner_shared.integrate_lane_branch` (`:1003`, `overlap = dirty_tree_overlap(repo, lane.changed_files)`). That call site is the single line E-02 changes.
  DO NOT MISREAD `integrate_lane_branch`'s THREE MATCHES AS SURVIVING DUPLICATION. `grep "def integrate_lane_branch"` returns three hits (`runner_shared.py:959`, `oc_runipd.py:1967`, `agy_runipd.py:1311`), but the two driver hits are THIN WRAPPERS that delegate to the shared implementation, binding only `host_label` and `run_checked`; both docstrings cite `6sb3yu` and say so. Read at review. So three hits here is the POST-extraction shape, not evidence the dependency was skipped, and the stop-and-report rule below does NOT fire on it. The rule keys on `dirty_tree_overlap` having more than one DEFINITION.
  IF TWO `dirty_tree_overlap` DEFINITIONS EXIST, STOP AND REPORT rather than fixing both. That would mean `6sb3yu` was reverted, and patching both would recreate the duplication `6sb3yu` removed and `cnwy8g` documents. Report, do not work around.
  THE LADDER HAS *NOT* LANDED, AND THIS IS THE GATING FACT (F-8). Verified at review: `51vw4y` is `Status: reviewed`, still in `.aw/records/plans/pending/`, and `integration-blocked` remains TERMINAL in both drivers (`oc_runipd.py:6754-6767`, `agy_runipd.py:3813` set `fail_status` to `integration-blocked` or `merge-conflict`, both finalizing). The only `integration_deferred` occurrences are an attempt-record FIELD carrying the reason string, not a non-terminal status. So E-01's own stop condition IS CURRENTLY MET and this plan must not be hand-run today. Re-check `51vw4y`'s status yourself; if it is still unexecuted, STOP AND REPORT, which is a successful outcome for this item.
  - Depends on: none
  - Expected outcome: a written statement, by symbol, that exactly ONE `dirty_tree_overlap` DEFINITION exists and where, that the two driver `integrate_lane_branch` hits are wrappers; plus the ladder's observed state. Any missing prerequisite is a stop-and-report.
  - Execution state: pending

### Task group 2: widen the input set

- [ ] E-02 COMPUTE THE PATH SET THE MERGE WOULD ACTUALLY WRITE, and pass THAT to the dirty check instead of `lane.changed_files`. USE `git merge-tree --write-tree` AND DIFF ITS RESULT TREE AGAINST `HEAD`; do NOT use the merge-base-to-both-tips union this plan originally prescribed, which review MEASURED to be wrong (F-7).
  WHY THE UNION IS WRONG, and it is the most important correction in this plan. The union includes every path main advanced on since the lane base, whether or not the merge WRITES it. Measured 2026-09-10: base has `a.txt`+`b.txt`; lane changes `a.txt`; main advances `b.txt` AND is dirty on `b.txt`. The union is `['a.txt','b.txt']`, so the widened guard returns `['b.txt']` and REFUSES. But the merge SUCCEEDS (`git merge --no-ff` exit 0, "Merge made by the 'ort' strategy", touching only `a.txt`) and the co-worker's dirty edit to `b.txt` SURVIVES intact. So the union refuses a previously-integrating case, which E-03 and V-03 define as a FAILURE of this plan. The union is not merely imprecise; it violates this plan's own acceptance bar.
  THE CORRECT SET IS WHAT THE MERGE RESULT CHANGES RELATIVE TO HEAD. Compute `git merge-tree --write-tree HEAD <lane>` to get the merge result tree, then `git diff --name-only HEAD <tree>`. Measured on both fixtures: the rename case yields `['renamed.txt']` (correctly BLOCKS, and the real merge does fail there), while the main-advanced case yields `[]` (correctly ALLOWS, and the real merge does succeed). That is exactly the discrimination this plan needs and the union cannot make.
  HANDLE THE CONFLICT EXIT SEPARATELY. `git merge-tree --write-tree` exits non-zero when the merge conflicts; a conflicting merge is a `merge-conflict` (terminal) and must NOT be reclassified as deferrable dirt, per OQ-01. Treat a non-zero merge-tree exit as "let the existing gate classify it", never as an empty path set, or a conflict would silently pass the dirty guard on a fabricated empty set.
  RECORD THE GIT FLOOR: `--write-tree` requires git >= 2.38 (measured available here: git 2.43.0). If the executor finds the repo must support older git, that is a REPORTABLE constraint and a reason to re-open OQ-02, not a licence to fall back to the union that F-7 disproves.
  KEEP THE RENAME HANDLING THE FUNCTION ALREADY HAS. Its porcelain parser takes both endpoints of a `orig -> dest` rename as dirty; that behavior is correct and must survive, because the reproduced failure was a rename.
  - Depends on: E-01
  - Expected outcome: the pre-merge check receives exactly the paths the merge result changes relative to HEAD; the reproduced rename case returns `['renamed.txt']` where it previously returned `[]`, AND the main-advanced-plus-dirty case still returns `[]` so it keeps integrating.
  - Execution state: pending

- [ ] E-03 PROVE THE DISPOSITION CHANGES AND THAT NOTHING BECAME PERMISSIVE. The observable win is classification: the reproduced case must now yield `integration-blocked` (with the accurate operator-facing reason naming the paths) instead of `merge-conflict`. Assert the reason string names the offending path.
  THE ANTI-REGRESSION HALF IS THE LOAD-BEARING ONE: widening an input set to a REFUSAL can only ever refuse MORE, so prove no case that previously integrated now refuses. Enumerate and assert: a clean main still fast-forwards; a clean main that has advanced still non-ff merges; dirt on a genuinely non-overlapping path still integrates and is left untouched (verified 2026-09-07 and again 2026-09-10: git only writes paths the merge result changes, and the dirty edit survives). A widened check that refuses a previously-clean integration is a FAILURE of this plan, not a stricter success.
  ONE ANTI-REGRESSION CASE IS MANDATORY AND NAMED, because it is the case that disproved this plan's original algorithm (F-7). Fixture: base has `a.txt` and `b.txt`; lane changes ONLY `a.txt`; main ADVANCES `b.txt` with a commit AND is left DIRTY on `b.txt`. Assert the widened guard returns `[]` and the integration still SUCCEEDS, and assert the co-worker's dirty `b.txt` content is intact afterwards. Measured: the real `git merge --no-ff` exits 0 here and preserves the dirt, so a guard that blocks this is wrong. If your implementation blocks it, you have built the union rather than the merge-result diff, and E-02 tells you why that is wrong.
  DO NOT TURN A REAL CONFLICT INTO A DEFERRAL. `merge-conflict` must remain reachable and terminal for genuine textual conflict; only the dirty-overlap case moves. Assert a true conflict still returns `merge-conflict`.
  - Depends on: E-02
  - Expected outcome: the reproduced case classifies `integration-blocked` with the paths named; every previously-integrating case still integrates; genuine conflict still returns `merge-conflict`.
  - Execution state: pending

- [ ] E-04 TEST THROUGH REAL GIT MERGES ON BOTH HOSTS, in a new `tests/test_merge_dirty_scope.py`, because the defect is precisely that real merge state was never consulted. Build the reproduced fixture: base with `a.txt`; lane changes `a.txt`; main renames `a.txt` to `renamed.txt` and is dirty there; assert the widened check catches it.
  A MOCKED PATH SET PROVES NOTHING HERE. The bug is in which paths get computed from real git history, so a test that hands the function a pre-built list would have passed against the broken code. Drive actual `git merge` behavior in a throwaway repository.
  ASSERT BOTH HOSTS FROM THE ONE SHARED IMPLEMENTATION. After `6sb3yu` there is a single function; assert by object identity that both drivers reach it, rather than running the same assertions twice against two symbols.
  - Depends on: E-03
  - Expected outcome: a test failing against pre-change HEAD on the rename case, passing after, driven through real merges, with both hosts shown to use one implementation.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `6sb3yu` HAS LANDED (`executed`, verified at review): `dirty_tree_overlap` is now a single definition at `runner_shared.py:888`, called once at `:1003`, and the two driver `integrate_lane_branch` symbols are thin wrappers binding `host_label`/`run_checked`. This plan is sequenced after it and that sequencing held.
- `51vw4y` HAS *NOT* LANDED (`reviewed`, still in `pending/` at review), so `integration-blocked` is still TERMINAL and this plan's E-01 stop condition is currently MET. `5wdoze` line 113 explicitly pairs the two: "these two must be reconciled, not stacked blindly".
- THE MERGE'S WRITE SET IS `git merge-tree --write-tree` DIFFED AGAINST HEAD, not a merge-base union. Measured at review: the union refuses a merge that succeeds safely (F-7), so the union is disqualified by this plan's own anti-regression bar.
- `git merge-tree` IS NOT USED ANYWHERE IN THE PACKAGE TODAY (only mentioned in an `engine.py` comment), so E-02 introduces a new git primitive to this codebase; treat its exit-code contract explicitly rather than assuming it mirrors `git merge`.
- Every re-attempt must route through `orchestrate_isolation.execute_merge_and_revalidate_gate`; `git merge-tree` cleanliness proves absence of TEXTUAL conflict only, never that the suite still passes.
- NO DIRT RESOLUTION: the driver's only recovery on this path is `git merge --abort`. Keep it that way.
- Shared checkout, and both driver modules are being edited by concurrent runs. Re-locate every symbol.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | wrong input set | The guard is called with `lane.changed_files`, so paths the merge writes but the lane never touched are unchecked. | reproduced 2026-09-07: `dirty_tree_overlap(repo, ["a.txt"])` -> `[]` while `git merge --no-ff` failed on `renamed.txt` |
| F-2 | HIGH | sequencing, not transcription - NOW RESOLVED | The item said TWO copies at `oc:1923`/`agy:1156`; at authoring they were at `oc:1951`/`agy:1241`. RE-VERIFIED AT REVIEW 2026-09-10: `6sb3yu` is `executed` and there is now EXACTLY ONE definition, `runner_shared.py:888`, called once at `runner_shared.py:1003`. The sequencing worked; E-01's two-copy stop condition will not fire. | `grep -n "def dirty_tree_overlap" agent_workflows/*.py` -> one hit |
| F-3 | HIGH | ladder interaction | Widening a refusal's input set makes refusal MORE reachable. Doing that while every refusal is terminal makes the failure worse; after the ladder it makes recovery better. Order matters. | `5wdoze:113`; `51vw4y` adds non-terminal `integration-deferred` |
| F-7 | HIGH | THE PRESCRIBED ALGORITHM CAUSES THE REGRESSION THIS PLAN FORBIDS | E-02 originally specified the merge-base-to-both-tips UNION. Measured: base `a.txt`+`b.txt`; lane changes `a.txt`; main advances AND dirties `b.txt`. Union = `['a.txt','b.txt']` so the guard returns `['b.txt']` and REFUSES, yet the real `git merge --no-ff` exits 0 ("Merge made by the 'ort' strategy", touching only `a.txt`) and the dirty `b.txt` survives intact. That is a previously-integrating case now refusing, which V-03 defines as a FAILED validation. The correct set is `git merge-tree --write-tree HEAD <lane>` diffed against HEAD: measured `['renamed.txt']` on the rename fixture (correctly blocks) and `[]` here (correctly allows). | both fixtures built and merged at review; `git merge-tree --write-tree` run on each |
| F-8 | HIGH | THE PLAN'S OWN STOP CONDITION IS CURRENTLY MET: THE LADDER HAS NOT LANDED | `51vw4y` is `Status: reviewed` and still in `pending/`. `integration-blocked` remains TERMINAL in both drivers (`oc_runipd.py:6754-6767`, `agy_runipd.py:3813`); the only `integration_deferred` occurrences are an attempt-record field holding the reason string, not a non-terminal status. So E-01 must STOP today, and `Item-Dependencies: executed:51vw4y` correctly makes the runner mark this `dependency-blocked` rather than running it. | both plans' `- Status:` read; both driver call sites read |
| F-9 | MEDIUM | THE `integrate_lane_branch` GREP IS A TRIPWIRE FOR E-01's STOP RULE | `grep "def integrate_lane_branch"` returns THREE hits, but the two driver hits are thin wrappers delegating to the shared implementation and binding only `host_label`/`run_checked` (both docstrings cite `6sb3yu`). An executor applying E-01's "more than one means stop" to this symbol would wrongly refuse to proceed. The stop rule keys on `dirty_tree_overlap` definitions only. | all three definitions read at review |
| F-10 | MEDIUM | THE PLAN OMITS `Priority` AND `Work-Kind` WHILE ITS SOURCE ITEM CARRIES BOTH | Backlog `h1ksy6` is `Priority: high`, `Work-Kind: bug`, `Blocks-Release: next`. The plan inherited the release gate but not the other two, and it is a release blocker for the single `planned` release `f33nrj` (2.0.0), so its priority is load-bearing for what gets done before ship. | `h1ksy6` front matter; `.aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md` |
| F-11 | LOW | `merge-tree --write-tree` HAS A GIT FLOOR | It requires git >= 2.38; measured 2.43.0 here. The repo declares no minimum-git capability check, so an older-git environment is an unmeasured assumption rather than a known-safe one. Report it if found rather than falling back to the disproved union. | `git --version`; no git-floor check found in `host_capabilities.py` |
| F-4 | MEDIUM | severity is diagnostic today | Git fails closed on its own in every dangerous case and the driver only ever `merge --abort`s, so today's cost is a worse message, not lost work. Do not call this a data-safety bug. | verified 2026-09-07: no `reset`/`checkout -f`/`stash`/`clean` on the integration path; dirty non-overlapping edits survive a successful merge |
| F-5 | MEDIUM | dead prior gate | The item's original `Gate-Kind: artifact` / `Gate-Ref: 2c122z` pointed at a plan retired to `superseded/` in `70b5338a`, so the gate was released and the defect left unowned. That is why it is being graduated now rather than waiting. | `2c122z` is in `.aw/records/plans/superseded/` |
| F-6 | LOW | rename handling exists | The porcelain parser already treats both endpoints of `orig -> dest` as dirty; the reproduced failure was a rename, so this behavior must survive the widening. | `dirty_tree_overlap` docstring and body |

## Proposed changes (ordered, validatable)

1. Confirm exactly ONE `dirty_tree_overlap` DEFINITION exists post-extraction (it does), and that the ladder is present (at review it was NOT); otherwise stop and report (E-01).
2. Compute the merge's real write set as `git merge-tree --write-tree` diffed against HEAD, not the union, and pass it to the check (E-02).
3. Prove the disposition changes to `integration-blocked` and that nothing previously-integrating now refuses (E-03).
4. Test through real merges on both hosts from the one shared implementation (E-04).

## Deferred / out of scope (with reason)

- CONTENT-BASED NARROWING of the false-positive rate (skip the refusal when main's dirty version is byte-identical to what the merge would produce): declined by the maintainer 2026-09-05 as low-value relative to the ladder. Recorded, not implemented.
- PATH-CATEGORY ALLOWLISTS ("docs are safe", "review records are harmless"): explicitly REJECTED, not deferred. They reason about who probably wrote a file rather than whether it can conflict, which is the fail-open inference `d07nz2` prohibits.
- THE DEFERRAL LADDER ITSELF: `51vw4y`. This plan depends on it and does not reimplement any rung.
- THE EXTRACTION: `6sb3yu`. This plan depends on it and must not perform it.
- OWNERSHIP DETECTION (`a8eufb`): would improve the refusal MESSAGE by naming whose dirt it is; orthogonal to which paths are checked.

## Scope check

- Over-scope: none. One shared module, two drivers (call sites only), two test files.
- Under-scope: this plan does NOT extract the function (`6sb3yu`, already landed), does NOT add or alter any ladder rung (`51vw4y`), and does NOT narrow the refusal by content or category.
- Scope-Paths justification, added at review: `agent_workflows/runner_shared.py` holds the single `dirty_tree_overlap` (`:888`) and its one call site inside `integrate_lane_branch` (`:1003`), which is the line E-02 changes; `tests/test_runner_shared.py` holds the existing coverage of that function; `tests/test_merge_dirty_scope.py` is new and carries the real-git fixtures (E-04). `agent_workflows/lane_containment.py` is declared but this review found NO change it needs: the pre-merge guard and its call site both live in `runner_shared.py`, and `lane_containment.evaluate_clean_base` is a DIFFERENT (base-cleanliness) check the plan does not touch. Either justify the edit at execution or drop the path, because `aw ipd finalize` refuses to complete without a `--scope-ack` for a declared-but-unmodified path.
- NOT declared and correctly so: `oc_runipd.py` and `agy_runipd.py`. Their `integrate_lane_branch` are wrappers and their `integration-blocked` classification is `51vw4y`'s to change, not this plan's.

## Required tests / validation

New `tests/test_merge_dirty_scope.py` driving REAL git merges in throwaway repositories, covering the reproduced rename case, the FOUR previously-integrating cases (clean fast-forward; clean advanced non-ff; dirt on a non-overlapping path; and the mandatory F-7 case of main advanced AND dirty on a path the lane never touched), a conflicting `merge-tree` exit, and a genuine textual conflict still returning `merge-conflict`. Plus the bare suite on a self-measured delta.

Baseline measured at review 2026-09-10 at HEAD `751904e3`: `1 failed, 5958 passed, 3 skipped, 2 xfailed in 56.85s`. The single failure is `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which is ENVIRONMENTAL: it globs the tree and trips over the gitignored local `opencode-recovery/` directory (`.gitignore:49`). It will not reproduce on a clean checkout. Measure your OWN baseline and compare failure sets by NODE ID, never totals; this plan's separate note about ~14 `test_run_viewer.py` failures inside a lane worktree still applies and belongs to `agrlvw`/`utwr6y`.

State the git version used, since E-02 introduces `git merge-tree --write-tree` (git >= 2.38; 2.43.0 measured here) and it is the first use of `git merge-tree` in this package (F-11).

## Spec / documentation sync

No `.spec.md` is amended: this plan changes which paths a check consults, not any contract. Spec `25kzda`'s integration dispositions (`integration-blocked`, `merge-conflict`) already exist and keep their meanings; this plan makes the classification ACCURATE rather than redefining either.

`dirty_tree_overlap`'s DOCSTRING (`runner_shared.py:888`) is the authoritative prose on what the guard compares, and it currently says it reports paths overlapping "an incoming lane's `changed_files`". That sentence becomes FALSE the moment E-02 lands, so it must be updated in the same change to say the input is the paths the MERGE RESULT would write. Leaving it would strand a docstring that describes the exact defect this plan fixes.

The same docstring must record WHY the input is the merge-result diff and not a merge-base union, citing the measured counterexample (F-7). Without that, the next reader will "simplify" it back to a union, which reads as more thorough and is measurably wrong.

The operator-facing refusal reason is user-facing prose: it must name the offending paths and must NOT tell the operator to commit or stash work AGENTS.md forbids them to touch (`z2isfg` wording discipline). Write no em or en dashes there.

## Open questions

### OQ-01: Should the widened set also include paths a merge would write only under conflict resolution?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED, and the answer SURVIVES the algorithm correction with its reasoning strengthened: NO, out of scope and unnecessary. A path written only DURING conflict resolution is by definition already a `merge-conflict`, which stays terminal and correctly needs a human, so classifying it as deferrable dirt would be wrong. NOTE THE PREMISE CHANGED WHILE THE ANSWER DID NOT: the original rationale said the merge-base-to-both-tips union "covers every path a clean merge writes", which review measured to be an OVER-count rather than a cover (F-7). The corrected computation, `git merge-tree --write-tree` diffed against HEAD, is the EXACT set a clean merge writes, so it answers this question more precisely than the union did. The closing clause is now load-bearing rather than cautionary: widening further would refuse integrations that would have succeeded, which is exactly the failure the union produced and which E-03's anti-regression half exists to prevent.

### OQ-02: The ladder (`51vw4y`) has not executed. Proceed, or wait?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Finding: PR-002
- Resolution or deferral rationale: RESOLVED 2026-09-10 (`/askme`): THE ORDERING IS ALREADY ENFORCED MECHANICALLY, so there was nothing here for the maintainer to decide, and `- Blocking:` is CORRECTED to `no` because a scheduling preference is not a statement that this plan is unready.
  THE MAINTAINER CHALLENGED THE QUESTION AND WAS RIGHT. Asked to approve `51vw4y` first, they replied: "Are you asking me to approve `51vw4y` before running this even though if I don't approve `51vw4y` this would refuse to run anyway? Are you concerned that someone would override the prerequisite? What is this mitigating that would not be required and enforced already?" Their stated worry was narrow and legitimate: "I was just worried that I missed some scenario where the prerequisite would be skipped." MEASURED AT HEAD `3b79f787`, THERE IS NO SUCH SCENARIO. (1) The edge is RE-CHECKED AT DISPATCH, not only at queue build: `edge_satisfied` is called from the selection loop (`oc_runipd.py:3581`, defined `:3345`). (2) There is NO bypass flag: re-queueing a `dependency-blocked` item happens ONLY under the `if retry_incomplete:` branch of `run_queue`, and that comes exclusively from an explicit `--retry-incomplete` on `resume`, so a bare `resume` leaves the item blocked (`oc_runipd.py:342-357`). (3) `dependency-blocked` is in `TERMINAL_STATES`, so the item does not quietly re-enter the queue.
  THE REMAINING ARGUMENT WAS ALSO WEAK AND IS WITHDRAWN. The prompt claimed approving this plan alone would leave it "silently unshippable"; it is not silent. The driver carries `DEPENDENCY_BLOCK_RECOVERY_HINT` in the event payload and the run report precisely because "a block whose exit is undocumented is a usability failure", so a held item names its cause and its recovery command.
  SO THIS QUESTION SHOULD NOT HAVE BEEN ASKED, and the mis-classification is the actual defect it exposed: it requested a SCHEDULING choice (which plan to approve first) while marked `Blocking: yes`, which held a `Priority: high` release blocker at `- Readiness: no-go` for a constraint the runner already enforces. Per the maintainer's ruling earlier the same day, a non-blocking question does not make a plan not-ready. A future reviewer must not mark an approval-ordering preference as blocking.
  WHAT REMAINS TRUE AND IS UNCHANGED: the sequencing rationale itself is sound and the edge stays. `51vw4y` is `reviewed`/`go-pending-approval` and `integration-blocked` is still in `TERMINAL_STATES` (verified), so E-01's stop condition genuinely holds and widening the refusal before the ladder lands would still make transient co-worker dirt fatal more often. Option (C), dropping the edge, remains REFUSED. Approving this plan while `51vw4y` is unapproved is now understood as merely no progress, not a hazard.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `grep -n "def dirty_tree_overlap" agent_workflows/*.py` showing EXACTLY ONE definition and naming its module (expected `runner_shared.py`), plus its single call site. Paste `grep -n "def integrate_lane_branch" agent_workflows/*.py` AND enough of the two driver bodies to show they are delegating wrappers, so the three hits are not mistaken for surviving duplication (F-9).
    Paste evidence of the ladder's state: `51vw4y`'s `- Status:` and directory, AND the driver code that classifies `integration-blocked`, showing whether it is terminal. At review the ladder was ABSENT and `integration-blocked` was terminal, so the expected outcome TODAY is a STOP. If you stopped, paste what you found and confirm NO edit was made; a stop-and-report is a successful outcome for this item, not a failure.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the new path-set computation and the git commands it runs, and show it uses `git merge-tree --write-tree` diffed against HEAD rather than the merge-base-to-both-tips union. Paste the REPRODUCED CASE end to end: build base/lane/main-rename, show `dirty_tree_overlap` returning `[]` for the OLD input set and `['renamed.txt']` for the new one, in the same fixture.
    THEN PASTE THE UNION-DISPROOF CASE (F-7), which is what proves you implemented the right algorithm: base `a.txt`+`b.txt`, lane changes `a.txt`, main advances AND dirties `b.txt`. Show the new computation returns `[]` here. If it returns `['b.txt']` you built the union, and this item FAILS.
    Paste the conflict-exit handling: show a conflicting merge does not yield a fabricated empty path set. Confirm the rename endpoint handling survived by pasting a `orig -> dest` porcelain line being parsed. State the git version you ran against (F-11).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the reproduced case's disposition as `integration-blocked` (NOT `merge-conflict`) with the operator-facing reason naming `renamed.txt`.
    THEN PASTE THE ANTI-REGRESSION SET, which is the half that can actually break something: a clean main fast-forwarding; a clean advanced main non-ff merging; dirt on a genuinely NON-overlapping path still integrating with the dirty edit shown intact afterwards; AND the mandatory F-7 case (main advanced on `b.txt` AND dirty on `b.txt` while the lane touched only `a.txt`) integrating successfully with the co-worker's `b.txt` content shown intact. Any previously-integrating case that now refuses is a FAILED validation, and the F-7 case is the one this plan's original algorithm got wrong, so its evidence is not optional.
    Paste a genuine textual conflict still returning `merge-conflict`, proving the terminal path survives.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new test FAILING against pre-change HEAD on the rename case and passing after. Paste proof the tests drive REAL merges (the fixture's git commands), not a hand-built path list. Paste the object-identity check showing both drivers reach ONE `dirty_tree_overlap`.
    Paste the bare `python3 -m pytest` summary line with a self-measured BEFORE baseline and the AFTER-minus-BEFORE failure set EMPTY. Inside a lane worktree, ~14 `test_run_viewer.py` failures belong to the separate `agrlvw` defect (plan `utwr6y`); do not report them as this plan's.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`).

THIS PLAN IS ORDER-SENSITIVE, E-01 ENFORCES IT, AND ONE OF ITS TWO PREREQUISITES IS CURRENTLY UNMET. It declares `executed:6sb3yu` (so there is ONE function to fix, not two) and `executed:51vw4y` (so a widened refusal is deferrable rather than terminal). VERIFIED AT REVIEW 2026-09-10: `6sb3yu` IS `executed` and the single function exists; `51vw4y` is only `reviewed` and still in `pending/`, and `integration-blocked` remains TERMINAL in both drivers. So this plan is NOT runnable today, and that is working as designed: the runner re-checks dependencies at dispatch and will mark this item `dependency-blocked` and continue. Do NOT hand-run it: without the ladder you would make transient dirt permanently fatal MORE often, which is precisely what `5wdoze:113` warns against.

WIDENING A REFUSAL CAN ONLY REFUSE MORE, so the anti-regression evidence in V-03 is not optional garnish; it is the proof this plan did not break integration. If a previously-integrating case now refuses, the plan is wrong, not the case. THIS IS NOT HYPOTHETICAL: the algorithm this plan ORIGINALLY prescribed (the merge-base-to-both-tips union) was measured at review to refuse a merge that succeeds safely and preserves the co-worker's dirt (F-7). E-02 now prescribes `git merge-tree --write-tree` diffed against HEAD instead, and V-02/V-03 require the disproving fixture as evidence that you implemented the corrected algorithm rather than the original one.

DO NOT RELAX ANY REFUSAL to make a test pass, and do not resolve dirt. The driver's only recovery on this path is `git merge --abort`; keep it that way.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT: run `aw runs` before starting, and re-locate every cited symbol, since this plan's own line numbers are the second generation and will move again.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

On completion, close backlog `h1ksy6` (this plan carries `- From-Backlog: h1ksy6` and inherits its `Blocks-Release: next`, which resolves to the single `planned` release `f33nrj` / 2.0.0, verified at review). Note `h1ksy6`'s own text still describes a two-copy tree and cites stale line numbers; the close should not propagate those. `Priority: high` and `Work-Kind: bug` were added at review from that item, which the plan had omitted while inheriting the release gate (F-10).
