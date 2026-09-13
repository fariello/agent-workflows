# IPD: Close a backlog item inside the lane so nothing writes to the shared checkout mid-run

- Date: 2026-09-13
- Kind: child
- Concern: The plan's own lifecycle move happens IN THE LANE and reaches main via the merge, but the backlog close happens IN MAIN, after integration and after the worktree is already torn down. So a successful item still mutates and commits into the shared checkout mid-run. When that commit lands only half the move, the shared tree is left dirty, which is exactly how three runs lost 68 items combined.
- Scope: Perform the backlog item's status move inside the lane, before the lane's finalize commit, so it lands if and only if the merge lands. Excludes the pre-launch gate (Order 01), the integration gate (Order 02), and orchestrator retirement (Order 04). Excludes changing which items are ELIGIBLE to close; the eligibility rule is reused unchanged.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Set: dirtygates
- Order: 3
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: 9iq461
- Priority: high
- Work-Kind: bug

## Workflow history

- 2026-09-13 reviewed (opencode (its_direct/pt3-claude-opus-5-1m-us)): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-301..PR-306 all FIXED; review record written; Readiness go-pending-approval. No collision with the approved `integpath`/`mergedirty`/`dirtybase` plans, unlike Orders 01 and 02.
- 2026-09-13 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-09-13 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): authored after tracing the finalize/integrate/teardown/close ordering in the live code and measuring how many backlog items have more than one carrier plan (20 of 107), which is the fact that shapes OQ-01.

## Goal

Make a successful item's bookkeeping arrive on main the same way its code does: as part of one merge. Nothing the runner does for a successful item should write to the shared checkout while the run is still going.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: move the write into the lane

- [ ] E-01 Move the backlog item's status change so it happens in the LANE tree rather than main. Today `process_backlog_close(run_dir, state, item)` is called at `oc_runipd.py:6863`, AFTER `integrate_lane_branch` (`:6740`) and AFTER `teardown_isolation_worktree` (`:6825`), and it operates on `repo` (main). The plan's own move already happens in the lane because `finalize_repo = Path(work_dir) if (work_dir and wt_handle) else repo` (`:6713`). Perform the item's move against the lane tree in that same window, so the lane's finalize commit carries BOTH the plan transition and the backlog transition. Preserve the non-isolated case (`wt_handle is None`) exactly as it behaves today.
  THE MECHANISM IS ALREADY THERE, VERIFIED AT REVIEW (F-8), so do not invent one: `close_backlog_item` shells `aw backlog set <id6> --status done ... --dir <repo> --no-commit` (`:1316-1328`), so redirecting the MOVE at the lane is passing the lane path as `--dir`, and the setter already does not commit. DO NOT CHANGE THE `--status done` SPELLING while you are in that call: the positional form (`aw backlog set done <selector>`) dispatches elsewhere and SKIPS `check_engine.evaluate_blocking_close`, so the runner's close would stop being gated. The function's own docstring records this as measured and load-bearing.
  ALSO REDIRECT `resolve_backlog_item`, not only the setter. `process_backlog_close` resolves the item path against `repo` (`:1467`) before calling the setter, and it must resolve in whichever tree the move will happen so the two agree; a lane-side move driven by a main-side path is the half-state this plan exists to remove.
  - Depends on: none
  - Expected outcome: for an isolated turn, `git status --porcelain` in MAIN is unchanged across the whole item, and the backlog move appears in the merge.
  - Execution state: pending
- [ ] E-02 Remove the now-redundant separate close COMMIT on main. `commit_backlog_close` (`:1340-1422`) exists solely because the setter moves the file without committing and "leaving it would hand the next turn a dirty main tree". Once the move rides the lane's commit, a second commit on main is not merely unnecessary, it is the exact mid-run write this plan removes. Do not delete the helper blindly: it is also reachable from the non-isolated path, which must keep working.
  - Depends on: E-01
  - Expected outcome: no commit is created on main by the close on the isolated path; the non-isolated path still commits as before.
  - Execution state: pending

