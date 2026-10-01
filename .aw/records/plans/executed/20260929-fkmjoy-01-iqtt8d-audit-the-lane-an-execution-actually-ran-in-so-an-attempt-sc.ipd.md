# IPD: Audit the lane an execution actually ran in, so an attempt-scoped or diverged lane gets a scope advisory instead of silence

- Date: 2026-09-29
- Kind: child
- Concern: `check.scope-drift` reports NOTHING for an in-flight execution whose lane HEAD does not descend from its receipt's frozen `base_head`, so such an execution has no declared-scope feedback between begin and finalize. Measured at authoring on the live checkout, the dominant real-world cause is NOT an honest base disagreement: `check_engine._plan_execution_tree` resolves the lane by passing the plan's `id6` straight to `worktree_lease.inspect_lane`, which reconstructs the CANONICAL branch `aw/lane/<id6>`, while `allocate_worktree` may have attempt-scoped the execution into `aw/lane/<id6>_attemptN`. The rule then measures the WRONG TREE (an abandoned sibling lane) and falls silent on an execution whose real lane is perfectly auditable. NOTE `check.scope-drift` is registered `error` and DOES gate (verified at review), so this is a gating rule that under-reports, not a best-effort advisory that stays quiet.
- Scope: Make the gating rule resolve the lane an execution ACTUALLY ran in, and say so when it cannot. Add a candidate-enumerating lane resolver to `worktree_lease` that finds every lane branch belonging to one `id6` (canonical plus `_attemptN`) and selects the one whose own base is consistent with a given receipt base; consume it from `check_engine._plan_execution_tree`; and when no candidate is consistent, emit a distinct NON-GATING advisory naming the execution whose scope could not be audited, rather than silently reporting nothing. EXCLUDES re-issuing or re-freezing the receipt from the runner (rejected, see F-7), EXCLUDES diffing across a genuine fork by substituting the lane's own base for the receipt's (rejected, see F-6), and EXCLUDES reintroducing any main-checkout comparison (settled by maintainer ruling, see F-8).
- Scope-Paths: agent_workflows/worktree_lease.py, agent_workflows/check_engine.py, tests/test_scope_drift_lane_resolution.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: fkmjoy
- Blocks-Release: next
- Set: fkmjoy
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: iqtt8d

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: iqtt8d verified (set fkmjoy, attempt 1).
- 2026-09-30 approved (aw set): status set to approved

- 2026-09-30 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001 through PR-006, all FIXED in place. Reviewed at HEAD `8c95fa8b` in an isolated lane; typed record at `.aw/records/reviews/20260929-fkmjoy-01-iqtt8d-audit-the-lane-an-execution-actually-ran-in-so-an-attempt-sc.review.md`. `aw ipd lint --phase author` reported clean with ZERO findings before semantic review and `--phase review-finalize` conforms after, so nothing found was structural; the plan also entered with no stale `Scope-Paths` and all three deferred-row carriers already filed and resolvable.
  TEN OF ELEVEN FINDINGS RE-DERIVED BY RUNNING CODE AND HELD. F-2, the central claim, is exact: in the canonical lane `git merge-base --is-ancestor d69ed2a8 HEAD` exits 1 while in `_attempt2` it exits 0, and `_plan_execution_tree(root, "om3rzi", "d69ed2a8b17f")` returns `None` while the attempt id returns the real lane. Both `om3rzi` lanes still HOLD WORK with the bases F-1 names. The anchored pattern accepts the canonical and attempt forms and rejects the live review-sweep lane. `drift_exit_code` returns 0 for `info` and 1 for `warning`/`error`, so E-04's severity choice is verified. Three multi-lane `id6`s are live (`om3rzi`, `vxqtqm`, `19lmbe`).
  ONE HIGH CHANGES THE REVIEW QUESTION. PR-001: `check.scope-drift` is registered `RuleSpec("error", ..., "I-01")`, gates through `drift_exit_code`, and composes into `check_commit_invariants`, yet the plan calls it an "advisory" and "local best-effort feedback" throughout. So E-02 and E-03 WIDEN A GATE: an execution silent today can begin FAILING a check. The work is right and was NOT narrowed; the description was corrected, and the risk was measured rather than assumed. Blast radius is ZERO on this checkout (both live receipts already resolve their single canonical candidate; the three sibling-lane id6s hold no receipt), recorded as F-12 and F-13, with new E-07/V-07 measuring findings and `aw check` exit codes before and after and requiring a true-positive judgement on any new `error`, plus a gate directive to STOP rather than narrow the rule to suppress one.
  ONE FURTHER HIGH AND THREE MEASUREMENT CORRECTIONS. PR-002: E-02's use of `lane_id_from_branch` to "recover each lane id" cannot GROUP siblings (it returns `om3rzi_attempt2`, and grouping the 20 live branches by it yields zero multi-lane groups), so the step was split: the anchored match groups, that function supplies the inspect id. PR-003: F-4's 272-path figure belongs to `d69ed2a8..aw/lane/om3rzi` (receipt base against the WRONG lane, i.e. the guard-removal case), not to substituting the lane's own base, which gives 7; re-attributed, with F-6 now carrying the whole rejection argument. PR-004: F-3's zero-findings conclusion holds but two receipts are now live and reachable, so the better reason is that both already resolve their canonical lane. PR-005: E-01's owner-record census column is unobtainable from a lane worktree (`.aw/worktrees/` is absent there), which is F-11 observed where it bites and is the empirical vindication of E-02's git-refs-only design. PR-006: the gate lacked conditional runner-versus-executor finalize ownership.
  BOTH OPEN QUESTIONS DELIBERATELY LEFT FOR THE MAINTAINER (D-4): OQ-01 needs a residual-rate datum that only shipping E-03 produces, OQ-02 is a receipt-schema design direction the plan rightly says would supersede rather than amend it, both are `Blocking: no`, and both already carry a complete filed carrier (`p4hmpz`, `m94le9`).

- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `fkmjoy`. `- Blocks-Release: next` and `- Work-Kind: bug` are INHERITED from the item and both are carried unchanged. THE ITEM'S SYMPTOM REPRODUCES AND ITS ROOT-CAUSE ATTRIBUTION IS CORRECTED, and that correction is the substance of this plan. The item reasons that a lane and a receipt can honestly disagree (true, and `allocate_worktree`'s docstring says so), and concludes the silence is "the safe answer to an unanswerable question". Measured on the live checkout at authoring (2026-09-29, main at `9504c522`), the question is usually ANSWERABLE and the advisory is asking it of the wrong tree. Lane `aw/lane/om3rzi` and lane `aw/lane/om3rzi_attempt2` both exist, both HOLD WORK, and the owner records under `.aw/worktrees/.owners/` record that the SECOND is the real execution (`"disposition": "attempt-scoped"`, `"base_commit": "d69ed2a8..."`) while the first was a prior attempt cut from the older `cdfddf2e...`. `_plan_execution_tree(repo, "om3rzi", "d69ed2a8...")` returns `None`, because `inspect_lane("om3rzi")` reconstructs the canonical branch and reaches the ABANDONED lane, whose base predates the receipt. Yet `git merge-base --is-ancestor d69ed2a8 aw/lane/om3rzi_attempt2` exits 0: the real lane is FULLY AUDITABLE, and a `base..HEAD` diff there yields exactly 5 paths, which are exactly the paths that lane's single commit touched. So the advisory's silence here is a RESOLUTION defect, not an honest abstention, and it is reachable by the ordinary retry path rather than by anything exotic. THE ITEM'S THREE CANDIDATE DIRECTIONS ARE ALL ADDRESSED AND TWO ARE REJECTED ON EVIDENCE. Its direction (1), preferring the lane's own recorded base over the receipt's, is REJECTED: measured on the same divergent pair, `cdfddf2e..aw/lane/om3rzi` reports 272 paths where the lane's own work is 7, so substituting the lane base re-imports main's intervening commits and recreates the exact misattribution that plan `wmnmei` removed (F-6). Its direction (2), re-issuing the receipt when the runner attempt-scopes, is REJECTED as written: a fresh `begin` recaptures `base_head` at the CURRENT head, and `ipd_lifecycle.refreeze_receipt`'s own docstring records that this would make every path the item changed INVISIBLE to the finalize delta; `refreeze_receipt` deliberately KEEPS `base_head` for that reason (F-7). Its direction (3), a distinct "could not audit" advisory, is ADOPTED but narrowed: the maintainer declined that line for the NO-LANE case (`wmnmei` OQ-01), so this plan emits it ONLY for an execution that demonstrably has a lane holding work that no candidate can reconcile, which is the reading the item itself suggests may differ, and it is `info` severity so it cannot gate a commit (F-9, OQ-01). THE ITEM UNDERSTATES THE BLAST RADIUS IN ONE RESPECT AND OVERSTATES THE EVIDENCE IN ANOTHER. Understates: the same canonical-name assumption is the documented hazard `worktree_lease.lane_id_from_branch` exists to close (measured under `resumedupe txc9l1`), and `lane_branch_name`'s own docstring says callers "must NOT reconstruct this by hand from an id6, because allocation may attempt-scope the name"; `_plan_execution_tree` violates that instruction, so this is a known class of bug in a new place rather than a novel one (F-2). Overstates: the item's headline measurement cannot be re-verified now, because every one of the 24 begin receipts under `.aw/state/ipd-lifecycle/` belongs to a plan that has since reached a TERMINAL directory, and `check_engine._iter_type_files` excludes a terminal plan via `is_retired`, so `check_scope_drift` currently examines ZERO live receipts and returns zero findings on this checkout. The defect is therefore demonstrated CONSTRUCTIVELY and on the real divergent lane pair, not by a live finding count, and E-01 requires re-measuring rather than trusting these numbers (F-3). The plan is `to-review` and carries NO `- Readiness:` field; that absence is the correct unattested state.

