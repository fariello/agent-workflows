# IPD: Retire an orchestrator in a coordinator-owned throwaway worktree so the rollup lands as one ref update

- Date: 2026-09-13
- Kind: child
- Concern: Orchestrator retirement performs three mutations in the SHARED checkout (edit the plan's status, move it to `executed/`, commit) behind a journal. Between the move and the commit there is a real window in which main is dirty, and a slow or contended commit widens it. Measured: a fault-injected retirement rolled the plan back correctly but still left two untracked index files behind, so a failed retirement does not restore the tree it started from.
- Scope: Perform the retirement's mutations in a COORDINATOR-OWNED throwaway worktree and land the result on main as a single ref update, and fix the index-file residue a failed retirement leaves. Excludes the pre-launch gate (Order 01), the integration gate (Order 02), and the backlog close (Order 03). Excludes any change to the eligibility rule or to the worker-role refusal.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/runner_shared.py, tests/test_orchestrator_retirement.py
- Item-Dependencies: none
- Status: to-review
- Set: dirtygates
- Order: 4
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: u23gbn
- Priority: medium
- Work-Kind: bug

## Workflow history

- 2026-09-13 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-09-13 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): authored after the maintainer challenged the claim that retirement is atomic. The challenge was correct: it is three operations, and a fault-injection run proved the rollback leaves untracked residue (F-3).

## Goal

Make an orchestrator's retirement arrive on main the way a lane's work does: as one ref update that either happened or did not. Keep the coordinator role, the eligibility gate, and the worker-role refusal exactly as they are.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: do the mutations off the shared checkout

- [ ] E-01 Perform the retirement's mutation sequence in a throwaway worktree created and owned by the COORDINATOR, not in the shared checkout. The existing pattern to reuse is `commit_lock.commit_isolated` (`:216-238`), which snapshots HEAD into a detached worktree, mirrors the paths, runs the real hooks there, and advances the branch under a compare-and-swap; it exists precisely because committing in the shared tree lets `pre-commit` stash and then restore over a peer's write. THE ROLE MUST REMAIN `coordinator`: retirement's first gate refuses when `AW_EXECUTION_ROLE=worker` (`ipd_lifecycle.py:2237-2246`), and this worktree is a coordinator-owned scratch tree, NOT a worker lane. Do not set, inherit, or emulate the worker role in it.
  - Depends on: none
  - Expected outcome: a retirement performs no edit, move, or commit in the shared checkout; main advances by one ref update.
  - Execution state: pending
- [ ] E-02 Keep the journalled transaction and its rollback, and state plainly what each layer now guarantees. The journal (`PHASE_PREPARED` -> `PHASE_MUTATING` -> `PHASE_READY_TO_COMMIT` -> `PHASE_COMMITTED_INCOMPLETE`/`PHASE_COMPLETE`, `:132-147`) plus `_rollback_precommit` (`:1874`) handle crash recovery ACROSS invocations; the throwaway worktree removes the shared-tree exposure WITHIN one invocation. These are complementary, not redundant. Do NOT delete the journal in the belief the worktree replaces it: `PHASE_COMMITTED_INCOMPLETE` and `PHASE_UNKNOWN_OUTCOME` still classify outcomes the CAS cannot.
  - Depends on: E-01
  - Expected outcome: crash recovery still works, and the docstrings say which layer covers which failure.
  - Execution state: pending

### Task group 2: fix the measured residue

- [ ] E-03 Stop a failed retirement leaving untracked index files in the shared checkout. MEASURED 2026-09-13 with `fault_injection="after_move"`: the plan was correctly restored to `pending/` with its original bytes, the `executed/` copy was removed, and HEAD was unmoved, but `git status --porcelain` afterwards reported `?? .aw/records/plans/INDEX.json` and `?? .aw/records/plans/INDEX.md`. `_rollback_precommit` step 4 "regenerates the plans index from the CURRENT corpus", which WRITES those files rather than restoring their prior state. They are untracked, so today's clean-base check (which excludes untracked) does not refuse on them, but the tree is still not as found. Either restore their prior state, or regenerate them inside the throwaway worktree so the shared tree is never written at all. The second is preferable because it follows from E-01.
  - Depends on: E-01
  - Expected outcome: after a failed retirement, `git status --porcelain` in the shared checkout is byte-identical to before the attempt.
  - Execution state: pending