### Task group 2: keep the eligibility decision honest

- [ ] E-03 Evaluate eligibility IN MAIN, BEFORE the merge, and perform only the MOVE in the lane (OQ-01, resolved: option (a)). `evaluate_backlog_close` (`:1122`) asks two questions: may this run close at all (the `earned_paths` gate), and do ALL carriers of the item prove the work. Keep that call against `repo` (main), where the coordinator sees every carrier's true state, because carrier discovery scans the FILESYSTEM (F-6) and 21 of 108 carried items have more than one carrier, one with NINE (F-5), so a lane-side evaluation could close an item whose sibling carrier has not run. THE ORDERING THAT FOLLOWS: evaluate before integration while the lane still exists, and if the verdict is `close`, perform the move inside the lane so it rides the merge. A `close=False` verdict must still be recorded with its reason (E-04). The `earned_paths` gate MUST keep refusing a close this run did not earn.
  SOLVE THE EARNED-PATHS PROBLEM EXPLICITLY OR THIS ITEM SILENTLY DISABLES ALL CLOSING (F-7). `evaluate_backlog_close`'s `earned_paths` argument comes from `run_earned_paths(state)`, fed by `collect_earned_paths`, which runs `git diff --name-only <starting_head>..<ending_head>` with `cwd=repo` (`:1279-1281`). For an isolated turn BOTH commits live on the LANE BRANCH, so BEFORE the merge that diff fails or returns nothing in main. The function is best-effort by design and its docstring says fewer earned paths "can only ever WITHHOLD a close": therefore evaluating in main pre-merge does not raise, it QUIETLY yields an empty earned set and the gate refuses every close forever. Choose one and say which in the code comment: (a) compute `earned_paths` from the LANE (`work_dir`) where the commits exist, while keeping the CARRIER scan against main, which is the split OQ-01 actually implies; or (b) resolve the lane commits from main by SHA, which works because the lane branch ref is visible in the same repository (`git diff` on a branch's commits does not require checkout). Option (a) is preferred and is the smaller change.
  DO NOT ACCEPT A GREEN E-05 AS PROOF THIS WORKED. E-05's regression asserts items 2 and 3 run and MAIN stays clean; a permanently-refusing close satisfies all of that. V-03 therefore requires a POSITIVE close (an item actually reaching `done` via the merge) plus the earned-paths gate still refusing an unearned close, which is the only pair that distinguishes "correct" from "silently disabled".
  - Depends on: E-01
  - Expected outcome: a multi-carrier item whose sibling has not executed is never closed, an ELIGIBLE item IS still closed (proving the earned-paths computation survived the move), and the decision is taken from main's carrier view while the write lands via the merge.
  - Execution state: pending
- [ ] E-04 Preserve the fail-closed behavior and the reporting. `evaluate_backlog_close` wraps every lookup and returns a recorded reason rather than raising, and `process_backlog_close` records the verdict either way so the run summary can list every item left open WITH its reason (the `Backlog items left open` block). Moving the work must not lose that reporting, and must not turn a recorded refusal into an escaping exception that fails the item.
  - Depends on: E-01, E-03
  - Expected outcome: the run summary still lists every item left open with its reason, and no close path can raise.
  - Execution state: pending

### Task group 3: parity and regression

