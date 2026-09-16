# IPD: Close a backlog item inside the lane so nothing writes to the shared checkout mid-run

- Date: 2026-09-13
- Kind: child
- Concern: The plan's own lifecycle move happens IN THE LANE and reaches main via the merge, but the backlog close happens IN MAIN, after integration and after the worktree is already torn down. So a successful item still mutates and commits into the shared checkout mid-run. When that commit lands only half the move, the shared tree is left dirty, which is exactly how three runs lost 68 items combined.
- Scope: Perform the backlog item's status move inside the lane, before the lane's finalize commit, so it lands if and only if the merge lands. Excludes the pre-launch gate (Order 01), the integration gate (Order 02), and orchestrator retirement (Order 04). Excludes changing which items are ELIGIBLE to close; the eligibility rule is reused unchanged.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: dirtygates
- Order: 3
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: 9iq461
- Priority: high
- Work-Kind: bug

## Workflow history
- 2026-09-16 executed (aw oc run): aw oc run self-finalize: 9iq461 verified (set dirtygates, attempt 1). [Scope reconciliation - out-of-scope agent_workflows/lane_containment.py: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope agent_workflows/runner_shared.py: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope tests/test_runner_backlog_close_in_lane.py: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope tests/test_runner_shared.py: changed by the plan's approved execution (auto-reconciled by aw oc run); in-scope-unmodified tests/test_agy_runipd_cli.py: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified tests/test_oc_runipd.py: declared-but-unmodified (auto-acknowledged by aw oc run)]
- 2026-09-14 approved (aw set): status set to approved
- 2026-09-13 reviewed (aw set): /plan-review round 2 (individual): APPROVE WITH REVISIONS APPLIED; PR-307..PR-313 all FIXED; readiness go-pending-approval confirmed
- 2026-09-13 reviewed (opencode (its_direct/pt3-claude-opus-5-1m-us)): /plan-review ROUND 2 (individual review of this child): APPROVE WITH REVISIONS APPLIED; PR-307..PR-313 all FIXED; readiness go-pending-approval CONFIRMED (not merely inherited). `aw ipd lint` CONFORMING at `--phase author` before and `--phase review-finalize` after. This plan was NOT one of the three the orchestrator's OQ-04 named, since it already carried a positive readiness from a clean round 1, so this round asked the sharper question of whether that readiness is still DESERVED. ROUND 1'S WORK HOLDS AND WAS RE-MEASURED RATHER THAN RE-READ: every anchor resolved exactly (`:6713`, `:6740`, `:6825`, `:6863`, the disproved comment at `:6859-6862`, `collect_earned_paths:1266-1296`, `close_backlog_item:1316-1328`), and F-5's multi-carrier count recomputed independently matches EXACTLY at 21 of 108. THE HAZARD ROUND 2 FOUND IS IN THE ONE SENTENCE BOTH THE PLAN AND ROUND 1 RELIED ON (PR-307, HIGH): E-01 and F-8 both treat `--dir` as choosing only where the file moves, but the gated setter route runs `check_engine.evaluate_blocking_close`, which uses its `repo_root` to SCAN THE TREE for release-gate carriers (`check_engine.py:2026`) and to RESOLVE the evidence citation (`:2036`). So passing the lane as `--dir` silently re-points a RELEASE GATE at the lane's view, and the error direction is the PERMISSIVE one: in the lane this plan's own file is already in `executed/` carrying its `From-Backlog` line, so a lane-side scan finds a satisfying carrier main's view would refuse, and a release-gated item could close `done` illegitimately. That is the exact inversion of the caution OQ-01 resolved for the eligibility predicate, applied to only one of the two predicates the redirect touches. PR-309: the validation could not have detected it, because no V-item named that predicate, so a widened gate passed all five items; V-01 now demands the discriminating fixture (a release-gated item whose only candidate carrier is this plan's own file, the single case where lane and main disagree). PR-308: the evidence citation is resolved against the same `repo_root` and is typically this plan's own plan path, whose location differs between the trees. PR-310: the gate still declared the RESOLVED OQ-01 blocking, which would stall an executor who has permission to proceed. PR-311/312/313: F-5's tail understated the multi-carrier concentration (three items at 4 or more, not "3 each"), `check_engine.py` is undeclared while the hazard reaches into it, and one cross-reference cited a since-renumbered question. No requirement was relaxed and no test dropped. No product code was modified by this review.
- 2026-09-13 to-review (aw set): status set to to-review

- 2026-09-13 reviewed (opencode (its_direct/pt3-claude-opus-5-1m-us)): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-301..PR-306 all FIXED; review record written; Readiness go-pending-approval. No collision with the approved `integpath`/`mergedirty`/`dirtybase` plans, unlike Orders 01 and 02.
- 2026-09-13 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-09-13 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): authored after tracing the finalize/integrate/teardown/close ordering in the live code and measuring how many backlog items have more than one carrier plan (20 of 107), which is the fact that shapes OQ-01.

## Goal

Make a successful item's bookkeeping arrive on main the same way its code does: as part of one merge. Nothing the runner does for a successful item should write to the shared checkout while the run is still going.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: move the write into the lane

- [x] E-01 Move the backlog item's status change so it happens in the LANE tree rather than main. Today `process_backlog_close(run_dir, state, item)` is called at `oc_runipd.py:6863`, AFTER `integrate_lane_branch` (`:6740`) and AFTER `teardown_isolation_worktree` (`:6825`), and it operates on `repo` (main). The plan's own move already happens in the lane because `finalize_repo = Path(work_dir) if (work_dir and wt_handle) else repo` (`:6713`). Perform the item's move against the lane tree in that same window, so the lane's finalize commit carries BOTH the plan transition and the backlog transition. Preserve the non-isolated case (`wt_handle is None`) exactly as it behaves today.
  THE MECHANISM IS ALREADY THERE, VERIFIED AT REVIEW (F-8), so do not invent one: `close_backlog_item` shells `aw backlog set <id6> --status done ... --dir <repo> --no-commit` (`:1316-1328`), so redirecting the MOVE at the lane is passing the lane path as `--dir`, and the setter already does not commit. DO NOT CHANGE THE `--status done` SPELLING while you are in that call: the positional form (`aw backlog set done <selector>`) dispatches elsewhere and SKIPS `check_engine.evaluate_blocking_close`, so the runner's close would stop being gated. The function's own docstring records this as measured and load-bearing.
  ALSO REDIRECT `resolve_backlog_item`, not only the setter. `process_backlog_close` resolves the item path against `repo` (`:1467`) before calling the setter, and it must resolve in whichever tree the move will happen so the two agree; a lane-side move driven by a main-side path is the half-state this plan exists to remove.
  `--dir` IS NOT ONLY "WHERE THE FILE MOVES", AND THIS IS THE ITEM'S REAL HAZARD (F-10). The gated setter route runs `check_engine.evaluate_blocking_close` (the same gate F-8 protects by forbidding a spelling change), and that predicate uses its `repo_root` to SCAN THE TREE for release-gate carriers (`check_engine.py:2026`). So passing the lane as `--dir` silently re-points the CLOSE-LEGITIMACY gate at the lane's filesystem view. The error direction is the unsafe one: in the lane this plan's own file is already in `executed/` carrying its `From-Backlog` line, so a lane-side scan is MORE likely to find a satisfying carrier than main's and could legitimize a `done` on a release-gated item main would refuse. DECIDE AND STATE IN A COMMENT which tree the legitimacy gate evaluates against; MAIN is the safe answer, for exactly the reason OQ-01 chose main for the eligibility evaluation. If keeping the gate on main means the move and the gate cannot share one `--dir`, say so plainly rather than quietly accepting the lane for both: that may mean moving the file with the setter pointed at the lane while the LEGITIMACY decision was already taken against main (which E-03 does anyway), or teaching the call to pass the two separately.
  THE EVIDENCE CITATION IS RESOLVED BY THAT SAME GATE (F-11), so it must be valid in whichever tree evaluates it: the SATISFIED route accepts a close only when `resolve_evidence_artifact(repo_root, evidence)` resolves (`check_engine.py:2036`). The evidence is typically this plan's own plan path, which is exactly the path whose LOCATION differs between lane and main. Verify the chosen tree resolves it, and cover that case in a test.
  - Depends on: none
  - Expected outcome: for an isolated turn, `git status --porcelain` in MAIN is unchanged across the whole item, the backlog move appears in the merge, AND the close-legitimacy gate plus its evidence resolution are evaluated against a deliberately chosen tree that is named in a comment.
  - Execution state: performed
- [x] E-02 Remove the now-redundant separate close COMMIT on main. `commit_backlog_close` (`:1340-1422`) exists solely because the setter moves the file without committing and "leaving it would hand the next turn a dirty main tree". Once the move rides the lane's commit, a second commit on main is not merely unnecessary, it is the exact mid-run write this plan removes. Do not delete the helper blindly: it is also reachable from the non-isolated path, which must keep working.
  - Depends on: E-01
  - Expected outcome: no commit is created on main by the close on the isolated path; the non-isolated path still commits as before.
  - Execution state: performed

### Task group 2: keep the eligibility decision honest

- [x] E-03 Evaluate eligibility IN MAIN, BEFORE the merge, and perform only the MOVE in the lane (OQ-01, resolved: option (a)). `evaluate_backlog_close` (`:1122`) asks two questions: may this run close at all (the `earned_paths` gate), and do ALL carriers of the item prove the work. Keep that call against `repo` (main), where the coordinator sees every carrier's true state, because carrier discovery scans the FILESYSTEM (F-6) and 21 of 108 carried items have more than one carrier, one with NINE (F-5), so a lane-side evaluation could close an item whose sibling carrier has not run. THE ORDERING THAT FOLLOWS: evaluate before integration while the lane still exists, and if the verdict is `close`, perform the move inside the lane so it rides the merge. A `close=False` verdict must still be recorded with its reason (E-04). The `earned_paths` gate MUST keep refusing a close this run did not earn.
  SOLVE THE EARNED-PATHS PROBLEM EXPLICITLY OR THIS ITEM SILENTLY DISABLES ALL CLOSING (F-7). `evaluate_backlog_close`'s `earned_paths` argument comes from `run_earned_paths(state)`, fed by `collect_earned_paths`, which runs `git diff --name-only <starting_head>..<ending_head>` with `cwd=repo` (`:1279-1281`). For an isolated turn BOTH commits live on the LANE BRANCH, so BEFORE the merge that diff fails or returns nothing in main. The function is best-effort by design and its docstring says fewer earned paths "can only ever WITHHOLD a close": therefore evaluating in main pre-merge does not raise, it QUIETLY yields an empty earned set and the gate refuses every close forever. Choose one and say which in the code comment: (a) compute `earned_paths` from the LANE (`work_dir`) where the commits exist, while keeping the CARRIER scan against main, which is the split OQ-01 actually implies; or (b) resolve the lane commits from main by SHA, which works because the lane branch ref is visible in the same repository (`git diff` on a branch's commits does not require checkout). Option (a) is preferred and is the smaller change.
  DO NOT ACCEPT A GREEN E-05 AS PROOF THIS WORKED. E-05's regression asserts items 2 and 3 run and MAIN stays clean; a permanently-refusing close satisfies all of that. V-03 therefore requires a POSITIVE close (an item actually reaching `done` via the merge) plus the earned-paths gate still refusing an unearned close, which is the only pair that distinguishes "correct" from "silently disabled".
  - Depends on: E-01
  - Expected outcome: a multi-carrier item whose sibling has not executed is never closed, an ELIGIBLE item IS still closed (proving the earned-paths computation survived the move), and the decision is taken from main's carrier view while the write lands via the merge.
  - Execution state: performed