- [ ] E-04 Add the assertion the existing fault tests lack. `tests/test_orchestrator_retirement.py:1961-1972` already asserts the plan is restored, the destination is gone, and HEAD is unmoved, but it never asserts the TREE IS CLEAN, which is why F-3 went unnoticed. Add that assertion to the existing fault-injection tests (`after_move` and `before_commit`) rather than writing a parallel test, so the property is pinned where the failure actually occurred.
  - Depends on: E-03
  - Expected outcome: the suite fails if a failed retirement leaves any residue in the shared checkout.
  - Execution state: pending

### Task group 3: prove the window is gone

- [ ] E-05 Add a test proving the shared checkout is never dirty DURING a successful retirement, not merely after it. Observe the tree at the point the old code would have had the plan moved but uncommitted (the fault-injection hooks `after_move` and `before_commit` already provide those instants). This is the property the maintainer identified and the one the journal alone does not provide.
  - Depends on: E-01, E-02
  - Expected outcome: at every observable instant of a retirement, the shared checkout is clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A WORKER may commit facts about its own item; only the COORDINATOR may commit facts about a whole Set. Retirement asserts every child of a Set is executed, so it is coordinator-only and re-checks eligibility itself rather than trusting the caller ("Kind alone is NOT authority"). This plan changes WHERE the coordinator works, never WHO may retire.
- `commit_isolated` is the shipped precedent for "run the real hooks somewhere private, then advance the ref under a CAS". It even reports `ISO_RACED` when a peer commit landed since the snapshot, which is the honest outcome rather than silently discarding their work.
- Retirement deliberately omits the pre-transition E/V checkpoint because an orchestrator's items are performed by its children. That omission is recorded in `ROLLUP_OMITTED_GATES` and is out of scope here.

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | Retirement is three mutations, not one, and only the last is a commit. So there is a window in which the shared checkout holds a moved-but-uncommitted plan. | `retire_orchestrator` (`ipd_lifecycle.py:2187`) delegates the status change to `status_set`, then the finalize transaction stages and commits; phases `PHASE_MUTATING` and `PHASE_READY_TO_COMMIT` (`:133-138`) name that window explicitly |
| F-2 | The journal provides RECOVERY, not atomicity. A failure is repaired by replaying or rolling back on a later invocation, which is strictly weaker than a ref update that either happened or did not. | `_rollback_precommit` (`:1874-1925`) and the `PHASE_COMMITTED_INCOMPLETE` / `PHASE_UNKNOWN_OUTCOME` classifications (`:139-144`) |
| F-3 | A FAILED retirement does not restore the tree it started from. Measured with the shipped fault injector: tree before was empty; after `after_move` the plan was correctly restored and HEAD unmoved, but the tree held `?? .aw/records/plans/INDEX.json` and `?? .aw/records/plans/INDEX.md`. | reproduced during authoring via the repository's own test harness |
| F-3a | SEVERITY QUALIFIER ADDED AT REVIEW, so the fix is not oversold: in THIS repository both index files are GITIGNORED (`.aw/.gitignore:45-46`, confirmed with `git check-ignore -v`; neither is tracked), so they do not appear in `git status --porcelain` here at all and cannot dirty this checkout. The residue was observed in the test harness's own fixture repo, which does not carry that ignore rule. So F-3 is a real correctness defect in the rollback (it writes files it does not restore) and is worth fixing, but it is NOT a live cause of the 2026-09-13 outage and must not be described as one. E-04's tree-cleanliness assertion is the durable value here, because it pins the property in the fixture where the residue IS visible. | `.aw/.gitignore:45-46`; `git check-ignore -v .aw/records/plans/INDEX.json`; `git ls-files --error-unmatch` reports both untracked |
| F-4 | The existing fault tests would not catch F-3, because they assert plan restoration and HEAD but never tree cleanliness. | `tests/test_orchestrator_retirement.py:1961-1972` |
| F-5 | Retirement CANNOT be moved into a worker lane, so a coordinator-owned scratch worktree is the only route to a single-ref-update rollup. | `retire_orchestrator`'s first gate refuses `AW_EXECUTION_ROLE=worker` (`ipd_lifecycle.py:2237-2246`), and a lane turn runs as worker |
| F-6 | Retirement is cheap and frequent, so the window is hit often. It spends no agent turn and runs as an ordinary queue item on both hosts. | `dispatch_orchestrator_item` (`runner_shared.py:3259`), called from `oc_runipd.py:7385` |

## Proposed changes (ordered, validatable)