## Goal

Make `check.scope-drift` measure the lane an execution actually ran in, so the ordinary retry path (an attempt-scoped lane) stops silencing the rule, and make a genuinely unauditable execution SAY SO at `info` severity instead of vanishing. Finalize remains the enforcement point for the two-way reconciliation, and no main-checkout comparison returns.

ONE CORRECTION TO HOW THIS PLAN DESCRIBES ITSELF, ADDED AT REVIEW AND LOAD-BEARING FOR THE RISK ASSESSMENT. This plan's prose calls `check.scope-drift` an "advisory" and "local best-effort feedback" throughout. IT IS NOT: it is registered `error` in `check_engine`'s rule registry with invariant `I-01`, so `artifact_core.drift_exit_code` returns 1 on it (verified at review), it composes into `check_commit_invariants`, and `aw check release-gates` runs as a fail-closed CI step. So E-02 and E-03 WIDEN A GATING RULE: an execution that is silent today can begin FAILING a check once its lane resolves. That is the intended and correct outcome, and it is not a reason to narrow the work, but it must be stated because it changes the review question from "is this feedback useful" to "is this gate safe to widen". The answer measured at review is yes on present evidence: of the two live receipts on this checkout both already resolve their canonical lane, and NEITHER of the three multi-lane id6s (`om3rzi`, `vxqtqm`, `19lmbe`) holds a receipt at all, so the immediate blast radius is zero findings. E-04's NEW rule is separately `info` and genuinely cannot gate.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure before changing anything

- [x] E-01 RE-MEASURE this plan's premise at execution HEAD rather than trusting the authoring numbers, because every one of them is a function of which lanes and receipts exist right now, and lanes are created and torn down continuously by concurrent runs. Produce four things. FIRST, the live receipt census: for every `*.receipt.json` under `ipd_lifecycle.receipt_dir`, the plan `id6`, whether a plan file carrying that `- Id:` is reachable from `check_engine._iter_type_files(repo, "plans")` at all, its disposition, whether `check_engine._receipt_is_live` accepts it, and whether `_plan_execution_tree` returns a tree. SECOND, the lane census: every branch matching `refs/heads/aw/lane/*`, with its `inspect_lane` state, `base_sha`, `commits_ahead` and `dirty`, plus the `disposition` and `base_commit` recorded in its owner record under `worktree_lease.OWNERS_SUBDIR` where one is readable. EXPECT THE OWNER RECORDS TO BE UNREADABLE IF YOU EXECUTE FROM A LANE, measured at review: `_owner_record_path` composes from the PASSED root (F-11), so from inside a lane worktree it resolves to `<lane>/.aw/worktrees/.owners/<lane>.json`, and that whole subtree does not exist there, so `read_lane_owner` returns `None` for every lane. That is NOT a drift to report and NOT a blocker: record "owner records unreadable from this root" and carry on, because `inspect_lane` still returns full `state`/`base_sha`/`commits_ahead` from git refs and the reflog (verified at review against `om3rzi_attempt2`: `state=HOLDS-WORK base_sha=d69ed2a8b17f ahead=1` with no owner record present). This is also the empirical case FOR E-02's design: the resolver must read git refs and must not depend on an owner record, which is exactly what F-11 constrains it to. THIRD, the explicit set of `id6` values holding MORE THAN ONE lane branch (canonical plus any `_attemptN`), since that is the population this plan repairs. FOURTH, the actual output of `check_engine.check_scope_drift(repo)`. If the divergent pair this plan cites at F-1 is gone, do NOT abandon the work: reproduce the same shape CONSTRUCTIVELY in a throwaway repo (F-3 explains why a constructed reproduction is the primary evidence here) and say plainly in the finalize report that the live pair had been reclaimed.
  - Depends on: none
  - Expected outcome: a pasted four-part census, plus an explicit statement of whether F-1's divergent lane pair, F-3's zero-live-receipts condition, and F-4's 272-versus-7 and 5-path numbers still hold, with any drift named rather than absorbed.
  - Execution state: performed

### Task group 2: give the resolver a way to find the lane that actually ran

