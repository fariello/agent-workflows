# IPD: Per-run worktree isolation: execute each IPD in its own git worktree via worktree_lease, then integrate the verified branch back to main

- Date: 2026-08-27
- Kind: child
- Concern: The driver runs every IPD's agent in the ONE main working tree, so concurrent runs (and even a serial run inheriting a prior run's uncommitted leftovers) clobber each other's files and finalize refuses on foreign dirty paths - the root of this session's contamination. The `worktree_lease` module already provides `allocate_worktree`/`teardown_worktree`/`allocate_session`/`LeaseTable`/`assert_worker_scope` (an earlier vwios6ipd run DID use `/tmp/opencode/aw-*-wt` worktrees), but the current driver ignores it. This child makes the driver execute each IPD in its own isolated worktree/branch and integrate the verified result back to main.
- Scope: Wrap the child-01 begin/execute/finalize pipeline in per-IPD worktree isolation: (1) before the agent turn, `allocate_worktree` a fresh worktree on a run/<id6> branch (via worktree_lease) and point the agent at it (`--dir <worktree>`); (2) begin/execute/verify/finalize all happen IN that worktree, so the main tree is untouched during the turn; (3) after finalize succeeds in the worktree, INTEGRATE the verified branch back to main (fast-forward if possible; else a controlled merge of only that IPD's commits); (4) `teardown_worktree` on success. Run-ledger + begin receipts remain anchored to the main repo's gitignored `.aw/` keyed by run-id (OQ from orchestrator) so finalize/state is findable regardless of worktree. This child delivers isolation + happy-path integration; the fail-closed guard + merge-CONFLICT handling is child 03. Reuse worktree_lease; do not fork worktree logic.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/worktree_lease.py, tests/
- Item-Dependencies: unresolved
- Status: draft
- Set: driverfin
- Order: 2
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: emus4n

## Workflow history

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Execute each IPD's agent turn in its own isolated git worktree/branch (via worktree_lease), keeping the main tree untouched during the turn, then integrate the verified branch back to main - so runs cannot contaminate each other or the main checkout.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: isolate the turn

- [ ] E-01 Before the child-01 begin/execute pipeline, `allocate_worktree` (worktree_lease) a fresh worktree on a run/<id6> branch and run the agent with `--dir <worktree>`; begin/execute/verify/finalize occur in the worktree. Anchor run-ledger + begin receipts to the main repo's gitignored `.aw/` keyed by run-id so state is findable. The main tree stays unmodified during the turn.
  - Depends on: none
  - Expected outcome: the agent edits/commits only in its worktree; `git status` on the main tree is clean during the turn.
  - Execution state: pending

### Task group 2: integrate back + teardown

- [ ] E-02 After finalize succeeds in the worktree, integrate the verified run/<id6> branch into main (fast-forward if possible, else a controlled merge of only that IPD's commits), then `teardown_worktree`. Happy-path only (no conflict) - conflict handling is child 03.
  - Depends on: E-01
  - Expected outcome: the verified commits land on main; the worktree is removed; main reflects the executed IPD.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `worktree_lease`: `allocate_worktree`/`teardown_worktree` (WorktreeHandle), `allocate_session`, `LeaseTable` (per-path exclusive ownership), `assert_worker_scope` (worker-forbidden paths). Worktrees are created under a gitignored location (earlier run used `/tmp/opencode/aw-*-wt`).
- The driver launches the agent with `--dir <repo>` today; change that to `--dir <worktree>` for the isolated turn.
- `.aw/records/runs/` is gitignored (per install); keep run state in the main repo keyed by run-id, not duplicated per worktree, so finalize can find the begin receipt.

## Findings

Isolation is the structural fix for contamination (impossible to clobber across worktrees). The genuinely new risk is integration (E-NEW task 2) and, next child, conflicts; the allocate/execute half is a direct reuse of worktree_lease.

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

- During an agent turn, the main working tree stays clean (assert `git status` empty on main while the worktree is dirty).
- A verified IPD's commits integrate to main (fast-forward case) and the worktree is removed.
- Run state (begin receipt, ledger) is anchored to the main repo by run-id and finalize finds it from the worktree.

## Spec / documentation sync

- Document that `aw oc/agy run` isolates each IPD in a worktree; cross-ref worktree_lease.

## Open questions

### OQ-01: Isolation per-IPD or per-set (one worktree reused across a set's children)?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Per-IPD is simplest + maximally isolated but re-creates a worktree per child; per-set reuses one worktree across a set's children (they share context, and the set integrates once). Lean per-IPD for isolation clarity; revisit if worktree churn is costly. Decide in implementation.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).