1. Perform the mutations in a coordinator-owned throwaway worktree and land via a CAS ref update (E-01).
2. Keep the journal, and document which layer covers which failure (E-02).
3. Stop leaving index residue on a failed retirement (E-03).
4. Assert tree cleanliness in the existing fault tests (E-04).
5. Prove the shared checkout is clean at every instant of a successful retirement (E-05).

## Deferred / out of scope (with reason)

- Moving retirement into a worker lane. Impossible by design per F-5; the worker-role gate refuses it, and that gate is correct because retirement is a Set-level claim.
- Removing the journalled transaction. Complementary to the worktree per E-02, and it still classifies outcomes a CAS cannot.
- Changing the eligibility rule, the `Kind: orchestrator` gate, or the omitted pre-transition checkpoint. All out of scope; this plan changes only where the coordinator performs its writes.
- Making the plans index tracked, or changing how it is generated. Out of scope; E-03 only requires that a failed retirement not leave the shared tree altered.

## Scope check

- Over-scope: none. Three files, all directly implicated.
- Under-scope: this plan fixes retirement only. Other coordinator-side writes to the shared checkout may exist and are not audited here. Say so at review if a full audit is wanted; it would be a separate plan.

## Required tests / validation

- The existing fault-injection tests, extended with a tree-cleanliness assertion (E-04), passing.
- The during-retirement cleanliness test (E-05), passing.
- A successful retirement still lands: the orchestrator reaches `executed/`, the commit subject keeps its `lifecycle(<id>)` marker so the journal's observed-state classification still works, and the commit is path-scoped to owned paths only (an existing test asserts this and must stay green).
- A CAS race case: a peer commit landing between snapshot and update is reported honestly rather than silently discarding the peer's work.
- Both hosts, since `dispatch_orchestrator_item` is shared and called by each.
- Full suite run bare, with the failure set diffed against a baseline from the same commit; paste both counts and the diff.

## Spec / documentation sync

- Spec `77tr3o` R-4/R-5/R-6 govern this transition. This plan changes WHERE the mutations happen, not WHAT the transition means, so no amendment is expected. VERIFY BEFORE EXECUTING: read those requirements and confirm none fixes the work to the shared checkout. If one does, amend that spec in this plan and add the spec file to `Scope-Paths` first.
- Update `retire_orchestrator`'s docstring and the `ROLLUP_*` commentary to describe the worktree, so a later reader does not reintroduce shared-tree mutation.

## Open questions

### OQ-01: Reuse `commit_isolated` directly, or add a retirement-specific isolated transaction?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: `commit_isolated` already does snapshot, mirror, real hooks, CAS, and it reports `ISO_RACED` honestly, so reusing it avoids a second implementation of a subtle mechanism. But it takes a path list and commits them, whereas retirement must also EDIT the plan and MOVE it, so the mutation has to happen somewhere before the commit; that may fit naturally inside the same worktree or may want its own helper. Non-blocking because either route satisfies every V-item, and the choice is visible in review. Raised so the implementer does not fork a near-copy of `commit_isolated` without saying why.

### OQ-02: Should the index files be regenerated in the worktree, or restored from the journal on rollback?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: regenerating inside the throwaway worktree follows from E-01 and means the shared tree is never written, which is the stronger property; restoring from the journal keeps the change local to `_rollback_precommit`. The author prefers regenerating in the worktree. Non-blocking because E-03's acceptance is stated as an observable property (tree byte-identical after a failure), which either route satisfies.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a successful retirement showing the orchestrator in `executed/` on main, plus proof the shared checkout was never mutated: the `git status --porcelain` observations taken at the fault-injection instants, all empty. Paste the resulting commit's `--name-status`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a crash-recovery case (a stale pre-commit journal) still recovering correctly, and paste the docstring text stating which layer covers within-invocation exposure and which covers across-invocation crashes.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `git status --porcelain` before and after a `fault_injection="after_move"` retirement, both EMPTY. The pre-change measurement showed `?? INDEX.json` and `?? INDEX.md`; the after must show neither.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the extended fault-injection test output, and demonstrate the assertion is real by showing it FAIL against the pre-change behavior (or by stating precisely why that demonstration is not possible).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the during-retirement test output showing a clean shared checkout at every observed instant, plus the bare full-suite counts before and after with the FAILED-set diff.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit only files this plan changed, path-scoped, never `git add -A`, never push. Paste actual runner output for every test claim. Do not weaken the worker-role gate or the eligibility gate in the course of this change; both are load-bearing and neither is in scope.

Post-gate lifecycle move: this plan reaches `executed/` only when every V-item above carries pasted evidence and `aw ipd lint --phase pre-transition` reports conforming.