- [x] E-04 Preserve the fail-closed behavior and the reporting. `evaluate_backlog_close` wraps every lookup and returns a recorded reason rather than raising, and `process_backlog_close` records the verdict either way so the run summary can list every item left open WITH its reason (the `Backlog items left open` block). Moving the work must not lose that reporting, and must not turn a recorded refusal into an escaping exception that fails the item.
  - Depends on: E-01, E-03
  - Expected outcome: the run summary still lists every item left open with its reason, and no close path can raise.
  - Execution state: performed

### Task group 3: parity and regression

- [x] E-05 Apply the same change to `agy_runipd.py` and add the regression that this Set exists for: a queue of at least three isolated execute items where item 1 closes a backlog item, and items 2 and 3 still run. Assert MAIN's `git status --porcelain` is empty after item 1. That single assertion is what would have caught the original defect, and its absence is why three runs failed identically.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: both hosts behave identically and the cross-item contamination cannot regress silently.
  - Execution state: performed

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
| F-10 | THE `--dir` REDIRECT ALSO MOVES A SECOND, UNNAMED GATE, AND THAT GATE IS A RELEASE GATE. E-01 says redirecting the move "is a matter of passing the lane path as `--dir`", treating `--dir` as if it only chose where the file moves. It does not: `aw backlog set --status done` runs `check_engine.evaluate_blocking_close` (the very reason F-8 forbids changing the `--status done` spelling), and that predicate takes `repo_root` and uses it to SCAN THE TREE for carriers via `find_from_backlog_artifacts` (`check_engine.py:2026`, defined `:1947-1959`). So passing the lane as `--dir` silently re-points the HANDOFF check at the LANE's filesystem view rather than main's. THE DIRECTION OF THE ERROR IS THE DANGEROUS ONE: in the lane, THIS plan's own file has already been moved to `executed/` and its `From-Backlog` line is present, so a lane-side scan is MORE likely to find a satisfying carrier than main's, which means a lane-side evaluation could legitimize a `done` transition on a release-gated item that main's view would refuse. That is the exact inversion of the caution OQ-01 resolved for `evaluate_backlog_close`, and this plan applies that caution to only ONE of the two predicates. Note it is not certain to differ (the lane is a worktree of main HEAD, so its committed tree matches; the difference is this plan's own uncommitted-in-main move plus anything else the lane changed), but "usually identical" is not a safety argument for a release gate. E-01 MUST decide and state explicitly which tree the CLOSE-LEGITIMACY gate evaluates against, and the safe answer is main, for the same reason OQ-01 chose main. | `close_backlog_item` passes `--dir <repo>` (`oc_runipd.py:1316-1328`); the setter's gated route runs `evaluate_blocking_close` (`check_engine.py:1980`), whose `done` branch scans with `find_from_backlog_artifacts(repo_root, item_id6)` (`:2026`); the lane is a worktree of main HEAD (`runner_shared.allocate_isolation_worktree:833-847`) |
| F-11 | THE EVIDENCE STRING IS A REPO-RELATIVE PATH THAT THE SAME GATE MUST RESOLVE, so it must be valid in whichever tree evaluates it. `process_backlog_close` builds the close message and passes `verdict.evidence` to the setter (`:1471-1478`), and `evaluate_blocking_close`'s SATISFIED route accepts a close when `resolve_evidence_artifact(repo_root, evidence)` resolves (`check_engine.py:2036`). So the evidence citation is checked against the SAME `repo_root` that F-10 is about, and a citation resolvable in one tree but not the other flips the verdict. This is a second, independent reason E-01 cannot treat `--dir` as merely "where the file moves". Verify at execution that whichever tree you choose resolves the evidence path, and add a test for the case where the evidence is this plan's own newly-moved plan file, which is precisely the path whose location DIFFERS between lane and main. | `oc_runipd.process_backlog_close` (`:1471-1478`) passing `verdict.evidence`; `check_engine.evaluate_blocking_close` SATISFIED route (`:2036-2043`) calling `resolve_evidence_artifact(repo_root, evidence)` |
| F-12 | THE MULTI-CARRIER MEASUREMENT IS CONFIRMED EXACTLY, AND ITS SHAPE IS SLIGHTLY WORSE THAN F-5 SAYS. Re-measured independently at review round 2 across `.aw/records/plans/**/*.ipd.md` and `.aw/records/specs/**/*.spec.md`: 108 items carry at least one `From-Backlog` carrier and 21 of them carry MORE THAN ONE, matching F-5 exactly. The tail: `kjzlgw` 9, `o9inwt` 6, `kxkc04` 5, then `1ap48y`/`5wdoze`/`sjsoqq` at 4 each. F-5 names `kjzlgw` at 9 but reports the next tier as "3 each"; there are in fact three items at 4 or more that it does not name, so the multi-carrier population is more concentrated than the plan implies. This STRENGTHENS OQ-01's resolution rather than changing it, and is recorded so the executor can build the multi-carrier fixture from a real case rather than a synthetic pair. | measured at review round 2 by counting `- From-Backlog:` occurrences per id6 across both trees: 108 items with >=1 carrier, 21 with >1, top counts 9/6/5/4/4/4 |
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

