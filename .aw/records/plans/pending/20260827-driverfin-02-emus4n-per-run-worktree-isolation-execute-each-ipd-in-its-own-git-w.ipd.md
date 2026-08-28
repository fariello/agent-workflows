# IPD: Per-run worktree isolation: execute each IPD in its own git worktree via worktree_lease, then integrate the verified branch back to main

- Date: 2026-08-27
- Kind: child
- Concern: The driver runs every IPD's agent in the ONE main working tree, so concurrent runs (and even a serial run inheriting a prior run's uncommitted leftovers) clobber each other's files and finalize refuses on foreign dirty paths - the root of this session's contamination. The `worktree_lease` module already provides `allocate_worktree`/`teardown_worktree`/`allocate_session`/`LeaseTable`/`assert_worker_scope` (an earlier vwios6ipd run DID use `/tmp/opencode/aw-*-wt` worktrees), but the current driver ignores it. This child makes the driver execute each IPD in its own isolated worktree/branch and integrate the verified result back to main.
- Scope: Wrap the child-01 begin/execute/finalize pipeline in per-IPD worktree isolation: (1) before the agent turn, `allocate_worktree` a fresh worktree on a run/<id6> branch (via worktree_lease) and point the agent at it (`--dir <worktree>`); (2) begin/execute/verify/finalize all happen IN that worktree, so the main tree is untouched during the turn; (3) after finalize succeeds in the worktree, INTEGRATE the verified branch back to main (fast-forward if possible; else a controlled merge of only that IPD's commits); (4) `teardown_worktree` on success. Run-ledger + begin receipts remain anchored to the main repo's gitignored `.aw/` keyed by run-id (OQ from orchestrator) so finalize/state is findable regardless of worktree. This child delivers isolation + happy-path integration; the fail-closed guard + merge-CONFLICT handling is child 03. Reuse worktree_lease; do not fork worktree logic.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/worktree_lease.py, tests/
- Item-Dependencies: executed:p7peqf
- Status: reviewed
- Set: driverfin
- Order: 2
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: emus4n

## Workflow history
- 2026-08-28 reviewed (/plan-review opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed (corrected worktree path `.aw/worktrees/<lane>` + branch `aw/lane/<id6>`, resolved the plan-move vs worker path-fence architecture via OQ-02, routed E-02 through the reused `execute_merge_and_revalidate_gate`, added agy parity coverage, completed execution contract). GO - PENDING HUMAN APPROVAL (gated on child-01 p7peqf executed).
- 2026-08-28 to-review (aw set): status set to to-review
- 2026-08-28 reviewed (aw set): status set to reviewed
- 2026-08-28 to-review (aw set): status set to to-review

- 2026-08-28 reviewed (Antigravity): /plan-review passed with revisions; resolved Item-Dependencies to executed:p7peqf, populated concrete V evidence, resolved OQ-01, and completed execution gate.
- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Execute each IPD's agent turn in its own isolated git worktree/branch (via worktree_lease), keeping the main tree untouched during the turn, then integrate the verified branch back to main - so runs cannot contaminate each other or the main checkout.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: isolate the turn

- [ ] E-01 In `execute_item` (both `oc_runipd.py` and `agy_runipd.py`), before the child-01 begin/execute pipeline, call `worktree_lease.allocate_worktree(repo, lane_id=<id6>)` (auto-branch `aw/lane/<id6>` under `.aw/worktrees/<id6>`) and run the agent with `--dir <handle.path>` (replacing the `--dir <repo>` at `oc_runipd.py:1333`); begin/execute/verify/finalize occur in the worktree. Anchor run-ledger + begin receipts to the MAIN repo's gitignored `.aw/state/`+`.aw/records/runs/` keyed by run-id (pass the main `repo` to begin/finalize, `--dir <worktree>` only to the agent) so state is findable from either tree.
  - Depends on: none
  - Expected outcome: the agent edits/commits only in its worktree; `git status` on the main tree is clean during the turn; the begin receipt is written under the main repo's `.aw/state/ipd-lifecycle/`.
  - Execution state: pending

### Task group 2: integrate back + teardown

- [ ] E-02 After finalize succeeds in the worktree, integrate the verified `aw/lane/<id6>` branch into main by REUSING `orchestrate_isolation.execute_merge_and_revalidate_gate` (do NOT fork ff/merge logic): build one `LaneOutcome` (base_commit = worktree base, head_commit = post-finalize HEAD, changed_files from the branch diff) and call the gate with `merge_order=[lane_id]` and the driver's full-validation runner. On `IntegrationGateResult.passed` -> commits land on main, then `teardown_worktree`. On a conflict/stale-base/lane-failure result -> leave NOT integrated with a recorded reason (deferred to child-03), do NOT teardown-force-away the branch, do NOT fake executed. Conflict DETECTION comes from the gate; conflict RESOLUTION is child-03.
  - Depends on: E-01
  - Expected outcome: a verified child's commits (including child-01's plan-move to executed/) land on main via the reused integration gate; the worktree is removed on success; a non-passing integration is recorded and deferred, not faked.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `worktree_lease`: `allocate_worktree(repo_root, lane_id, *, base_commit="HEAD")`/`teardown_worktree` (WorktreeHandle), `allocate_session`, `LeaseTable` (per-path exclusive ownership), `assert_worker_scope` (worker-forbidden paths). Worktrees are created under the gitignored `repo_root/.aw/worktrees/<lane>` (`WORKTREES_SUBDIR = ".aw/worktrees"`, `worktree_lease.py:32,83`); the per-lane branch is auto-derived as `aw/lane/<lane_id>` (`worktree_lease.py:84`), NOT a caller-chosen `run/<id6>`. Pass a lane id (e.g. the child's id6) as `lane_id`.
- The driver launches the agent with `--dir <repo>` today (`oc_runipd.py:1333`, `argv.extend(["--dir", state["repo"], ...])`); change that to `--dir <worktree_path>` for the isolated turn.
- `.aw/records/runs/` is gitignored (per install); keep run state in the main repo keyed by run-id, not duplicated per worktree, so finalize can find the begin receipt.
- INTEGRATION IS NOT RE-IMPLEMENTED (`worktree_lease.py:17-18`): the canonical reuse-verbatim integration surface is `orchestrate_isolation.execute_merge_and_revalidate_gate(integration_base_commit, lane_outcomes, merge_order, full_validation_runner, declared_scope=...)`, which gathers `LaneOutcome`s, DETECTS conflicts/stale-base/lane-failure, re-runs full validation on the combined HEAD, and returns an `IntegrationGateResult`. E-02 MUST route through this, not fork ff/merge logic.
- WORKER PATH-FENCE HAZARD (`worktree_lease.py:199-216`): `FORBIDDEN_WORKER_PATH_HINTS` includes `.aw/records/plans/` and `.aw/records/runs/`, and `assert_worker_scope` fails closed on a worker write to them. child-01's `aw ipd finalize` MOVES the plan under `.aw/records/plans/` (pending/ -> executed/) and makes a path-scoped lifecycle commit - a tracked change on a coordinator-owned surface. See Findings for the resolution this child adopts.

## Findings

- Isolation is the structural fix for contamination (impossible to clobber across worktrees). The genuinely new risk is integration and, next child, conflict RESOLUTION; the allocate/execute half is a direct reuse of worktree_lease.
- PLAN-MOVE vs PATH-FENCE (resolution): child-01's `aw ipd finalize` runs INSIDE the worktree (a complete checkout, so `.aw/records/plans/` and the plan file exist there). It moves the plan pending/ -> executed/ and makes the path-scoped lifecycle commit ON the `aw/lane/<id6>` branch; that commit is then carried to main by `execute_merge_and_revalidate_gate`. `assert_worker_scope`/`FORBIDDEN_WORKER_PATH_HINTS` fence UNTRUSTED PARALLEL WORKER agent writes (the exec-set lane model); they are NOT applied to the driver's own coordinator-driven finalize step here. This distinction is load-bearing and is surfaced as OQ-02 for human confirmation before execution.
- INTEGRATION reuse: E-02 gathers a single `LaneOutcome` for the child's `aw/lane/<id6>` branch (base_commit = the worktree base, head_commit = post-finalize HEAD, changed_files from the diff) and calls `execute_merge_and_revalidate_gate` with `merge_order=[lane_id]` and the driver's validation runner. A `passed` result integrates to main; a `INTEGRATION_FAILED_CONFLICT`/stale-base/lane-failure result leaves the child NOT integrated (recorded, deferred to child-03), never faked executed. Conflict DETECTION is free from the gate; conflict RESOLUTION is child-03.

## Proposed changes (ordered, validatable)

1. `oc_runipd.py`/`agy_runipd.py`: allocate worktree, run agent in it, anchor state to main repo by run-id.
2. Integrate verified branch to main (ff/controlled-merge) + teardown.
3. `tests/`: main tree clean during a turn; verified commits integrate to main; worktree torn down.

## Deferred / out of scope (with reason)

- Merge CONFLICT handling + fail-closed guard: child 03 (this child is happy-path integration).
- Self-finalize itself: child 01 (dependency).

## Scope check

- Over-scope: none.
- Under-scope: none (isolate + happy-path integrate + teardown is this child's deliverable).

## Required tests / validation

- During an agent turn, the main working tree stays clean (assert `git status` empty on main while the worktree is dirty). Cover BOTH `test_oc_runipd.py` and `test_agy_runipd_cli.py`.
- A verified IPD's commits integrate to main via the reused `execute_merge_and_revalidate_gate` (passed case) and the worktree is removed; a non-passing gate result (conflict/stale-base) is recorded and deferred, not faked executed.
- Run state (begin receipt under `.aw/state/ipd-lifecycle/`, ledger under `.aw/records/runs/`) is anchored to the main repo by run-id and finalize finds it from the worktree.

Validation command: `python -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -q` (paste the actual runner output; do not claim success unrun).

## Spec / documentation sync

- Document that `aw oc/agy run` isolates each IPD in a worktree; cross-ref worktree_lease.

## Open questions

### OQ-01: Isolation per-IPD or per-set (one worktree reused across a set's children)?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved. Per-IPD worktree allocation is selected for maximum cleanliness, isolation determinism, and parallel safety. Each IPD executes in its own isolated worktree and merges back to main upon successful verification and finalization.

### OQ-02: Does the driver's coordinator-driven finalize (which writes the plan-move under `.aw/records/plans/`) bypass the worker path-fence, and is finalize-in-worktree the right layer?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: Resolved with the design recorded in Findings. `assert_worker_scope`/`FORBIDDEN_WORKER_PATH_HINTS` (`worktree_lease.py:199-216`) fence UNTRUSTED PARALLEL WORKER agent writes (the exec-set lane model), NOT the driver's own coordinator-driven `aw ipd finalize`. Finalize runs inside the worktree (a full checkout where `.aw/records/plans/` and the plan file exist), commits the plan-move on the `aw/lane/<id6>` branch, and `execute_merge_and_revalidate_gate` carries that commit to main. The driver does NOT call `assert_worker_scope` around the finalize step. Human to confirm this layering at approval; if instead finalize should run against the main tree post-integration, that is a foundational re-shape and this child would be REPLANNED.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Unit tests in `tests/test_oc_runipd.py` AND `tests/test_agy_runipd_cli.py` (both drivers in Scope-Paths) asserting that during a simulated child execution the MAIN git working tree has an empty `git status` while mutations occur only within the allocated worktree at `repo/.aw/worktrees/<id6>` (the real `WORKTREES_SUBDIR` path), the worktree branch is `aw/lane/<id6>`, and the begin receipt is written under the MAIN repo's `.aw/state/ipd-lifecycle/<id6>.receipt.json`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Tests in `tests/test_oc_runipd.py` AND `tests/test_agy_runipd_cli.py` demonstrating that on a verified turn the driver builds a `LaneOutcome` and calls `orchestrate_isolation.execute_merge_and_revalidate_gate` (not a forked merge), a `passed` result lands the child's commits (including the child-01 plan-move to executed/) on main and `teardown_worktree` removes the worktree, AND a non-passing `IntegrationGateResult` (e.g. `INTEGRATION_FAILED_CONFLICT`) leaves the child NOT integrated with a recorded reason and does not fake executed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:

1. Open questions: OQ-01 and OQ-02 RESOLVED; execution requires explicit human approval AND requires child-01 (`p7peqf`) executed first (`Item-Dependencies: executed:p7peqf`).
2. Scope fence: touch ONLY `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `agent_workflows/worktree_lease.py` (reuse; extend only if strictly required), and `tests/` (`test_oc_runipd.py`, `test_agy_runipd_cli.py`). REUSE `orchestrate_isolation.execute_merge_and_revalidate_gate` verbatim; do NOT fork merge logic and do NOT edit `orchestrate_isolation.py`. Do NOT implement merge-CONFLICT resolution or the fail-closed guard (child 03). If the work seems to need more, STOP and report.
3. Honesty rule (HARD MUST): when you report tests/validation passed, paste the ACTUAL runner output (`python -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -q`); never claim success you did not run.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move on completion: verify all V items with pasted test output, run `aw ipd lint --phase pre-transition`, then finalize via `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Do NOT mark executed or move the plan unless validation actually passed.