- [ ] E-05 Apply the same change to `agy_runipd.py` and add the regression that this Set exists for: a queue of at least three isolated execute items where item 1 closes a backlog item, and items 2 and 3 still run. Assert MAIN's `git status --porcelain` is empty after item 1. That single assertion is what would have caught the original defect, and its absence is why three runs failed identically.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: both hosts behave identically and the cross-item contamination cannot regress silently.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A WORKER may commit facts about its own item; only the COORDINATOR may commit facts about a whole Set. `retire_orchestrator` enforces this with a worker-role gate as its FIRST check (`ipd_lifecycle.py:2237`), refusing when `AW_EXECUTION_ROLE=worker`. A backlog close is a consequence of THIS plan, so it is legitimately worker-side; that is precisely why this plan is possible and Order 04 needs a different mechanism.
- `finalize_repo` is the existing, tested seam for "do this in the lane if isolated, else in main". Reuse it rather than inventing a second selector.
- The status setter now relocates with `git mv` (commit `c53849e5`), so the move is one staged rename. This plan should not reintroduce any pair-the-halves logic.

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | The plan move and the backlog move are handled asymmetrically for no stated reason. | plan move: `finalize_repo` in the lane (`oc_runipd.py:6713`); backlog move: `repo` in main (`:6863`, `:1467-1478`) |
| F-2 | The close runs AFTER teardown, so the lane no longer exists at that point. Reordering is therefore part of the work, not just re-pointing a path. | `teardown_isolation_worktree(repo, wt_handle)` at `:6825`, `process_backlog_close(...)` at `:6863` |
| F-3 | The existing rationale for closing on main does not survive scrutiny. The comment at `:6859-6862` argues the close must wait because only then is the plan "genuinely `executed` on main". But a merge is atomic: if it succeeds both moves land, if it fails neither does. The property the comment wants is better achieved by riding the merge. | the comment itself, plus the merge behavior measured for Order 02 |
| F-4 | The measured harm is cross-item, not per-item. One item's own bookkeeping disabled the remainder of three runs: 27 of 42, 23 of 41, 18 of 43 items refused, all naming a single uncommitted backlog markdown file. | runs `run-20260913T031350Z-1732436`, `run-20260913T031148Z-1722898`, `run-20260913T031521Z-1774617` |
| F-5 | Multi-carrier items are common enough to matter. RE-MEASURED AT REVIEW: 21 of 108 items with at least one `From-Backlog` carrier have MORE THAN ONE carrier (the plan said 20 of 107; the tree moved). The tail is longer than "two carriers": `kjzlgw` has 9, and `dh0uno`, `h7qsje` and `wjl471` have 3 each. So "are all carriers executed?" is a real question, and the code's own comment cites `dh0uno` as the case that would have closed with half its work unwritten. | re-measured at review across `.aw/records/plans/**/*.ipd.md` and `.aw/records/specs/**/*.spec.md` for `- From-Backlog:`; `oc_runipd.py:1183-1186` cites `dh0uno` |
| F-6 | Carrier discovery reads the filesystem, not git refs, so the answer differs between the lane tree and main. VERIFIED AND EXTENDED AT REVIEW: `find_from_backlog_artifacts` returns plans AND SPECS (`check_engine.py:1936-1943`, `find_from_backlog_specs`), because a spec-first graduation preserves the gate as well as a plan does. So a carrier is not necessarily an IPD, and `evaluate_backlog_close` applies the strict "every IPD carrier must be terminal `executed`" rule ONLY when at least one IPD carrier exists (`oc_runipd.py:1178-1200`). Any lane-side reasoning must not assume carriers are plans. | `check_engine.find_from_backlog_artifacts` (`:1946-1959`), `find_from_backlog_specs` (`:1936-1943`); `oc_runipd.evaluate_backlog_close` (`:1155-1200`) |
| F-7 | THE EARNED-PATHS GATE IS COMPUTED FROM GIT COMMITS THAT DO NOT EXIST IN MAIN BEFORE THE MERGE, which is the concrete hazard E-01/E-03 must handle and did not name. `collect_earned_paths` runs `git diff --name-only <starting_head>..<ending_head>` with `cwd=repo` (`oc_runipd.py:1279-1281`), and for an isolated turn those two commits are on the LANE BRANCH. Its docstring says a git failure "yields fewer earned paths, which can only ever WITHHOLD a close": so evaluating in MAIN before the merge does not crash, it SILENTLY RETURNS FEWER OR ZERO EARNED PATHS and the `earned_paths` gate then refuses every close. That would not fail loudly; it would quietly stop the runner ever closing a backlog item again, and E-05's regression (which asserts items 2 and 3 still run and main stays clean) would still PASS. | `oc_runipd.collect_earned_paths` (`:1266-1296`), its best-effort docstring (`:1269-1270`), and `process_backlog_close` calling it with `repo` (`:1438`) |
| F-8 | THE SETTER IS ALREADY DIRECTORY-PARAMETERIZED AND ALREADY NON-COMMITTING, so E-01 is smaller than it looks and E-02 is nearly free. `close_backlog_item` shells `aw backlog set <id6> --status done ... --dir <repo> --no-commit` (`:1316-1328`), so pointing the MOVE at the lane is a matter of passing the lane path as `--dir`, and no commit is made by the setter itself. The separate `commit_backlog_close` (`:1340`) exists only to commit what the setter left staged. ONE WARNING CARRIED FORWARD: the `--status done` spelling is load-bearing (it routes through the gated `backlog.run_set` which runs `evaluate_blocking_close`, unlike the positional form which does not); do not alter it while changing `--dir`. | `oc_runipd.close_backlog_item` (`:1298-1336`) including its explicit spelling warning; `commit_backlog_close` (`:1340`) |
| F-9 | `plan_bucket` IS A PURE PATH INSPECTOR WITH NO IO, which refines (and partly weakens) OQ-01's stated premise. It decides `executed` from the path SEGMENT and "does no IO and must not learn to" (`runner_shared.py:1463-1487`). So the lane-versus-main difference for a carrier is not about file CONTENT but about which DIRECTORY each carrier file sits in within the tree being scanned. That still supports evaluating in main (in the lane THIS plan's file has already been moved to `executed/`, so a lane-side scan would see it as executed while main does not), but it means the difference is a filesystem-layout difference, not a stale-content one. State it that way so nobody later "fixes" it by reading file contents. | `runner_shared.plan_bucket` (`:1463-1487`), especially "A BUCKET IS A DIRECTORY; READINESS IS A FIELD" and "does no IO and must not learn to (OQ-03)" |