AT EXECUTION (2026-09-16) THE ACTUAL FILE SET DIFFERED FROM THE DECLARATION, and the honest reconciliation is stated here rather than left to `--scope-reason` alone. What was declared: `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`.

WHAT WAS ACTUALLY CHANGED, with the reason for each:

| path | declared? | why |
|---|---|---|
| `agent_workflows/oc_runipd.py` | yes | the close path itself (E-01..E-04) |
| `agent_workflows/agy_runipd.py` | yes | host parity (E-05) |
| `agent_workflows/runner_shared.py` | NO | the two new helpers live here, NOT in a host. See below. |
| `agent_workflows/lane_containment.py` | NO | required, or every closing lane is preserved. See below. |
| `tests/test_runner_backlog_close_in_lane.py` (new) | NO | the plan's tests, in a new module rather than the two declared ones |
| `tests/test_runner_shared.py` | NO | its call-site census REFUSES an unnamed new `save_state` call site |
| `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py` | declared, UNMODIFIED | the tests went in a dedicated module instead |

`agent_workflows/runner_shared.py`, AND WHY THIS IS THE RIGHT CALL RATHER THAN A CONVENIENCE. Both hosts need `lane_executed_carrier_override` and `collect_lane_earned_paths`. Defining them in `oc_runipd` and importing them into `agy_runipd` would deepen exactly the coupling backlog `cnwy8g` tracks, and `test_the_oc_to_agy_import_count_did_not_increase` measures that count with an exact baseline and states the rule outright ("both hosts must reach it through `runner_shared`"). Putting them in the shared module keeps that count UNCHANGED, so no baseline was re-based and the guard was satisfied rather than edited. `collect_lane_earned_paths` needs the host's own `run_checked`, so each host keeps a one-line wrapper, which is the established `build_lane_outcome` shape.