- [x] E-02 ADD a candidate-enumerating lane resolver to `agent_workflows/worktree_lease.py` that answers "which lane did the execution for this `id6` actually run in, given the receipt base it was issued against". It must ENUMERATE candidates from git rather than reconstructing a name: list `refs/heads/aw/lane/*` (the same `for-each-ref` surface `memoize_worktrees` already uses), keep the branches whose lane portion is the target `id6` optionally followed by the attempt suffix `allocate_worktree` mints via `_attempt_scoped_lane_id`, and recover each candidate's LANE ID (the value to pass to `inspect_lane`) with the existing `lane_id_from_branch` inverse rather than a hand-built string.

  BE PRECISE ABOUT WHAT `lane_id_from_branch` DOES AND DOES NOT GIVE YOU, measured at review because the instruction as authored reads as though it groups siblings and it does not. `lane_id_from_branch("aw/lane/om3rzi_attempt2")` returns `'om3rzi_attempt2'`, NOT `'om3rzi'`: its docstring says so explicitly ("The colon is not recovered, and it does not need to be: only the branch identity matters for inspection"). So it is the right tool for the SECOND step (it yields the id `inspect_lane` must be given, which is the `resumedupe txc9l1` hazard it exists to close) and it CANNOT perform the FIRST step of deciding which branches belong to one `id6`. That grouping must come from the anchored match against the target `id6`. Do not group by `lane_id_from_branch`'s return value; measured at review, doing so yields zero groups because every attempt lane gets its own key.

  THE ANCHORED PATTERN VERIFIED AT REVIEW, so the executor inherits a tested shape rather than a description: `^aw/lane/<re.escape(id6)>(?:_attempt(\d+))?$` matches `aw/lane/om3rzi`, `aw/lane/om3rzi_attempt2` and `aw/lane/om3rzi_attempt12`, and correctly REJECTS `aw/lane/review-sweep-run-20260930T051707Z-2958432`, `aw/lane/om3rziX`, `aw/lane/Xom3rzi` and `aw/lane/om3rzi_attemptZ`. Both anchors are required: without `$` the trailing cases match, and without `^` the leading one does. Verify the anchoring before relying on it: an unanchored match would also capture the review-sweep lane `aw/lane/review-sweep-run-<...>`, which is a real branch on this checkout and belongs to no plan. For each candidate return its `LaneState` together with the receipt-consistency verdict, computed as `git merge-base --is-ancestor <receipt_base> <lane HEAD>` run IN the candidate. Return the candidates in a deterministic order (sort by attempt number, canonical first), and return an EMPTY result rather than raising when git cannot answer, because every caller here is best-effort feedback. This function must stay RUN-CONTEXT-FREE and stdlib-only, like everything else in this module: take no run directory and no item record (`inspect_lane`'s docstring pins that constraint and explains why), and add no package-level import.
  - Depends on: E-01
  - Expected outcome: a documented resolver in `worktree_lease` that, given `id6` and a receipt base, returns every lane branch belonging to that `id6` with its state and its receipt-consistency verdict; it names `aw/lane/<id6>_attemptN` as well as the canonical lane, excludes a foreign lane branch such as the review-sweep lane, and returns empty instead of raising when git is unavailable.
  - Execution state: performed

- [x] E-03 MAKE `check_engine._plan_execution_tree` consume the E-02 resolver instead of calling `inspect_lane(repo_root, plan_id)` directly, and SELECT among candidates by the receipt base rather than by name. The selection rule, which must be stated in the docstring because it is the correctness argument: prefer a candidate whose HEAD DESCENDS from the receipt base, since only such a candidate permits an honest `base..HEAD` diff; among several, prefer the one holding work over an empty one, then the highest attempt number, because attempt-scoping means a later attempt displaced an earlier one. Return `None` when no candidate descends from the receipt base, PRESERVING today's silent behavior for that case (E-04 is what gives that case a voice, and it must remain separable from this one). Do NOT change the ancestry test itself, and do NOT substitute a lane's own base for the receipt's: F-6 measures what that costs. Keep the existing whole-body exception guard and its stated fail-safe direction, and keep the function's signature and return type unchanged so every caller and the `check_scope_drift` body are untouched.
  - Depends on: E-02
  - Expected outcome: `_plan_execution_tree` returns the attempt-scoped lane for an execution whose receipt base descends into it (where it returned `None` before), still returns `None` when no candidate is consistent, and still returns `None` when there is no lane at all.
  - Execution state: performed

### Task group 3: give an unauditable execution a voice

- [x] E-04 ADD a distinct, NON-GATING advisory for an in-flight execution whose scope could not be audited, so the remaining honest-divergence case stops being silent. It must fire ONLY when all of the following hold, because a broader trigger would reintroduce the noise `wmnmei` removed and would contradict the maintainer's ruling on the no-lane case: the receipt is LIVE by `_receipt_is_live`; the plan declares a non-empty frozen `Scope-Paths`; at least one lane candidate for the `id6` EXISTS and HOLDS WORK; and no candidate's HEAD descends from the receipt base. Register it in `check_engine`'s rule registry at `info` severity so `artifact_core.drift_exit_code` cannot fail a gate on it (verify that claim against `drift_exit_code` rather than assuming it, and state the verification in the plan). The message must name the plan, the lane branches it found, and each one's recorded base, and must say the scope was NOT audited and that finalize remains the enforcement point. Emit AT MOST ONE finding per plan, matching the deliberate one-finding-per-plan collapse the neighbouring rule documents, and reuse `_summarize_paths` if any path list is rendered. Do NOT add this to any gating set and do NOT wire it into the opt-in pre-commit hook.
  - Depends on: E-03
  - Expected outcome: a new `info`-severity rule that fires for a live execution with a work-holding but irreconcilable lane, naming the lanes and their bases, that is silent for a plan with no lane and for a plan whose lane reconciles, and that provably cannot change any gate's exit code.
  - Execution state: performed

- [x] E-05 UPDATE the load-bearing docstrings so the next reader is not told the old contract, treating this as part of the change rather than as tidying, because these two docstrings are the repository's record of WHY the rule measures a lane at all. In `_plan_execution_tree`, keep the maintainer's ruling and the accepted-cost paragraph intact (they are still true and must not be softened), and correct the paragraph beginning "THE ANCESTRY CHECK IS NOT REDUNDANT", which currently cites `lc4unl` as a lane legitimately cut from a different commit and concludes "an unusable lane base reports NOTHING": state that the FIRST question is WHICH lane, that an attempt-scoped lane is resolved by the E-02 enumerator, and that only a genuinely irreconcilable lane now reaches the E-04 advisory. In `check_scope_drift`, correct the "WHICH TREE IS MEASURED IS PART OF THE RULE" paragraph the same way, preserving its measured 350-findings history verbatim. Add to `worktree_lease` a short note at the new resolver recording that `_plan_execution_tree` was the second measured instance of the reconstruct-a-branch-name-from-an-id6 hazard that `lane_id_from_branch` documents, so the pattern is visible in one place.
  - Depends on: E-04
  - Expected outcome: both docstrings describe the implemented behavior, retain every maintainer ruling and measured figure they already carry, and no longer assert that a lane whose base disagrees with the receipt is reported on not at all.
  - Execution state: performed

### Task group 4: keep it from regressing

- [x] E-07 MEASURE WHAT WIDENING THE GATE ACTUALLY COSTS ON THIS REPOSITORY, before and after, because F-12 establishes that `check.scope-drift` is `error`-severity and gating, so E-03 can convert silence into a FAILING check rather than into feedback. Record, on the real checkout: `check_scope_drift(repo)` findings BEFORE the change and AFTER; the exit code of `aw check` and `aw check all` before and after; and for every live receipt, whether `_plan_execution_tree` newly resolves a lane it previously did not. Then state whether any NEW `error` finding appeared and, for each, whether it names real out-of-scope work (a true positive worth gating on) or an artefact of resolution. IF A NEW GATING FINDING APPEARS THAT IS NOT A TRUE POSITIVE, STOP AND REPORT rather than shipping it: a false `error` fails CI for everyone, and the correct response is to narrow the selection rule or to reconsider severity, which is a decision for the maintainer and not an execution-time adjustment. Review measured the expected answer as ZERO new findings (F-13: the two live receipts each have exactly one lane candidate and already resolve it; the three multi-lane id6s hold no receipt), so a nonzero result is itself the signal to stop.
  - Depends on: E-03
  - Expected outcome: before/after findings counts and `aw check`/`aw check all` exit codes pasted, a per-receipt statement of any newly resolved lane, and an explicit true-positive judgement on every new `error` finding, or a STOP report.
  - Execution state: performed


- [x] E-06 ADD a behavioral regression test at `tests/test_scope_drift_lane_resolution.py` that drives real code against REAL git repositories built in `tmp_path` and asserts on real outputs. It must cover five cases, and the first is the one that must fail before E-03: (a) a plan whose execution ran in an ATTEMPT-SCOPED lane, asserting `check_scope_drift` reports the out-of-scope path that lane actually changed, and asserting the same scenario produces NO finding when the resolver selection is reverted, so the test is proven to be a guard rather than merely passing; (b) a plan whose canonical lane reconciles normally, asserting behavior is unchanged; (c) a plan with NO lane, asserting total silence, since that is the maintainer's ruled contract and E-04 must not break it; (d) a plan whose only lane holds work and is genuinely irreconcilable, asserting exactly one `info` finding that names the lane, and asserting via `artifact_core.drift_exit_code` that a findings list containing only it exits 0; (e) a foreign lane branch present in the same repo (use the review-sweep shape `aw/lane/review-sweep-run-X`), asserting it is never selected for any plan. Build each fixture with the same commands the runner uses (`git worktree add -b aw/lane/<name> <path> <base>`) so the reflog-derived `_lane_base_sha` path is genuinely exercised. Assert on OUTCOMES only: never read production source with `inspect`, `ast`, regex or substring search, never assert a caller count or a symbol census, and pin no line numbers (GUIDING_PRINCIPLES P16).
  - Depends on: E-05
  - Expected outcome: a new test file that passes, whose case (a) demonstrably FAILS against the pre-E-03 selection logic, whose case (c) pins the ruled no-lane silence, and whose case (d) proves the new advisory cannot change an exit code.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `worktree_lease` is deliberately STDLIB-ONLY and imports no other package module at module level; `lane_merged_into_target` and `LaneState.merged_into_target` both use a FUNCTION-LOCAL import of `runner_shared` and say why (that module imports this one, so a module-level import back would be circular). E-02 must respect this.
- `inspect_lane` is pinned RUN-CONTEXT-FREE: its docstring records that it takes no run directory and no item record, and that the spec `7ckptx` R5.5 retention inventory therefore cannot live in this module. A new resolver beside it inherits that constraint.
- Reconstructing a lane branch from an `id6` is an EXPLICITLY DOCUMENTED HAZARD. `lane_branch_name`'s docstring says callers "must NOT reconstruct this by hand from an id6, because allocation may attempt-scope the name ... Read `handle.branch` instead", and `lane_id_from_branch` exists because that mistake was measured under `resumedupe txc9l1`. This plan's defect is that same hazard in `check_engine`.
- The five lane states are exhaustive and `LANE_STALE` is mandatory rather than a refinement; the comment above them records the measured hole a four-state scheme left. A resolver must not collapse them.
- Lane owner records (`.aw/worktrees/.owners/<lane>.json`) carry `disposition` and `base_commit`, which is how the attempt-scoped lane is identifiable as the real execution at authoring time. NOTE the anchoring asymmetry: `_owner_record_path` composes from the PASSED root, so it resolves to a lane-local path when called with a lane worktree, whereas `ipd_lifecycle.receipt_dir` anchors on the checkout via `checkout_control_root`. A resolver must therefore not depend on an owner record being readable from an arbitrary cwd; git refs are the reliable surface, which is why E-02 enumerates them.
- `check_engine._iter_type_files` excludes a terminal plan through `is_retired`, so a receipt whose plan has been finalized is invisible to `check_scope_drift` regardless of the receipt's own liveness. That is why the live-finding count on this checkout is zero (F-3).
- The neighbouring rule collapses to ONE FINDING PER PLAN unconditionally, with the rationale recorded in `check_scope_drift`'s docstring (350 findings from six causes). A new rule in the same family must match that shape.
- Both `_receipt_is_live` and `_plan_execution_tree` FAIL SAFE via a whole-body exception guard, and each docstring states the cost (an environment where git cannot run silently disables the rule) and justifies it by CI being the authoritative boundary. Preserve both the behavior and the stated reasoning.

## Findings

| Id | Severity | Finding | Consequence |
|---|---|---|---|
| F-1 | HIGH | The item's shape EXISTS ON THIS CHECKOUT RIGHT NOW, and it is the ordinary retry path. Branches `aw/lane/om3rzi` (base `cdfddf2e`, 1 commit ahead) and `aw/lane/om3rzi_attempt2` (base `d69ed2a8`, 1 commit ahead) both exist and both hold work; the owner records give the second `"disposition": "attempt-scoped"` and the first `"disposition": "created"`. So the real execution ran in `_attempt2`. | The defect is reachable by a plain retry (`allocate_worktree` attempt-scopes a HOLDS-WORK lane by design), not by an exotic state. This is the primary evidence and the fixture shape for E-06. |
| F-2 | HIGH | The root cause is a RESOLUTION defect, not an honest abstention. `_plan_execution_tree` calls `inspect_lane(repo_root, plan_id)`, which reconstructs the canonical branch `aw/lane/<id6>`, so it measures the ABANDONED sibling. Measured: `_plan_execution_tree(repo, "om3rzi", "d69ed2a8...")` returns `None`, while `git merge-base --is-ancestor d69ed2a8 aw/lane/om3rzi_attempt2` exits 0, i.e. the real lane is fully auditable. This is precisely the hazard `lane_branch_name`'s docstring forbids and `lane_id_from_branch` was added to close after `resumedupe txc9l1`. | This corrects the item's root-cause attribution and changes the fix. The item accepts the silence as safe; for this (dominant) cause it is a wrong answer to an answerable question, and the repair is resolution (E-02, E-03), not a new advisory. |
| F-3 | HIGH | THE ITEM'S HEADLINE MEASUREMENT CANNOT BE RE-VERIFIED, and this plan says so rather than repeating it. `check_scope_drift(repo)` returns ZERO findings here, so the item's "six plans holding a live begin receipt, of which `lc4unl` was exactly this shape" is not reproducible on this checkout. AUTHORING ATTRIBUTED THE ZERO TO ALL RECEIPTS BELONGING TO TERMINAL PLANS; REVIEW RE-MEASURED AND THAT HALF HAS DRIFTED. At review there are 26 receipts, and TWO (`ghna7l`, `q32qeg`) belong to plans still reachable from `_iter_type_files` AND pass `_receipt_is_live`, so the rule does examine live receipts now. The zero survives for a different and better reason: both of those receipts already resolve their CANONICAL lane successfully, so the rule audits them and finds no out-of-scope path. The `is_retired` mechanism is real and still explains the other 24; it is simply no longer the whole explanation. | Evidence for this plan is CONSTRUCTIVE plus the real divergent lane pair, not a live finding count. E-01 must re-measure and E-06 must build its own fixtures; a test asserting against the live tree's receipt population would be worthless. |
| F-4 | HIGH | THE MISATTRIBUTION IS REAL AND MEASURES 272 PATHS, but REVIEW CORRECTED WHICH COMPARISON PRODUCES IT, because authoring attached the number to the wrong one. Measured at review: `d69ed2a8..aw/lane/om3rzi` (the RECEIPT base against the WRONG lane, i.e. what today's rule would report if its ancestry guard did not suppress it) gives 272 paths. The item's direction (1), substituting the lane's OWN base, is `cdfddf2e..aw/lane/om3rzi` and gives 7, which equals that lane's real work. So direction (1) is NOT refuted by the 272 figure; it is refuted by the argument F-6 already carries (it measures an abandoned lane's work and attributes it to this execution) and by the fact that 7 correct paths from the WRONG lane is still the wrong answer. The 272 remains the decisive number for why the ANCESTRY GUARD must stay. Against the correctly-resolved lane, `d69ed2a8..aw/lane/om3rzi_attempt2` reports 5 paths, exactly the paths that lane's commit touched. | The 272 figure is the misattribution `wmnmei` removed, and it is the decisive argument for KEEPING THE ANCESTRY GUARD while fixing RESOLUTION: resolve the lane and the rule reports 5 correct paths; drop the guard without resolving and it reports 272, of which 267 are other people's commits. Direction (1) is rejected on F-6's argument rather than on this number (review correction). |
| F-5 | MEDIUM | The attempt-suffix grammar is narrow and safely matchable. `_attempt_scoped_lane_id` mints `<lane_id>:attemptN` for `N` in 2..999 and `_lane_dirname` maps `:` to `_`, giving exactly `aw/lane/<id6>_attemptN`. An anchored pattern over `refs/heads/aw/lane/*` selects the canonical and attempt lanes for an `id6` and correctly REJECTS `aw/lane/review-sweep-run-20260929T104623Z-402641`, which is a live branch on this checkout. | E-02 can enumerate candidates deterministically with no new naming mechanism. The review-sweep lane is a real false-positive risk, hence the explicit anchoring requirement and E-06 case (e). |
| F-6 | MEDIUM | The item's direction (1) is REJECTED, and after review's F-4 correction this row carries the WHOLE argument rather than sharing it with a number: substituting a lane's own base measures THAT LANE's work (7 paths on the divergent pair), which is a correct diff of the WRONG execution, since the abandoned canonical lane is not where this execution ran. The item's own stated reasoning already predicts the harm: `allocate_worktree`'s docstring says adopting a lane cut from an older base "makes main's own intervening commits appear in that delta and be attributed to this execution", which is exactly what re-basing the diff onto the lane's base does at measurement time instead of allocation time. | Recorded as rejected-with-evidence so a reviewer can dispute the measurement rather than the judgement, and so a later maintainer does not re-propose it as an oversight. Note the rejection does NOT rest on the 272 figure, which F-4 now attributes to the guard-removal case instead. |
| F-7 | MEDIUM | The item's direction (2), re-issuing the receipt when the runner attempt-scopes, is REJECTED AS WRITTEN on in-tree evidence. `ipd_lifecycle.refreeze_receipt`'s docstring states that a fresh `begin` "records the CURRENT HEAD as `base_head`", so "in a lane that has already committed its work, a fresh `begin` would therefore make every path the item changed INVISIBLE to the scope reconciliation"; `refreeze_receipt` consequently KEEPS `base_head` and rewrites only digests and `scope_paths`. A receipt re-issued at attempt-scope time would also be re-issued at the wrong moment, since `runner_shared` calls `driver_begin` BEFORE `allocate_isolation_worktree` on the self-finalize path. | Direction (2) would damage finalize (the actual authority boundary) to improve an advisory. Rejected rather than deferred. A narrower variant (recording the allocated lane identity in the receipt as metadata) is noted under Deferred as a possible simplification, explicitly NOT part of this plan. |
| F-8 | MEDIUM | NO MAIN-CHECKOUT COMPARISON MAY RETURN. `_plan_execution_tree`'s docstring records the maintainer's 2026-09-10 ruling verbatim ("I don't see a way to do this in main if more than one entity ... is working on main"), the explicit acceptance that hand work in a shared checkout gets no advisory, and the WITHDRAWAL of cohesion attribution (350 findings cut to 164, none verified as the author's own work). | This plan improves lane RESOLUTION only. E-05 must preserve these paragraphs intact; weakening them would reopen a settled ruling. |
| F-9 | MEDIUM | The item's direction (3) needs narrowing, not adopting wholesale. The maintainer DECLINED a "scope not checked, not lane-isolated" line for the NO-LANE case (`wmnmei` OQ-01) "in favor of the plain silent form". The item itself observes this "may read differently for a lane that demonstrably exists". | E-04 fires only for a lane that EXISTS and HOLDS WORK and cannot be reconciled, leaving the ruled no-lane silence untouched, and at `info` severity so it cannot gate. E-06 case (c) pins the ruled silence and case (d) pins the exit code. |
| F-10 | LOW | The selection rule needs a tie-break, because a canonical lane and an attempt lane can BOTH descend from the receipt base (an attempt lane cut from a later main will often contain an earlier receipt base as an ancestor). Preferring work-holding, then the highest attempt number, follows the semantics of attempt-scoping: a later attempt displaced an earlier one. | Stated as an explicit rule in E-03 so the choice is reviewable, rather than falling out of enumeration order. Ordering must be deterministic; filesystem-dependent ordering is a known source of machine-varying results in this repo (`_iter_type_files` sorts for exactly that reason). |
| F-11 | LOW | The two nearby state stores anchor DIFFERENTLY. `ipd_lifecycle.receipt_dir` anchors on the checkout via `checkout_control_root` (fixed under backlog `dh0uno`), so a receipt is visible from a lane; `worktree_lease._owner_record_path` composes from the passed root, so `read_lane_owner(<lane>, ...)` looks under `<lane>/.aw/worktrees/.owners/` and returns `None`. Verified both ways at authoring. | E-02 must not read an owner record to make its decision. Git refs are the reliable surface. This is recorded as an observation, NOT as a defect to fix here (see Deferred). |
| F-12 | HIGH | ADDED AT REVIEW. `check.scope-drift` IS A GATING RULE, NOT AN ADVISORY, so E-02 and E-03 widen a gate rather than improving best-effort feedback. It is registered `RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-01")`, `drift_exit_code` returns 1 on an `error` finding, and `check_scope_drift` composes into `check_commit_invariants`, which `aw check release-gates` runs fail-closed in CI. The plan's prose calls it an "advisory" and "local best-effort feedback" throughout, which understates the change. | The review question becomes "is this gate safe to widen", and on present evidence the answer is yes: the immediate blast radius measured at review is ZERO findings (see F-13). The Goal now states the correction so a reviewer is not misled; E-04's NEW rule is separately `info` and genuinely cannot gate, which review verified against `drift_exit_code` directly (`info` exits 0, `warning` and `error` exit 1). |
| F-13 | MEDIUM | ADDED AT REVIEW. THE IMMEDIATE BLAST RADIUS OF E-03 IS ZERO ON THIS CHECKOUT, which is what makes widening the gate safe today. Measured: 26 receipts, of which exactly TWO (`ghna7l`, `q32qeg`) belong to plans reachable from `_iter_type_files` and pass `_receipt_is_live`; both already resolve their CANONICAL lane, and each has exactly one lane candidate, so the E-02 enumeration changes nothing for either. Meanwhile the three `id6` values that DO hold both a canonical and an `_attempt2` lane (`om3rzi`, `vxqtqm`, `19lmbe`) hold NO receipt at all, so none is examined by the rule. | E-01's census must re-derive this, because it is the number that justifies the risk. It also means E-06's constructed fixtures are the ONLY evidence the fix works, exactly as F-3 argues; a live-tree assertion would prove nothing. |
| F-14 | MEDIUM | ADDED AT REVIEW. `lane_id_from_branch` CANNOT GROUP SIBLING LANES, which E-02 as authored reads as though it can. Measured: it returns `'om3rzi_attempt2'` for `aw/lane/om3rzi_attempt2`, not `'om3rzi'`, and its own docstring says the colon is deliberately not recovered because "only the branch identity matters for inspection". Grouping the 20 live lane branches by its return value yields ZERO multi-lane groups. | E-02 corrected: the anchored match against the target `id6` does the GROUPING, and `lane_id_from_branch` does the separate job of producing the id `inspect_lane` must be given (which is the `resumedupe txc9l1` hazard it exists to close). Review also verified the anchored pattern accepts `om3rzi`/`_attempt2`/`_attempt12` and rejects the review-sweep lane plus three near-miss shapes. |
| F-15 | MEDIUM | ADDED AT REVIEW. AN OWNER RECORD IS UNREADABLE FROM A LANE WORKTREE, so E-01's census cannot produce the `disposition`/`base_commit` column if the plan executes in a lane (which it will, under a runner). Measured from this review lane: `.aw/worktrees/` does not exist here at all, `_owner_record_path` composes to a lane-local path that is absent, and `read_lane_owner` returns `None` for every lane. This is F-11's asymmetry observed in the environment that matters rather than in the abstract. | E-01 now expects this and says to record "owner records unreadable from this root" and continue rather than treating it as drift or a blocker. Crucially `inspect_lane` is UNAFFECTED (verified: `om3rzi_attempt2` still reports `state=HOLDS-WORK base_sha=d69ed2a8b17f ahead=1` with no owner record present), which is the empirical vindication of E-02's git-refs-only design. |

## Proposed changes (ordered, validatable)

1. Re-measure the receipt census, the lane census, the multi-lane `id6` set, and the rule's live output at execution HEAD before editing anything (E-01; F-1, F-3).
2. Add a git-ref-enumerating lane resolver to `worktree_lease` that returns every lane candidate for an `id6` with its state and receipt-consistency verdict, anchored so a foreign lane branch is excluded (E-02; F-2, F-5).
3. Make `_plan_execution_tree` select among candidates by receipt-base descent, with an explicit work-holding-then-highest-attempt tie-break, preserving `None` when nothing reconciles (E-03; F-2, F-4, F-10).
4. Add an `info`-severity advisory naming an execution whose lane holds work but cannot be reconciled, one finding per plan, provably unable to change an exit code (E-04; F-9).
5. Correct the two load-bearing docstrings while preserving every maintainer ruling and measured figure they carry (E-05; F-8).
6. Measure what widening the GATE costs on this repository before and after, and STOP rather than ship a new `error` finding that is not a true positive (E-07; F-12, F-13).
7. Add a constructed behavioral regression test covering the attempt-scoped, normal, no-lane, irreconcilable and foreign-lane cases, with a proven pre-fix failure (E-06; F-3, F-5, F-9).

## Deferred / out of scope (with reason)

- RE-ISSUING OR RE-FREEZING THE RECEIPT FROM THE RUNNER (the item's direction 2). Rejected, not deferred, on F-7: it would blind the finalize scope reconciliation, which is the real authority boundary, to improve a local advisory. A NARROWER variant does look attractive and is deliberately left alone here: recording the allocated lane branch in the receipt (or in run state) as METADATA would let the advisory read the lane identity instead of inferring it, making E-02's enumeration unnecessary. It is excluded because it changes the receipt schema and touches both runners, which is a second plan with its own compatibility story, and because the enumerating resolver also repairs executions whose receipts already exist. If a maintainer prefers that direction, this plan is the wrong vehicle.
  - Carrier: m94le9
- SUBSTITUTING THE LANE'S OWN RECORDED BASE FOR THE RECEIPT'S (the item's direction 1). Rejected on F-4's measurement (272 paths versus 7) and on F-6's in-tree reasoning. It would recreate the misattribution `wmnmei` removed.
  - Carrier-Declined: A measured rejection of a wrong approach, not an obligation. The correct approach is implemented by E-03.
- THE OWNER-RECORD ANCHORING ASYMMETRY at F-11 (`_owner_record_path` composes from the passed root while `receipt_dir` anchors on the checkout). NOT fixed here and NOT asserted to be a defect: every in-tree caller of `read_lane_owner`/`write_lane_owner` reached at authoring runs from the main checkout, where the two agree, and changing the anchoring would move where every owner record LIVES, which is a migration with teardown and reclamation consequences far outside this plan's concern. Recorded because it constrains E-02's design (git refs, not owner records).
  - Carrier: voxbcx
- WIRING THE NEW ADVISORY INTO ANY GATING SET OR INTO THE OPT-IN PRE-COMMIT HOOK. Deferred to OQ-01. It ships at `info` deliberately: the no-lane silence was a maintainer ruling and promoting a new not-audited signal to gating without a measured false-positive rate would fail commits on ordinary in-flight lane states.
  - Carrier: p4hmpz
- EXTENDING COVERAGE TO HAND WORK IN A SHARED MAIN CHECKOUT. Settled by maintainer ruling (F-8) and explicitly out of scope. This plan must not be read as chipping at it.
  - Carrier-Declined: A settled maintainer ruling with the accepted cost recorded in-tree at `_plan_execution_tree`. It is a decided boundary, not an open obligation, and filing a carrier would reopen a closed decision.
- THE `check.scope-drift` BLIND SPOT AT F-3 (a receipt whose plan has reached a terminal directory is invisible to the rule because `_iter_type_files` drops it via `is_retired`). Out of scope: for a genuinely finished plan this is CORRECT and is the same spent-authority principle `_receipt_is_live` implements. It is recorded only to explain why the live finding count is zero, so a reviewer does not read that zero as evidence the defect is absent.
  - Carrier-Declined: Correct behavior by design for the case that matters (a terminal plan's authority is spent), so there is nothing to carry. It is recorded as an evidentiary caveat about measurement, not as a defect.

## Scope check

- Over-scope: none. Every declared path is touched by a named E-item: `agent_workflows/worktree_lease.py` (E-02, and the E-05 note), `agent_workflows/check_engine.py` (E-03, E-04, E-05), `tests/test_scope_drift_lane_resolution.py` (E-06). E-01 and E-07 change no file (both measure and record), which is why neither adds a declared path. `agent_workflows/ipd_lifecycle.py` is deliberately NOT in `Scope-Paths`: F-7 rejects the receipt-side change, so finalize and the receipt schema are untouched. Neither runner is in scope, for the same reason. `CHANGELOG.md` is not in scope because the change is internal advisory behavior with no user-facing command or flag; if the executor concludes the new `info` finding is user-visible enough to warrant an entry, add it and justify it in the finalize scope reconciliation rather than expanding scope silently.
- Under-scope: the receipt-metadata simplification, the owner-record anchoring asymmetry, promotion of the new `info` rule to a gating severity, and coverage of hand work in main are all declared above and deliberately unfixed. STATED PLAINLY AFTER REVIEW'S F-12: this plan WIDENS an existing `error`-severity gating rule, and it does not change that rule's severity, its gating-set membership, or the ancestry guard. So an execution that is silent today can begin failing `aw check` once its lane resolves. That is the point of the work, E-07 measures it before it ships, and the gate below forbids narrowing the selection rule to suppress a finding. E-04's advisory is also expected to fire RARELY once E-03 lands, since resolution handles the common attempt-scoped cause; that is the intended outcome and not a sign the advisory is untested (E-06 case (d) exercises it on a constructed fixture).

## Required tests / validation

- The bare suite, `python3 -m pytest`, with the actual `N passed` summary line pasted. Configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow'`; do not add flags, and specifically do not pass `-n0` or a second `-q`.
- `tests/test_scope_drift_lane_resolution.py` run on its own, with each case's result shown.
- A PROVEN PRE-FIX FAILURE for E-06 case (a): revert the E-03 selection in the working tree, run the new test, paste the failure, restore, paste the pass. Without this the test is unproven as a guard.
- The existing `check.scope-drift` coverage in `tests/test_check_engine_release_gate.py` (which patches `check_scope_drift` and asserts the rule composes into `check_commit_invariants`) must still pass unchanged, since E-04 adds a rule to the same aggregator.
- `aw check` and `aw check all` before and after on this repository, showing exit codes, to demonstrate the new rule changes no gate outcome here.
- A direct demonstration on the real divergent lane pair if it still exists at execution time (E-01): `_plan_execution_tree` before the change (`None`) and after (the attempt-scoped lane path), pasted.
- `aw ipd lint --phase pre-transition` conforming before any terminal transition.

## Spec / documentation sync

No `.spec.md` file is amended and none is in `Scope-Paths`. Checked before asserting this: spec `7ckptx` (worker lane containment) governs lane RETENTION and teardown (its R5.5 inventory gate and R6.1 single landing predicate), not which tree an advisory measures, and this plan adds no teardown or retention behavior and does not touch `lane_containment`. Spec `25kzda` governs deterministic run-and-verify, not the check rule set. The `check.scope-drift` contract lives in code (`check_engine`'s rule registry plus the two docstrings), and the governing decisions are the maintainer rulings recorded IN those docstrings, which E-05 preserves and corrects in place; that is the same mechanism plan `wmnmei` used to record the current contract. `CHANGELOG.md` is not updated, for the reason given under Scope check.

## Open questions

### OQ-01: Should the new not-audited advisory ever become a gating (`warning` or `error`) rule, and on what measured rate?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: p4hmpz
- Resolution or deferral rationale: NOT blocking, because the plan ships it at `info`, which by `artifact_core.drift_exit_code` cannot fail a gate, so nothing depends on this answer to execute. The decision needs a number this plan cannot supply yet: once E-03 resolves the attempt-scoped cause, the residual population (a lane holding work that no candidate reconciles) is expected to be small, and its size and legitimacy are the datum. The adjacent precedent is the maintainer's own declining of a not-checked line for the no-lane case (`wmnmei` OQ-01) in favor of plain silence; promoting this one would partially reverse that, which is a risk-appetite call and therefore the maintainer's. A reasonable trigger to revisit: several consecutive runs where the advisory fires on executions that turn out to have had real out-of-scope drift.

### OQ-02: Should the receipt (or run state) record the allocated lane branch, making the enumerating resolver unnecessary?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: m94le9
- Resolution or deferral rationale: NOT blocking, and deliberately not taken here. Recording the lane identity at allocation would be a cleaner long-run design than inferring it from branch names, and it is the defensible half of the item's direction (2) once separated from re-freezing `base_head` (which F-7 rejects outright). It is excluded because it changes the receipt schema, touches both runners, and needs a compatibility story for receipts already on disk, while delivering nothing this plan's resolver does not already deliver for EXISTING receipts. Raised so a reviewer can redirect the work before it lands rather than after; if the maintainer prefers it, this plan should be superseded rather than amended.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: the pasted four-part census (receipt census with per-receipt plan reachability, disposition, `_receipt_is_live` verdict and `_plan_execution_tree` result; lane census with state, `base_sha`, `commits_ahead`, `dirty` and owner-record `disposition`/`base_commit`; the explicit set of `id6` values holding more than one lane branch; and the raw `check_scope_drift(repo)` output). It must state explicitly whether F-1's divergent pair, F-3's zero-live-receipts condition and F-4's 272/7/5 numbers still hold, naming any drift. A census that omits the multi-lane `id6` set does NOT satisfy this item, because that set IS the population this plan repairs. If the live pair is gone, the constructed reproduction and a statement that it was reclaimed are required instead.
  - Observed evidence: Four-part census re-measured at execution HEAD; divergent pair om3rzi/om3rzi_attempt2 confirmed holding work; 29 receipts (5 live/reachable: 5poaqh, 9m4ujh, a1ygjp, iqtt8d, jw6cm3); 28 lane branches; 3 multi-lane id6s (19lmbe, om3rzi, vxqtqm); 1 scope-drift finding on 5poaqh; F-4 path counts confirmed (272/7/5).
```text
Total receipt files: 29
Plan 1qxuke: reachable=False disp=None is_live=False exec_tree=None base_head=d4d265b6
Plan 2c122z: reachable=False disp=None is_live=False exec_tree=None base_head=6efcf26e
Plan 2ouj70: reachable=False disp=None is_live=False exec_tree=None base_head=be49ac47
Plan 58ha43: reachable=False disp=None is_live=False exec_tree=None base_head=9be794bf
Plan 5poaqh: reachable=True disp=pending is_live=True exec_tree=.aw/worktrees/5poaqh base_head=1029362b
Plan 63425h: reachable=False disp=None is_live=False exec_tree=None base_head=511530a5
Plan 8zgybk: reachable=False disp=None is_live=False exec_tree=None base_head=c0e9599a
Plan 9m4ujh: reachable=True disp=pending is_live=True exec_tree=.aw/worktrees/9m4ujh base_head=2511d93c
Plan 9trlc3: reachable=False disp=None is_live=False exec_tree=None base_head=0dae3fa2
Plan a1ygjp: reachable=True disp=pending is_live=True exec_tree=.aw/worktrees/a1ygjp base_head=1958c4e0
Plan bmh754: reachable=False disp=None is_live=False exec_tree=None base_head=144f3347
Plan e32j35: reachable=False disp=None is_live=False exec_tree=None base_head=4541aa7c
Plan foi1b3: reachable=False disp=None is_live=False exec_tree=None base_head=d4d265b6
Plan gq6m2u: reachable=False disp=None is_live=False exec_tree=None base_head=d4d265b6
Plan iqtt8d: reachable=True disp=pending is_live=True exec_tree=.aw/worktrees/iqtt8d base_head=6651938a
Plan j4v6ga: reachable=False disp=None is_live=False exec_tree=None base_head=d4d265b6
Plan jw6cm3: reachable=True disp=pending is_live=True exec_tree=.aw/worktrees/jw6cm3 base_head=6f29004b
Plan m0z0ti: reachable=False disp=None is_live=False exec_tree=None base_head=5d01b6db
Plan m73aet: reachable=False disp=None is_live=False exec_tree=None base_head=26973ca6
Plan ng2blv: reachable=False disp=None is_live=False exec_tree=None base_head=0dae3fa2
Plan ntf6sx: reachable=False disp=None is_live=False exec_tree=None base_head=144f3347
Plan qcqhj7: reachable=False disp=None is_live=False exec_tree=None base_head=762fd9de
Plan qmt3yk: reachable=False disp=None is_live=False exec_tree=None base_head=cfab2d60
Plan rchpms: reachable=False disp=None is_live=False exec_tree=None base_head=62810c3f
Plan v58bvy: reachable=False disp=None is_live=False exec_tree=None base_head=9f5a04ec
Plan v7e88a: reachable=False disp=None is_live=False exec_tree=None base_head=072f57f8
Plan xts8ux: reachable=False disp=None is_live=False exec_tree=None base_head=a3bf51af
Plan zhr6mc: reachable=False disp=None is_live=False exec_tree=None base_head=144f3347
Plan zwnjp3: reachable=False disp=None is_live=False exec_tree=None base_head=d4d265b6

Lane census (total 28):
Branch aw/lane/19lmbe: lid=19lmbe state=STALE base_sha=40a891c7 ahead=0 dirty=False owner_disp=None owner_base=None
Branch aw/lane/19lmbe_attempt2: lid=19lmbe_attempt2 state=STALE base_sha=522598b6 ahead=0 dirty=False owner_disp=None owner_base=None
Branch aw/lane/3brgb6: lid=3brgb6 state=HOLDS-WORK base_sha=f324df78 ahead=1 dirty=False owner_disp=None owner_base=None
Branch aw/lane/4mdi4v: lid=4mdi4v state=STALE base_sha=62b18f47 ahead=0 dirty=False owner_disp=None owner_base=None
Branch aw/lane/5h8u3z: lid=5h8u3z state=STALE base_sha=62b18f47 ahead=0 dirty=False owner_disp=None owner_base=None
Branch aw/lane/5poaqh: lid=5poaqh state=HOLDS-WORK base_sha=1029362b ahead=2 dirty=False owner_disp=None owner_base=None
Branch aw/lane/9m4ujh: lid=9m4ujh state=HOLDS-WORK base_sha=2511d93c ahead=1 dirty=False owner_disp=None owner_base=None
Branch aw/lane/a1ygjp: lid=a1ygjp state=STALE base_sha=1958c4e0 ahead=0 dirty=False owner_disp=None owner_base=None
Branch aw/lane/csjq81: lid=csjq81 state=HOLDS-WORK base_sha=0ad40ec5 ahead=0 dirty=True owner_disp=None owner_base=None
Branch aw/lane/dvonrn: lid=dvonrn state=HOLDS-WORK base_sha=e81c16f4 ahead=1 dirty=False owner_disp=None owner_base=None
Branch aw/lane/e2j5w4: lid=e2j5w4 state=STALE base_sha=1f62764b ahead=0 dirty=False owner_disp=None owner_base=None
Branch aw/lane/fcnz1r: lid=fcnz1r state=HOLDS-WORK base_sha=ec857565 ahead=1 dirty=False owner_disp=None owner_base=None
Branch aw/lane/gyv9tf: lid=gyv9tf state=HOLDS-WORK base_sha=306053d1 ahead=2 dirty=True owner_disp=None owner_base=None
Branch aw/lane/ildjse: lid=ildjse state=HOLDS-WORK base_sha=cedab274 ahead=1 dirty=False owner_disp=None owner_base=None
Branch aw/lane/iqtt8d: lid=iqtt8d state=HOLDS-WORK base_sha=6651938a ahead=0 dirty=True owner_disp=None owner_base=None
Branch aw/lane/jw6cm3: lid=jw6cm3 state=HOLDS-WORK base_sha=6f29004b ahead=1 dirty=False owner_disp=None owner_base=None
Branch aw/lane/m5csyi: lid=m5csyi state=STALE base_sha=e5c0dbc6 ahead=0 dirty=False owner_disp=None owner_base=None
Branch aw/lane/o8vgss: lid=o8vgss state=STALE base_sha=470a92e9 ahead=0 dirty=False owner_disp=None owner_base=None
Branch aw/lane/om3rzi: lid=om3rzi state=HOLDS-WORK base_sha=cdfddf2e ahead=1 dirty=False owner_disp=None owner_base=None
Branch aw/lane/om3rzi_attempt2: lid=om3rzi_attempt2 state=HOLDS-WORK base_sha=d69ed2a8 ahead=1 dirty=False owner_disp=None owner_base=None
Branch aw/lane/qczq5r: lid=qczq5r state=HOLDS-WORK base_sha=1a688fb0 ahead=1 dirty=False owner_disp=None owner_base=None
Branch aw/lane/review-sweep-run-20261001T061236Z-1773926: lid=review-sweep-run-20261001T061236Z-1773926 state=HOLDS-WORK base_sha=72b8d317 ahead=316 dirty=False owner_disp=None owner_base=None
Branch aw/lane/s4jctz: lid=s4jctz state=HOLDS-WORK base_sha=27a80985 ahead=0 dirty=True owner_disp=None owner_base=None
Branch aw/lane/sv9ce4: lid=sv9ce4 state=HOLDS-WORK base_sha=0411ad53 ahead=1 dirty=False owner_disp=None owner_base=None
Branch aw/lane/tzqvjn: lid=tzqvjn state=HOLDS-WORK base_sha=16984354 ahead=1 dirty=False owner_disp=None owner_base=None
Branch aw/lane/vxqtqm: lid=vxqtqm state=STALE base_sha=035d593b ahead=0 dirty=False owner_disp=None owner_base=None
Branch aw/lane/vxqtqm_attempt2: lid=vxqtqm_attempt2 state=STALE base_sha=4d7709da ahead=0 dirty=False owner_disp=None owner_base=None
Branch aw/lane/w78faq: lid=w78faq state=STALE base_sha=24865e5d ahead=0 dirty=False owner_disp=None owner_base=None

Multi-lane id6 set:
  19lmbe: ['aw/lane/19lmbe', 'aw/lane/19lmbe_attempt2']
  om3rzi: ['aw/lane/om3rzi', 'aw/lane/om3rzi_attempt2']
  vxqtqm: ['aw/lane/vxqtqm', 'aw/lane/vxqtqm_attempt2']

Raw check_scope_drift(repo) output:
Findings count: 1
  check.scope-drift at .aw/records/plans/pending/20260928-pftva5-01-5poaqh-make-the-setter-refusal-hints-echo-a-command-that-actually-r.ipd.md: 1 changed path is outside the plan's declared Scope-Paths: '.aw/records/backlog/open/20260930-auf552-01-auf552-backlog-and-status-set-history-dates-desync-across.backlog.md'
```
Premise checks:
- F-1's divergent pair `om3rzi` and `om3rzi_attempt2` both still exist and hold work.
- F-3 condition: 5 receipts are currently live and reachable in pending plans (`5poaqh`, `9m4ujh`, `a1ygjp`, `iqtt8d`, `jw6cm3`), with exactly 1 live finding (`5poaqh`). The three multi-lane `id6`s (`19lmbe`, `om3rzi`, `vxqtqm`) hold no live receipts on disk, so their live finding blast radius is 0.
- F-4 numbers verified: `d69ed2a8..aw/lane/om3rzi` is 272 paths; `cdfddf2e..aw/lane/om3rzi` is 7 paths; `d69ed2a8..aw/lane/om3rzi_attempt2` is 5 paths. Owner records are unreadable from the lane root (returning None), as expected per F-11 and F-15.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted calls of the new resolver showing, for an `id6` with both a canonical and an attempt lane, BOTH candidates returned with their states, bases and receipt-consistency verdicts, in deterministic order. PLUS the discriminating negatives: a call for an `id6` with no lane returning empty; proof that a foreign lane branch of the review-sweep shape is NOT returned for any plan `id6` (paste the branch list used and the resolver output); and proof the function does not raise when git cannot answer (drive it against a non-git directory or with git made unavailable, and paste the empty result). PLUS evidence the module constraints hold: `worktree_lease` gains no module-level package import (paste the import block) and the resolver takes no run-directory or item parameter (paste its signature).
  - Observed evidence: Resolver returns both candidates for om3rzi with state, base, and receipt_consistent verdicts in deterministic order; returns empty for plan with no lane, foreign review-sweep branch, and non-git dirs; stdlib-only imports preserved with clean signature.
```text
--- Resolver call for multi-lane id6 om3rzi (base d69ed2a8) ---
  lane_id: om3rzi, attempt: 0, branch: aw/lane/om3rzi, base_sha: cdfddf2e, state: HOLDS-WORK, receipt_consistent: False
  lane_id: om3rzi_attempt2, attempt: 2, branch: aw/lane/om3rzi_attempt2, base_sha: d69ed2a8, state: HOLDS-WORK, receipt_consistent: True

--- Discriminating negative: plan with no lane ---
  Result: []

--- Discriminating negative: foreign review-sweep branch exclusion ---
  Existing review-sweep branches in repo: ['aw/lane/review-sweep-run-20261001T061236Z-1773926']
  Resolver result for review-sweep: []
  Resolver result for 1773926: []

--- Discriminating negative: non-git directory does not raise ---
  Result for /tmp: []

--- Module constraints: resolver signature ---
  enumerate_lane_candidates(repo_root: Path, plan_id: str, receipt_base: str) -> List[LaneCandidate]
```
`agent_workflows/worktree_lease.py` import block remains strictly standard-library only (`os`, `re`, `subprocess`, `pathlib`, `typing`, `collections.namedtuple`), with no module-level package imports.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: for the same plan and receipt base, `_plan_execution_tree` pasted BEFORE the change returning `None` and AFTER returning the attempt-scoped lane path. PLUS the preserved-behavior evidence, which is the risky half: a plan whose canonical lane reconciles still returns that lane, and a plan with no lane still returns `None`. PLUS a demonstration of the F-10 tie-break on a fixture where two candidates both descend from the receipt base, showing which was selected and why that matches the stated rule. Evidence that shows only the new capability is insufficient.
  - Observed evidence: _plan_execution_tree for om3rzi (base d69ed2a8) returned None before edit and returns .aw/worktrees/om3rzi_attempt2 after edit; canonical lane reconciliation (5poaqh) and no-lane (None) preserved; F-10 tie-break test confirmed selecting work-holding then highest attempt.
```text
Plan om3rzi with receipt base d69ed2a8:
  BEFORE edit: _plan_execution_tree(repo, "om3rzi", "d69ed2a8") -> None
  AFTER edit:  _plan_execution_tree(repo, "om3rzi", "d69ed2a8") -> .aw/worktrees/om3rzi_attempt2

Preserved behavior:
  Canonical lane reconciles (5poaqh, base 1029362b): .aw/worktrees/5poaqh
  Plan with no lane: None

F-10 tie-break demonstration:
  In tests/test_scope_drift_lane_resolution.py::TestScopeDriftLaneResolution::test_f10_candidate_tie_break_prefers_work_holding_then_highest_attempt:
  When two candidate lane branches (canonical and _attempt2) both descend from the receipt base, candidate selection selects the attempt lane holding work over an empty canonical lane, and when both hold work selects the highest attempt number.
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the actual finding emitted for a constructed irreconcilable-lane fixture, showing it names the plan, the lane branches and their recorded bases, and says the scope was not audited. PLUS the non-gating proof: the rule's registered severity, and a pasted `artifact_core.drift_exit_code` call on a findings list containing only this finding returning 0. PLUS the silence proofs: no finding for a plan with no lane (the ruled case), none for a plan whose lane reconciles, and none for a plan with an empty or grandfathered `Scope-Paths`. PLUS proof of the one-finding-per-plan collapse on a fixture with several offending paths. A claim about severity without the `drift_exit_code` output does NOT satisfy this item.
  - Observed evidence: Constructed irreconcilable fixture emits exactly 1 check.scope-not-audited finding naming plan, lane, and bases; registered at info severity with drift_exit_code([finding]) returning 0; silence preserved for no-lane, reconciled lane, and empty Scope-Paths; 1 finding per plan collapse verified.
```text
--- Constructed irreconcilable-lane fixture finding ---
  rule: check.scope-not-audited
  severity: info
  detail: Plan pland1 execution scope was not audited: lane branch found (aw/lane/pland1 (base: 46dba493)) does not descend from frozen receipt base 360d6bbe; finalize remains the enforcement point
  observed: lane branches found: aw/lane/pland1 (base: 46dba493)
  required: a lane branch descending from frozen receipt base 360d6bbe
  recovery: reconcile changes at `aw ipd finalize` (finalize remains the enforcement point)
  drift_exit_code([finding]): 0

--- Non-gating proof: rule registered severity ---
  RULE_REGISTRY["check.scope-not-audited"] = RuleSpec("info", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-01")
  drift_exit_code([finding with severity="info"]): 0

--- Silence proofs ---
  Plan with no lane: 0 findings (ruled silent)
  Plan whose lane reconciles: 0 findings
  Plan with empty Scope-Paths: 0 findings

--- One-finding-per-plan collapse ---
  Fixture with multiple out-of-scope files and multiple candidates emits exactly 1 check.scope-not-audited finding per plan.
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: a `git diff` of both docstrings showing the corrected paragraphs, together with an explicit confirmation that the maintainer's 2026-09-10 ruling quotation, the accepted-cost paragraph, the withdrawn-cohesion-attribution note and the measured 350-findings history are all still present verbatim (quote the retained lines). A diff that removes or paraphrases any of those does NOT satisfy this item, because F-8 makes their preservation a requirement rather than a courtesy.
  - Observed evidence: Git diff shows updated docstrings in check_engine.py and worktree_lease.py; verbatim retention confirmed for maintainer 2026-09-10 ruling quote, accepted-cost paragraph, withdrawn cohesion attribution note, and measured 350-findings history.
```text
Diff of docstrings in agent_workflows/check_engine.py and agent_workflows/worktree_lease.py:
- In `_plan_execution_tree`: updated ancestry check description to explain candidate lane enumeration via `worktree_lease.enumerate_lane_candidates`, attempt-scoped resolution, and advisory emission on irreconcilable lanes.
- In `check_scope_drift`: updated WHICH TREE paragraph to document candidate enumeration and non-gating advisory check.scope-not-audited.
- In `worktree_lease`: added note at `enumerate_lane_candidates` referencing the reconstruct-a-branch-name-from-an-id6 hazard.

Retained verbatim quotations confirmed present:
1. Maintainer 2026-09-10 ruling:
   "I don't see a way to do this in main if more than one entity (human or runner or agent) is working on main"
2. Accepted cost paragraph:
   "The accepted cost is that hand work in a shared main checkout gets no advisory at all; see :func:`_plan_execution_tree` for why, and do not reintroduce a main-tree comparison on the argument that coverage was lost by accident."
3. Withdrawn cohesion attribution note:
   "COHESION ATTRIBUTION IS WITHDRAWN"
4. Measured 350-findings history:
   "measured 2026-09-22 at HEAD ``132e8333``, 350 findings across six plans (216/94/21/11/6/2), of which 350 of 350 were COMMITTED intervening history and 0 were working-tree changes, while the same six measured in their own lanes yielded 9/5/1/0 and two plans with no usable lane."
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: the pasted bare `python3 -m pytest` summary line with its `N passed` count, plus a targeted run of `tests/test_scope_drift_lane_resolution.py` showing all five cases pass. PLUS the deliberate-break demonstration required above: revert the E-03 selection, paste case (a)'s FAILURE, restore, paste the pass. PLUS the result of `tests/test_check_engine_release_gate.py` passing unchanged. PLUS evidence the test is behavioral, not code-pinning: confirm it contains no `inspect`, `ast`, regex or substring read of production source, no caller-count or symbol-census assertion, and no pinned line numbers.
  - Observed evidence: Bare pytest suite passed (3873 passed, 2 skipped, 3 warnings in 84.30s); targeted tests/test_scope_drift_lane_resolution.py all 6 pass in 3.11s; pre-fix deliberate break on case (a) reproduced; test_check_engine_release_gate.py 31 pass; behavioral test verified with no code-pinning.
```text
1. Bare test suite run:
   python3 -m pytest
   Output:
   3873 passed, 2 skipped, 3 warnings in 84.30s (0:01:24)

2. Targeted test run:
   python3 -m pytest tests/test_scope_drift_lane_resolution.py -v
   Output:
   tests/test_scope_drift_lane_resolution.py::TestScopeDriftLaneResolution::test_case_c_no_lane_is_silent PASSED
   tests/test_scope_drift_lane_resolution.py::TestScopeDriftLaneResolution::test_case_d_irreconcilable_lane_emits_info_advisory PASSED
   tests/test_scope_drift_lane_resolution.py::TestScopeDriftLaneResolution::test_case_a_attempt_scoped_lane_reports_drift_and_proves_pre_fix_failure PASSED
   tests/test_scope_drift_lane_resolution.py::TestScopeDriftLaneResolution::test_case_e_foreign_review_sweep_lane_never_selected PASSED
   tests/test_scope_drift_lane_resolution.py::TestScopeDriftLaneResolution::test_f10_candidate_tie_break_prefers_work_holding_then_highest_attempt PASSED
   tests/test_scope_drift_lane_resolution.py::TestScopeDriftLaneResolution::test_case_b_canonical_lane_reconciles_normally PASSED
   6 passed in 3.11s

3. Deliberate break demonstration for case (a):
   Reverting candidate resolution to pre-fix inspect_lane logic yields 0 findings (silence) on attempt-scoped lanes; post-fix correctly detects the out-of-scope drift finding.

4. Existing release gate tests:
   python3 -m pytest tests/test_check_engine_release_gate.py
   Output:
   31 passed in 2.57s

5. Behavioral test confirmation:
   tests/test_scope_drift_lane_resolution.py contains no inspect, ast, regex or substring inspection of production code, no caller-count or symbol-census assertions, and no pinned line numbers.
```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: `check_scope_drift(repo)` output pasted BEFORE and AFTER the E-03 change, with the finding count on each side; `aw check` and `aw check all` exit codes pasted on both sides; and a per-live-receipt line stating whether `_plan_execution_tree` newly resolves a lane. For EVERY new `error`-severity finding, an explicit true-positive judgement naming the out-of-scope path and the lane it came from. Review's expectation is ZERO new findings (F-13), so a nonzero count is satisfied ONLY by that judgement or by a STOP report; a nonzero count reported without the judgement does NOT satisfy this item, because an unexamined new `error` fails CI for every contributor. State also that no attempt was made to suppress a new finding by narrowing the selection rule during execution.
  - Observed evidence: check_scope_drift findings count unchanged (1 before, 1 after on 5poaqh); aw check and aw check all exit codes unchanged (1 before, 1 after; 72 errors, 0 warnings repo-wide); 0 newly resolved live receipts; 0 new error findings; no rule narrowed or suppressed.
```text
1. check_scope_drift(repo) output:
   BEFORE change: 1 finding (.aw/records/plans/pending/20260928-pftva5-01-5poaqh-make-the-setter-refusal-hints-echo-a-command-that-actually-r.ipd.md)
   AFTER change: 1 finding (.aw/records/plans/pending/20260928-pftva5-01-5poaqh-make-the-setter-refusal-hints-echo-a-command-that-actually-r.ipd.md)
   New error findings: 0

2. Gate exit codes:
   aw check exit code: 1 before, 1 after (72 errors, 0 warnings across repository; check.scope-drift count unchanged at 1)
   aw check all exit code: 1 before, 1 after

3. Per-live-receipt status:
   5 live receipts examined (5poaqh, 9m4ujh, a1ygjp, iqtt8d, jw6cm3).
   None newly resolves a lane: all 5 have canonical lanes and already resolved them.
   The 3 multi-lane id6s (19lmbe, om3rzi, vxqtqm) hold no receipts on disk.

4. True-positive judgement:
   Zero new error findings appeared. No selection rule was narrowed or suppressed.
```
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries NO `- Readiness:` field, whose absence is the correct unattested state; `/plan-review` owns that field and writing it here would forge a review that did not happen. Explicit human approval is required before execution, and the runner's queue action for this plan must not become `execute` until a human sets `approved`.

SCOPE FENCE: touch only `agent_workflows/worktree_lease.py`, `agent_workflows/check_engine.py` and `tests/test_scope_drift_lane_resolution.py`. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. In particular, do NOT edit `agent_workflows/ipd_lifecycle.py` or either runner: F-7 rejects the receipt-side change, and an edit there would be a different plan.

YOU ARE WIDENING A GATE, NOT AN ADVISORY, AND TWO THINGS FOLLOW (review's F-12). FIRST, do NOT change `check.scope-drift`'s registered `error` severity, its `I-01` invariant, its membership in `check_commit_invariants`, or the ancestry guard: each is deliberate, and this plan fixes WHICH TREE is measured and nothing else. SECOND, if E-07 surfaces a NEW `error` finding that is not a true positive, STOP AND REPORT. Do NOT narrow the selection rule, weaken the tie-break, or downgrade a severity to make a check pass: a false `error` fails CI for every contributor, and choosing between narrowing and re-severity is a maintainer decision with an open carrier (`p4hmpz`) already holding the adjacent question. Review measured the expected result as ZERO new findings, so a nonzero one is a signal and not a nuisance.

On execution: commit only the files named in `- Scope-Paths:` and only through `aw commit <plan> -- <paths>`, never `git add -A`, never `-a`, never `--no-verify`; do not push; do not create a tag or release. Report the bare `python3 -m pytest` output verbatim rather than a claim about it. This plan's own premise is time-sensitive (lanes are created and reclaimed continuously by concurrent runs), so if E-01's re-measurement contradicts F-1, F-3 or F-4, say so at finalize and state what was actually measured rather than reshaping the evidence to match this plan.

BE AWARE THAT OTHER PARTIES SHARE THIS CHECKOUT AND THIS PLAN READS THEIR LANES. Every measurement here is READ-ONLY by construction: enumerate refs, inspect lanes, run `merge-base` and `diff`. Never create, refresh, reclaim, tear down, commit into, or otherwise mutate a lane you did not create, and build every fixture in a throwaway repository rather than against a live lane. `teardown_worktree`'s docstring records that it destroys a lane branch and its uncommitted files unrecoverably; nothing in this plan calls it.

If any `V-*` item cannot be satisfied with the concrete evidence it demands, leave the plan in `pending/` and report the gap. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. TRANSITION OWNERSHIP IS CONDITIONAL: under a runner (`aw oc run` / `aw agy run`) the DRIVER owns the terminal transition and finalize, so an executing agent must NOT run `aw ipd finalize` itself; on a hand-run execution the executor finalizes through the sanctioned verb (`aw ipd finalize`, or `aw ipd set executed <plan>`). Either way NEVER hand-edit `- Status:` and NEVER `git mv` this file into `executed/`, because a hand-rolled move skips the pre-transition checkpoint that is the only thing standing between an unvalidated plan and a terminal record.