## Proposed changes (ordered, validatable)

1. Perform the item's status move in the lane, inside the finalize window (E-01).
2. Stop committing the close separately on main for the isolated path; keep the non-isolated path intact (E-02).
3. Fix the evaluation point per OQ-01, preserving the `earned_paths` gate (E-03).
4. Preserve fail-closed behavior and the left-open reporting (E-04).
5. Mirror on agy and add the multi-item cross-contamination regression (E-05).

## Deferred / out of scope (with reason)

- Changing WHICH items are eligible to close. The eligibility rule is reused unchanged; only where it runs is in question.
- Orchestrator retirement. It is a Set-level claim, refused from a worker role by design, and Order 04 handles it with a coordinator-owned worktree.
- Post-verifying the close commit contains both halves of the move. Made unnecessary here by `git mv` (commit `c53849e5`) plus riding the lane commit; nothing pairs halves any more.

## Scope check

- Over-scope: none. The change is confined to the two runners and their tests.
- NO INTENT COLLISION, VERIFIED AT REVIEW, which distinguishes this plan from Orders 01 and 02. The three approved `Blocks-Release: next` plans that contradict those two (`fujm0y`, `51vw4y`, `3i0aaz`) mention `process_backlog_close`, `commit_backlog_close` and the backlog close ZERO times between them. Two of them DO declare `oc_runipd.py`/`agy_runipd.py` in their `Scope-Paths`, but that is ordinary file overlap in different regions, which the runner's worktree isolation and merge-and-revalidate gate already handle; it is not a contradictory instruction. So this plan is independently approvable and executable regardless of how the orchestrator's OQ-02 is answered.
- Under-scope: this plan does not remove the `commit_backlog_close` helper, because the non-isolated path still needs it. If review wants isolation to be mandatory, that is a separate decision and a separate plan.

## Required tests / validation