`agent_workflows/lane_containment.py`, WHICH IS THE ONE GENUINELY UNFORESEEN EDIT. `aw backlog set` appends to the global history sidecar (`.aw/records/history.jsonl`), so a lane that closes a backlog item now holds that file; the lane teardown gate then REFUSED every such lane with "1 unknown IGNORED file(s): .aw/records/history.jsonl". Measured on the first end-to-end run. This was never reachable before because PLANS are excluded from the sidecar, so a finalize-only lane never wrote it. It is the same "refuses always" failure the adjacent generated-`INDEX` clause exists to prevent, and it is fixed the same way, scoped to that one exact relative path taken from `record_history.SIDECAR_RELPATH`. Left unfixed, this plan would trade a dirty main tree for a preserved worktree and branch per closing item.

`agent_workflows/check_engine.py` WAS **NOT** TOUCHED, which the plan's own under-scope note asked to be stated explicitly. The `--dir` redirect does reach two predicates there (F-10/F-11), and V-01 records the consequence: one `--dir` cannot be split from the caller, so the setter's move and its release gate necessarily share a tree. Rather than edit that high-blast-radius shared module (used by `aw check` and the pre-commit hook), the ELIGIBILITY decision was taken against main BEFORE the setter call, which is the alternative E-01 authorised. The residual coupling is filed as backlog `10pcd5` instead of being fixed silently here.