- The cross-item regression of E-05: three isolated items, item 1 closes a backlog item, items 2 and 3 run, MAIN clean after item 1.
- A test proving the backlog move is IN the merge: inspect the merge's `--name-status` and see the item's rename, and confirm no separate close commit exists on main.
- A test proving a FAILED integration leaves the backlog item unclosed and still `graduated`, with the lane preserved. This is the property the maintainer asked for explicitly: the move lands if and only if the merge lands.
- A multi-carrier test per OQ-01's answer, proving an item with a sibling carrier that is not yet executed is NOT closed.
- The non-isolated path unchanged.
- Both hosts. Full suite run bare, with the failure set diffed against a baseline from the same commit.

## Spec / documentation sync

- No spec is expected to change: `bkclose (zhr6mc)` introduced the close and this plan moves WHERE it happens, not WHETHER. VERIFIED AT REVIEW rather than left as a pre-execution chore: the specs tree contains NO requirement that fixes the backlog close to the main checkout (grepped for `zhr6mc`, `backlog_close`, and close-plus-main phrasings across `.aw/records/specs/`; no hit binds the close to a tree). Re-check cheaply at execution in case a spec landed since, but treat this as settled rather than an open risk. If one does appear, amend it in this plan and add the spec file to `Scope-Paths` first.
- Update the comment at `oc_runipd.py:6859-6862`, which currently states the reasoning F-3 disproves.

## Open questions

### OQ-01: Evaluate close eligibility in main before the merge, or in the lane?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-13 by the maintainer: option (a), EVALUATE IN MAIN BEFORE THE MERGE and PERFORM THE MOVE IN THE LANE. So E-03 splits decision from action deliberately. The reason this is the right split, and not merely the cautious one: eligibility asks whether ALL carriers of the item prove the work, which is a claim about several plans, and carrier discovery scans the FILESYSTEM (F-6), so the lane's view genuinely differs from main's (in the lane THIS plan is already `executed/` while siblings show their main state). With 20 of 107 carried items having more than one carrier (F-5), evaluating in the lane could close an item whose sibling carrier has not run. This is the SAME principle Order 04 rests on: a worker may commit facts about its own item, but a claim about several plans belongs to the coordinator. The `earned_paths` gate stays on the main-side evaluation where it already lives.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste MAIN's `git status --porcelain` immediately after an isolated item that closed a backlog item, showing it EMPTY. Paste the merge commit's `--name-status` showing the backlog item's move inside it.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `git log --oneline` for the item's window showing NO separate "closed by aw oc run" commit on main for the isolated path, and paste a non-isolated run showing its close still commits.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste a multi-carrier test result showing an item with an UNEXECUTED sibling carrier is NOT closed, with the recorded reason. Paste a case proving the `earned_paths` gate still refuses a close the run did not earn. Prove the evaluation ran against MAIN (not the lane) by asserting on a fixture where the two views differ: the lane has this plan executed, main does not yet, and the verdict must be computed from main's view.
  - MANDATORY POSITIVE CASE (F-7), because every negative case above is also satisfied by a close path that refuses UNCONDITIONALLY: paste an eligible single-carrier item actually reaching `done` through the merge, with the item file's new path shown in the merge's `--name-status`. State which option E-03 took for `earned_paths` (compute in the lane, or resolve lane commits by SHA from main) and paste the non-empty earned set that proves the gate had real input rather than an empty one. A close-path change whose only evidence is refusals is indistinguishable from a broken one.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste a run summary containing the `Backlog items left open` block with at least one reason, proving the reporting survived. Paste a forced-failure case showing a recorded refusal rather than a traceback.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the three-item regression output showing items 2 and 3 executed and MAIN clean after item 1. Paste the equivalent for agy. Paste the bare full-suite counts before and after with the FAILED-set diff.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit only files this plan changed, path-scoped, never `git add -A`, never push. Paste actual runner output for every test claim. OQ-01 is BLOCKING and must be answered before E-03 is written.

Post-gate lifecycle move: this plan reaches `executed/` only when every V-item above carries pasted evidence and `aw ipd lint --phase pre-transition` reports conforming.