- Over-scope: `runner_shared.py`, `lane_containment.py` and `tests/test_runner_shared.py` are outside the declaration, each for a reason given above; none broadens what this plan DOES, and each is the minimum needed to make the declared change work and stay measurable.
- UNDER-SCOPE, ADDED AT REVIEW ROUND 2: `agent_workflows/check_engine.py` is NOT declared, and F-10/F-11 show the `--dir` redirect reaches two predicates that live there (`evaluate_blocking_close`'s carrier scan and its evidence resolution). If E-01 achieves the correct tree split WITHOUT touching that module, which is the expected and preferred outcome, the omission is right and those functions must be left alone. If it turns out the two `repo_root` uses cannot be separated from the caller, then `check_engine.py` MUST be added in the same pass, and a change there is high-blast-radius shared code used by `aw check` and the pre-commit hook as well as the runner. State which case you hit; do not edit it silently.
- NO INTENT COLLISION, VERIFIED AT REVIEW, which distinguishes this plan from Orders 01 and 02. The three approved `Blocks-Release: next` plans that contradict those two (`fujm0y`, `51vw4y`, `3i0aaz`) mention `process_backlog_close`, `commit_backlog_close` and the backlog close ZERO times between them. Two of them DO declare `oc_runipd.py`/`agy_runipd.py` in their `Scope-Paths`, but that is ordinary file overlap in different regions, which the runner's worktree isolation and merge-and-revalidate gate already handle; it is not a contradictory instruction. So this plan is independently approvable and executable. NOTE THE QUESTION NUMBER MOVED: that collision was the orchestrator's OQ-03 when this line was written, was renumbered to its OQ-02, and is now RESOLVED to the path split, so it constrains nothing here either way. This plan was never affected.
- Under-scope: this plan does not remove the `commit_backlog_close` helper, because the non-isolated path still needs it. If review wants isolation to be mandatory, that is a separate decision and a separate plan.

## Required tests / validation

- The cross-item regression of E-05: three isolated items, item 1 closes a backlog item, items 2 and 3 run, MAIN clean after item 1.
- A test proving the backlog move is IN the merge: inspect the merge's `--name-status` and see the item's rename, and confirm no separate close commit exists on main.
- A test proving a FAILED integration leaves the backlog item unclosed and still `graduated`, with the lane preserved. This is the property the maintainer asked for explicitly: the move lands if and only if the merge lands.
- A multi-carrier test per OQ-01's answer, proving an item with a sibling carrier that is not yet executed is NOT closed. BUILD THE FIXTURE FROM A REAL SHAPE (F-12): 21 of 108 carried items have more than one carrier, and the tail runs 9, 6, 5, then three at 4, so a two-carrier synthetic pair is the easiest case rather than a representative one. Use at least a three-carrier shape.
- A RELEASE-GATE TEST, which is the property F-10 shows is at risk and which nothing else here covers: an item carrying `- Blocks-Release:` whose only candidate carrier is this plan's own file must reach the SAME verdict it would reach against main, regardless of the lane. Assert the verdict, not merely that the run completed.
- The non-isolated path unchanged, asserted rather than assumed: paste a `--no-isolate-worktree` run whose close still moves and still commits via `commit_backlog_close`.
- Both hosts. Full suite run bare (`python3 -m pytest`), with the failure set diffed against a baseline captured from the SAME commit before any edit; paste both counts and the FAILED-set diff. Do not state a baseline from memory: sibling reviews in this Set each found a plan's claimed baseline wrong.

## Spec / documentation sync

- No spec is expected to change: `bkclose (zhr6mc)` introduced the close and this plan moves WHERE it happens, not WHETHER. VERIFIED AT REVIEW rather than left as a pre-execution chore: the specs tree contains NO requirement that fixes the backlog close to the main checkout (grepped for `zhr6mc`, `backlog_close`, and close-plus-main phrasings across `.aw/records/specs/`; no hit binds the close to a tree). Re-check cheaply at execution in case a spec landed since, but treat this as settled rather than an open risk. If one does appear, amend it in this plan and add the spec file to `Scope-Paths` first.
  RE-CHECKED AT EXECUTION (2026-09-16) as instructed, and it holds: NO spec was amended and none needed to be. No `.spec.md` file is in this change's diff.
- Update the comment at `oc_runipd.py:6859-6862`, which currently states the reasoning F-3 disproves.
  DONE. That comment now records that this site serves the NON-ISOLATED path only, states why the "wait until it is genuinely executed on main" reasoning does not survive (a merge is atomic, so riding it gets the same property without touching main), and explains why the guard keys on the close RECORD rather than on `wt_handle` (a successful teardown sets `wt_handle` to None above, so it would no longer distinguish the two paths). The agy twin carries the matching comment.

## Open questions

### OQ-01: Evaluate close eligibility in main before the merge, or in the lane?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-13 by the maintainer: option (a), EVALUATE IN MAIN BEFORE THE MERGE and PERFORM THE MOVE IN THE LANE. So E-03 splits decision from action deliberately. The reason this is the right split, and not merely the cautious one: eligibility asks whether ALL carriers of the item prove the work, which is a claim about several plans, and carrier discovery scans the FILESYSTEM (F-6), so the lane's view genuinely differs from main's (in the lane THIS plan is already `executed/` while siblings show their main state). With 20 of 107 carried items having more than one carrier (F-5), evaluating in the lane could close an item whose sibling carrier has not run. This is the SAME principle Order 04 rests on: a worker may commit facts about its own item, but a claim about several plans belongs to the coordinator. The `earned_paths` gate stays on the main-side evaluation where it already lives.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste MAIN's `git status --porcelain` immediately after an isolated item that closed a backlog item, showing it EMPTY. Paste the merge commit's `--name-status` showing the backlog item's move inside it.
  - NAME THE TREE THE CLOSE-LEGITIMACY GATE RAN AGAINST, and prove it (F-10). State in the evidence which tree `evaluate_blocking_close` evaluated (main or the lane) and paste the code comment recording that choice. Then paste the DISCRIMINATING case: a RELEASE-GATED item (one carrying `- Blocks-Release:`) whose only would-be carrier is THIS plan's own file, which sits in `executed/` in the lane and still in `pending/` in main. The two trees give different verdicts there, so this is the case that proves which tree was used. An implementation that closes it because the LANE view found a carrier has widened a release gate and FAILS this item, even with main's status empty and the merge correct.
  - PROVE THE EVIDENCE PATH RESOLVES IN THAT TREE (F-11). Paste the `verdict.evidence` string actually passed to the setter and show `resolve_evidence_artifact` resolving it in the chosen tree. If the evidence is this plan's own plan path, say which location it carried, since that path differs between lane and main.
  - Observed evidence: produced by running the REAL `oc_runipd.execute_item` path against a live git repo with an isolated lane (harness `.aw/state/scratch-9iq461/v_evidence.py`, full transcript at `.aw/state/lane-submissions/run-20260916T182835Z-1650244/04-9iq461/attempt-1/v-evidence.txt`), plus `tests/test_runner_backlog_close_in_lane.py` (22 passed).

    MAIN's `git status --porcelain -uall` DURING the turn, and AFTER the whole item:

    ```text
    --- MAIN `git status --porcelain` DURING the turn ---
    ''
    --- MAIN `git status --porcelain` AFTER the whole item ---
    ''
    ```

    The item's move IS INSIDE THE MERGED RANGE (`git diff --name-status <before>..HEAD`), alongside the plan transition and the agent's own file:

    ```text
    A	.aw/records/backlog/done/20260913-demo-01-bbbbbb-demo-item.backlog.md
    D	.aw/records/backlog/graduated/20260913-demo-01-bbbbbb-demo-item.backlog.md
    R092	.aw/records/plans/pending/20260913-demo-01-aaaaaa-demo.ipd.md	.aw/records/plans/executed/20260913-demo-01-aaaaaa-demo.ipd.md
    A	src/aaaaaa.txt
    ```

    The recorded verdict, including the new `wrote_in` field that names the tree the write happened in:

    ```json
    {
      "item": "bbbbbb", "closed": true, "rule": "ipd",
      "reason": "every IPD carrier is executed and this run executed .aw/records/plans/executed/20260913-demo-01-aaaaaa-demo.ipd.md",
      "evidence": ".aw/records/plans/executed/20260913-demo-01-aaaaaa-demo.ipd.md",
      "wrote_in": "lane", "commit": "458d0b0a0b141ab4289b373c0268ca5b2b7b7bd5"
    }
    ```

    THE TREE THE CLOSE-LEGITIMACY GATE RAN AGAINST IS **THE LANE**, and the honest reason is that ONE `--dir` CANNOT BE SPLIT. `backlog.run_set` derives both the destination root and `evaluate_blocking_close`'s `repo_root` from the same `resolve_verb_repo_root(args.dir)`, so the setter's move and its gate necessarily share a tree. Measured at the call:

    ```text
    --dir passed to the setter     : LANE
    evidence cited                 : .aw/records/plans/executed/20260913-demo-01-aaaaaa-demo.ipd.md
    evidence resolves in gate tree  : True
    evidence resolves in main       : False
    Blocks-Release preserved on the closed item : True
    ```

    SO THE PLAN'S PREFERRED ANSWER (gate on main) WAS NOT ACHIEVABLE WITHOUT EDITING `check_engine`/`backlog`, and per the plan's own scope check the correct response was to NOT edit that shared module silently. What was done instead is exactly the split E-01 authorised as the alternative: **the ELIGIBILITY DECISION is taken against MAIN** (E-03/V-03, `evaluate_backlog_close(repo, ...)` with `repo` never `write_repo`), while the setter's move plus its own gate run in the lane. The choice is recorded in a comment on `close_backlog_item`, as required:

    ```text
    `--dir` IS NOT MERELY "WHERE THE FILE MOVES" (dirtygates-03 `9iq461` F-10/F-11). Because the
    gated route runs `check_engine.evaluate_blocking_close`, this ONE argument also chooses the tree
    that predicate scans for release-gate carriers ... and the tree its `--evidence` citation is
    resolved against ... `backlog.run_set` derives both from the same `resolve_verb_repo_root(args.dir)`,
    so THE TWO CANNOT BE SPLIT FROM HERE: one `--dir` is one tree for the move AND the gate. That is why
    `process_backlog_close` performs the MOVE in the lane but takes the ELIGIBILITY decision against main
    BEFORE calling this, and why the evidence it cites is a path that resolves in the lane.
    ```

    THE DISCRIMINATING RELEASE-GATE CASE, MEASURED, AND IT CORRECTS F-10's PREMISE. The item carries `- Blocks-Release: next` and its only candidate carrier is this plan's own file (`executed/` in the lane, `pending/` in main):

    ```text
      evidence=main's pending path    legitimate=True  path=SATISFIED resolvable=True
      evidence=lane's executed path   legitimate=False path=None     resolvable=False
      with NO evidence at all       : legitimate=False severity=error
      reason: backlog item carries Blocks-Release 'next'; closing it `done` would silently drop that release gate
    ```

    F-10 PREDICTED THE LANE VIEW WOULD BE THE **PERMISSIVE** ONE VIA THE HANDOFF ARM. That is NOT what happens, and the difference matters: `find_from_backlog_artifacts` keys on the `- From-Backlog:` FIELD, not on the lifecycle bucket, so it finds the carrier in BOTH trees and the HANDOFF verdict is identical either way (here HANDOFF cannot fire at all, because the carrier does not itself carry `Blocks-Release`). What actually differs between the trees is only whether the **evidence path resolves**, i.e. the SATISFIED arm. So the gate is NOT widened by the lane: it is if anything STRICTER there, and the fail-closed arm remains reachable (third line above, asserted by `TheReleaseGateIsNotWidened::test_a_release_gated_item_with_NO_carrier_link_is_still_refused`). The gate field also survives the close (`Blocks-Release preserved: True`).
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste `git log --oneline` for the item's window showing NO separate "closed by aw oc run" commit on main for the isolated path, and paste a non-isolated run showing its close still commits.
  - Observed evidence: `git log --oneline` for the isolated item's window:

    ```text
    458d0b0 closed by aw oc run: IPD aaaaaa executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260913-demo-01-aaaaaa-demo.ipd.md); evidence .aw/records/plans/executed/20260913-demo-01-aaaaaa-demo.ipd.md
    579118c lifecycle(aaaaaa): finalize aaaaaa -> executed
    b990372 demo(aaaaaa): create the file
    ```

    READ THAT PRECISELY, BECAUSE THE DISTINCTION IS THE WHOLE OF E-02. A close commit IS present in the window and MUST be: it is what carries the move into the merge. What E-02 removes is a commit **authored on main**, and the proof is the commit's parentage:

    ```text
    close commits in window     : 1
    close commit parent subject : 'lifecycle(aaaaaa): finalize aaaaaa -> executed'
      -> parent is the LANE's finalize commit, so the close was authored IN THE LANE
    ```

    Had the driver committed on main after the merge (the pre-fix behavior), the close would be main's tip with the MERGE RESULT as its parent. Instead it sits directly on the lane's finalize commit, i.e. it was made on the lane branch and arrived by fast-forward. Pinned by `TheCloseHappensInTheLane::test_main_stays_clean_and_the_move_rides_the_merge`, which asserts exactly this parentage.

    THE NON-ISOLATED PATH STILL COMMITS, asserted rather than assumed (`--no-isolate-worktree`):

    ```text
    --- NON-ISOLATED (`--no-isolate-worktree`): still moves AND still commits ---
      ✓ IPD aaaaaa finalized -> executed/ and integrated to main (in-place (no isolation))
      ✓ backlog item bbbbbb closed done (evidence .aw/records/plans/executed/20260913-demo-01-aaaaaa-demo.ipd.md)
      wrote_in : main
      closed   : True
      commit   : 4a4cd904197649b7a17d33256ba5cc31e7bc5912   <- committed via commit_backlog_close
      item     : done
      backlog tree porcelain: ''
    ```

    So `commit_backlog_close` is retained and still reached (the plan's under-scope note is honored), and that path leaves its tree clean exactly as before.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste a multi-carrier test result showing an item with an UNEXECUTED sibling carrier is NOT closed, with the recorded reason. Paste a case proving the `earned_paths` gate still refuses a close the run did not earn. Prove the evaluation ran against MAIN (not the lane) by asserting on a fixture where the two views differ: the lane has this plan executed, main does not yet, and the verdict must be computed from main's view.
  - MANDATORY POSITIVE CASE (F-7), because every negative case above is also satisfied by a close path that refuses UNCONDITIONALLY: paste an eligible single-carrier item actually reaching `done` through the merge, with the item file's new path shown in the merge's `--name-status`. State which option E-03 took for `earned_paths` (compute in the lane, or resolve lane commits by SHA from main) and paste the non-empty earned set that proves the gate had real input rather than an empty one. A close-path change whose only evidence is refusals is indistinguishable from a broken one.
  - Observed evidence: THE MULTI-CARRIER REFUSAL, on a THREE-carrier shape per F-12 (the real tail is 9/6/5/4/4/4, so a pair would be the easiest case rather than a representative one). Two sibling carriers unexecuted, the run's own plan executed:

    ```text
    --- THREE-CARRIER item, two siblings unexecuted (F-12 shape) ---
    item status   : executed
    closed        : False
    reason        : IPD carrier(s) not executed: .aw/records/plans/pending/20260913-demo-02-cccccc-demo.ipd.md, .aw/records/plans/pending/20260913-demo-03-dddddd-demo.ipd.md
    item on disk  : graduated
    siblings named: True, True
    ```

    The ITEM STILL EXECUTED while the backlog item stayed `graduated`, which is the intended asymmetry: the run's work landed, the Set-level claim did not.

    THE EVALUATION RAN AGAINST MAIN, proved on a fixture where the two views DIFFER. In the lane this plan's file is in `executed/`; in main it is still `pending/`. The verdict is computed from main's carrier view, with the lane contributing exactly ONE fact (its own plan is executed) via the new `executed_overrides` mapping, and NO override for any sibling:

    ```text
    main's view, with the lane's own-plan fact supplied -> close=False
    reason names the unexecuted SIBLING, i.e. main's bucket for it was read, not the lane's
    ```

    (`EligibilityIsDecidedInMain::test_the_verdict_is_main_s_view_not_the_lane_s_permissive_one`, plus `test_the_override_is_limited_to_the_callers_own_plan`, which STRUCTURALLY asserts via AST that the helper's only non-empty return is the single own-plan mapping, so it cannot later widen into a general "treat pending as executed" switch.)

    THE EARNED GATE STILL REFUSES A CLOSE THE RUN DID NOT EARN:

    ```text
    close=False  reason=this run executed none of its carriers, so the close was not earned (all carriers were already executed before this run)
    ```

    THE MANDATORY POSITIVE CASE: an eligible single-carrier item ACTUALLY REACHING `done` through the merge, with a NON-EMPTY earned set:

    ```text
    --- POSITIVE CASE: an eligible single-carrier item REACHES done via the merge ---
    closed        : True
    reason        : every IPD carrier is executed and this run executed .aw/records/plans/executed/20260913-demo-01-aaaaaa-demo.ipd.md
    item on disk  : done
    EARNED SET (non-empty is the discriminator vs a starved gate):
        .aw/records/plans/executed/20260913-demo-01-aaaaaa-demo.ipd.md
        src/aaaaaa.txt
    --- the item's new path inside the merge ---
    A	.aw/records/backlog/done/20260913-demo-01-bbbbbb-demo-item.backlog.md
    D	.aw/records/backlog/graduated/20260913-demo-01-bbbbbb-demo-item.backlog.md
    R092	.aw/records/plans/pending/20260913-demo-01-aaaaaa-demo.ipd.md	.aw/records/plans/executed/20260913-demo-01-aaaaaa-demo.ipd.md
    A	src/aaaaaa.txt
    ```

    WHICH `earned_paths` OPTION WAS TAKEN, AND WHY NEITHER OF F-7's TWO WAS RIGHT AS STATED. F-7 offered (a) compute in the lane, or (b) resolve lane commits by SHA from main, on the premise that the diff would fail or return nothing with `cwd=main`. MEASURED IN A SCRATCH REPO, THAT PREMISE IS WRONG: a linked worktree shares the object database and refs with its parent, so `git diff <sha>..<sha>` over lane commits resolves IDENTICALLY from either cwd (both printed the same path, rc=0). Option (a) would have been a no-op.

    THE REAL DEFECT WAS THE **RANGE**, not the cwd: `collect_earned_paths` diffs the attempt's `starting_head..ending_head`, and both are `git_head(repo)` -- MAIN's HEAD sampled around the turn -- which for an isolated turn does not move, making the range `X..X` and therefore EMPTY. Measured:

    ```text
    the attempt's OWN recorded range (main HEAD..main HEAD)  -> (empty), rc=0
    the lane range by BRANCH NAME, cwd=main                  -> executed/plan.md, item-done.md, rc=0
    ```

    So the fix NAMES THE RANGE THAT HOLDS THE WORK: a new `runner_shared.collect_lane_earned_paths` diffs the lane's `base_commit..branch`, read with `cwd=repo`. F-7's CONCLUSION was nevertheless correct and load-bearing -- an empty earned set would have made the gate refuse every close SILENTLY forever, since the earned gate can only withhold -- which is exactly why V-03 demanded this positive case. Both halves are pinned by `TheEarnedPathsRangeIsTheLaneBranch`, including an explicit assertion that the attempt's own range is empty. The corrected diagnosis is filed as backlog `h5a3ba` so the stale finding does not mislead a later reader.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste a run summary containing the `Backlog items left open` block with at least one reason, proving the reporting survived. Paste a forced-failure case showing a recorded refusal rather than a traceback.
  - Observed evidence: the `Backlog items left open` block, rendered by the shipped `render_unclosed_report`, WITH its reason:

    ```text
    --- Backlog items left open ---
      - bbbbbb: IPD carrier(s) not executed: x.ipd.md, y.ipd.md
      (this run's own items only; `aw attention` owns the cross-tree view)
    ```

    A FORCED SETTER FAILURE is RECORDED as the reason and the item is left ALONE, with no traceback escaping:

    ```text
    --- a FORCED setter failure is RECORDED, not raised ---
    closed=False  reason=setter refused the close: induced setter failure
    item left at: graduated  (no traceback escaped)
    ```

    A FORCED EVALUATION failure likewise records rather than raises, so a broken predicate cannot fail the item:

    ```json
    {
      "item": "bbbbbb",
      "closed": false,
      "reason": "close evaluation failed: induced evaluation failure"
    }
    ```

    ONE REPORTING HAZARD WAS FOUND AND FIXED WHILE DOING THIS, and it is the reason both post-merge call sites are now guarded. Moving the close earlier means the item can already be `done` when the pre-existing post-merge site runs; a second evaluation would answer `item is already done`, i.e. `close=False`, and OVERWRITE the success record with a refusal, so a CORRECT close would be reported to the operator as "left open". The guard `if not (item.get("backlog_close") or {}).get("closed"):` prevents that in both hosts, and `BothHostsBehaveIdentically::test_the_post_merge_close_is_guarded_against_overwriting_a_success` fails without it (verified: it is one of the four that fail when the change is reverted in place).
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: paste the three-item regression output showing items 2 and 3 executed and MAIN clean after item 1. Paste the equivalent for agy. Paste the bare full-suite counts before and after with the FAILED-set diff.
  - Observed evidence: THE THREE-ITEM REGRESSION, run through the real `execute_item` for each item in turn, sampling MAIN's porcelain after each:

    ```text
    ▶ IPD 01/3 aaaaaa  set=demo  action=execute  attempt 1
      ✓ isolated worktree aw/lane/aaaaaa at .../.aw/worktrees/aaaaaa
      ✓ backlog item bbbbbb closed done (evidence .aw/records/plans/executed/20260913-demo-01-aaaaaa-demo.ipd.md)
      ✓ IPD aaaaaa finalized -> executed/ and integrated to main (fast-forward integrated to main)
    ✓ IPD 01/3 aaaaaa (execute) -> executed  (exit 0)
      after aaaaaa: status=executed  main porcelain=''
    ▶ IPD 02/3 cccccc ...
    ✓ IPD 02/3 cccccc (execute) -> executed  (exit 0)
      after cccccc: status=executed  main porcelain=''
    ▶ IPD 03/3 dddddd ...
    ✓ IPD 03/3 dddddd (execute) -> executed  (exit 0)
      after dddddd: status=executed  main porcelain=''
      item bbbbbb            : done
      item 1 wrote_in        : lane
    ```

    Items 2 and 3 both executed and MAIN was clean after item 1, which is the exact shape of run `run-20260913T031148Z-1722898` that lost 23 of 41 items.

    HONEST NOTE ON WHAT THAT ALONE PROVES, measured by REVERTING the change in place and re-running rather than assumed: the cross-item assertions PASS EVEN PRE-FIX. The root cause of the dirty tree was the un-paired move, already fixed separately by commit `c53849e5` (`git mv`), so a post-merge close now commits both halves and leaves main clean too. What this Set removes is the remaining mid-run WRITE, which is why the discriminating assertion is `wrote_in == "lane"`. With the fix reverted, FOUR of the new tests fail:

    ```text
    FAILED tests/test_runner_backlog_close_in_lane.py::TheCloseHappensInTheLane::test_main_stays_clean_and_the_move_rides_the_merge
    FAILED tests/test_runner_backlog_close_in_lane.py::ThreeItemsAndMainStaysClean::test_item_one_closing_a_backlog_item_does_not_block_items_two_and_three
    FAILED tests/test_runner_backlog_close_in_lane.py::BothHostsBehaveIdentically::test_both_drivers_close_in_the_lane_before_integrating
    FAILED tests/test_runner_backlog_close_in_lane.py::BothHostsBehaveIdentically::test_the_post_merge_close_is_guarded_against_overwriting_a_success
    4 failed, 13 passed
    ```

    So the new tests DO detect the defect, which is the property E-05 exists for.

    THE agy HOST, exercised end to end rather than asserted about (its turn signature and verifier key differ, so a shared fake would not have caught a divergence):

    ```text
    tests/test_runner_backlog_close_in_lane.py::AgyHostClosesInTheLaneToo::test_agy_closes_in_the_lane_and_leaves_main_clean PASSED [ 50%]
    tests/test_runner_backlog_close_in_lane.py::AgyHostClosesInTheLaneToo::test_agy_three_items_and_main_stays_clean PASSED [100%]
    ============================== 2 passed in 5.73s ===============================
    ```

    BARE FULL-SUITE COUNTS, BEFORE AND AFTER, from the SAME commit (`5f0bb8d8`), run as `python3 -m pytest` with no added flags:

    ```text
    BEFORE : 7328 passed, 3 skipped, 2 xfailed in 79.32s (0:01:19)   EXIT=0
    AFTER  : 7350 passed, 3 skipped, 2 xfailed in 82.29s (0:01:22)   EXIT=0
    ```

    FAILED-SET DIFF: **empty in both directions** (zero failures before, zero after). The delta is +22 passed, which is exactly the new `tests/test_runner_backlog_close_in_lane.py` module.

    ONE MEASUREMENT CAVEAT, STATED RATHER THAN GLOSSED, because a naive baseline here is wrong. This turn runs with `AW_EXECUTION_ROLE=worker` exported, and 21 tests legitimately fail under that variable because they exercise `aw ipd begin`/`finalize`, which the worker-role gate REFUSES by design (`AW-LIFECYCLE-ROLE-001`). That is the guard working, not a regression, and it is unrelated to this plan. Both runs above were therefore taken with `env -u AW_EXECUTION_ROLE`, identically, so the comparison is apples to apples. The 21-failure worker-role baseline is preserved alongside at `suite-baseline.txt` for audit.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit only files this plan changed, path-scoped, never `git add -A`, never push. Paste actual runner output for every test claim. The declared scope is `Scope-Paths`; an out-of-scope edit must be made and then JUSTIFIED with `--scope-reason` at finalize, and a declared-but-unmodified path acknowledged with `--scope-ack`.

NOTHING IN THIS PLAN IS GATED. CORRECTED AT REVIEW ROUND 2: this contract previously read "OQ-01 is BLOCKING and must be answered before E-03 is written", which was true when written and is now false. OQ-01 is RESOLVED to option (a): EVALUATE ELIGIBILITY IN MAIN, PERFORM THE MOVE IN THE LANE. Proceed on that basis rather than waiting.

THREE WAYS TO GET THIS WRONG, each measured or traced rather than imagined. FIRST, do NOT change the `--status done` SPELLING while changing `--dir`: the positional form skips `evaluate_blocking_close` entirely, so the runner's close would stop being gated (F-8, and the function's own docstring records this as measured). SECOND, do NOT assume `--dir` only chooses where the file moves: it also re-points the close-legitimacy gate's carrier scan and its evidence resolution, and the lane view is the PERMISSIVE one (F-10, F-11). THIRD, do NOT accept a green E-05 as proof the close still works: a permanently-refusing close satisfies every assertion in it (F-7), which is why V-03 demands a POSITIVE close.

Post-gate lifecycle move: this plan reaches `executed/` only when every V-item above carries pasted evidence and `aw ipd lint --phase pre-transition` reports conforming.
