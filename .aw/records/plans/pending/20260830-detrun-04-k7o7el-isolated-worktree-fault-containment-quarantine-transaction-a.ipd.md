# IPD: Isolated worktree fault containment, quarantine transaction, and commit gateway trailers

- Date: 2026-08-30
- Kind: child
- Concern: Worktree mutation failures currently risk leaving dirty paths in the main working tree or aborting entire multi-item runs rather than containing errors item-locally.
- Scope: Implement worktree allocation with path leases, the 7-step deterministic containment transaction for failed/out-of-scope mutations, the exhaustive 6-class `ABORT RUN` engine, and the commit gateway appending `AW-Run:` and `AW-Item:` trailers. Implements spec 25kzda Sections 4.1, 4.2, 5.1, and 5.7.
- Scope-Paths: agent_workflows/worktree_containment.py, agent_workflows/commit_gateway.py, agent_workflows/orchestrate_isolation.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_fault_containment.py
- Item-Dependencies: executed:kaygwo
- Status: to-review
- Set: detrun
- Order: 4
- Highest E allocated: 06
- Author: antigravity
- Id: k7o7el
- Blocks-Release: next

## Workflow history

- 2026-08-30 draft (antigravity): created.
- 2026-08-30 to-review (antigravity): authored from approved spec 25kzda (20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md).

## Goal

Provide a robust worktree isolation and fault-containment system that isolates mutations, automatically quarantines and rolls back out-of-scope or failed item mutations without polluting the workspace, restricts run aborts to six fatal integrity violations, and formats commit trailers immutably.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Worktree allocation and path lease management

- [ ] E-01 Implement `WorktreeContext` in `agent_workflows/worktree_containment.py` integrating with `orchestrate_isolation.py` to allocate clean, isolated worktrees and acquire single-writer path leases before mutation starts.
  - Depends on: none
  - Expected outcome: Mutating actions run in an isolated worktree; coordinator-owned paths and non-leased paths are protected.
  - Execution state: pending

### Task group 2: Deterministic containment transaction

- [ ] E-02 Implement `contain_item_failure()` in `agent_workflows/worktree_containment.py` executing the 7-step containment transaction (terminate worker, freeze/hash quarantine bundle, restore baseline, verify clean worktree, release leases).
  - Depends on: E-01
  - Expected outcome: Out-of-scope changes or failed validation restore isolated worktree to baseline with `contained: true` evidence, allowing independent queue items to proceed.
  - Execution state: pending

- [ ] E-03 Implement the exhaustive 6-class `ABORT RUN` classifier in `agent_workflows/worktree_containment.py` (corrupt ledger, lease conflict, unknown outcome, push attempt, hook bypass, identity ambiguity).
  - Depends on: E-02
  - Expected outcome: Only the 6 enumerated fatal classes abort the full run; all other failures remain item-local.
  - Execution state: pending

### Task group 3: Commit gateway and trailers

- [ ] E-04 Implement `CommitGateway` in `agent_workflows/commit_gateway.py` executing path-scoped `git commit -- <paths>` with appended `AW-Run: <run-id>` and `AW-Item: <id6>` trailers while respecting commit hooks and conventional commit syntax.
  - Depends on: E-01
  - Expected outcome: Commits are created only by the engine gateway, scoped to action-owned paths, with verifiable run/item trailers.
  - Execution state: pending

### Task group 4: Runner integration

- [ ] E-05 Integrate worktree isolation, containment rollback, and commit gateway into `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: Runner executes items in confined worktrees, invokes commit gateway for lifecycle transitions, and executes containment on check failures.
  - Execution state: pending

### Task group 5: Test suite coverage

- [ ] E-06 Create `tests/test_fault_containment.py` covering worktree allocation, baseline restoration on scope violation, quarantine hashing, abort classification, and commit trailer formatting.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: Full pytest suite passes with comprehensive fault containment and commit gateway coverage.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `orchestrate_isolation.py` defines the canonical worktree lease manager for parallel lanes.
- Commit trailers must follow Git trailer conventions (`Key: Value` at the end of the commit body, separated by a blank line).

## Findings

- If an agent modifies an out-of-scope file today, the runner aborts without cleanly isolating and rolling back the untracked or modified files created in that turn.

## Proposed changes (ordered, validatable)

1. Implement `WorktreeContext` in `worktree_containment.py` (E-01).
2. Implement 7-step `contain_item_failure()` transaction (E-02).
3. Implement 6-class `ABORT RUN` classifier (E-03).
4. Implement `CommitGateway` with `AW-Run:`/`AW-Item:` trailers (E-04).
5. Integrate with runner dispatch loop (E-05).
6. Cover with unit and integration tests (E-06).

## Deferred / out of scope (with reason)

- **Skeptical verifier session launch**: Deferred to child plan `detrun-05` (`7f7782`).
- **Ledger hash chaining**: Deferred to child plan `detrun-05` (`7f7782`).

## Scope check

- Over-scope: none. Strictly implements worktree isolation, containment, and commit gateway mechanics.
- Under-scope: none. Covers all 7 steps of the containment transaction and the 6 abort classes.

## Required tests / validation

- `python3 -m pytest tests/test_fault_containment.py` passing.
- Test demonstrating out-of-scope change quarantined and restored with independent item succeeding.

## Spec / documentation sync

- Implements spec `25kzda` (`20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`) Sections 4.1, 4.2, 5.1, and 5.7.
- Documents commit trailers and fault containment in `.aw/records/plans/README.md`.

## Open questions

### OQ-01: Does containment delete untracked files created by other processes?

- Blocking: no
- Status: resolved
- Owner: resolved from spec 25kzda Section 4.1
- Resolution or deferral rationale: RESOLVED - No. Containment removes only untracked paths proven to have been created by the specific item in its isolated worktree; main worktree paths and pre-existing files are never touched.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Python test showing worktree creation, lease acquisition, and lease release.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Test session showing out-of-scope mutation rolled back to baseline with `contained: true` recorded in output.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Test demonstrating only the 6 fatal classes aborting the run, with other failures cascading item-locally.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Git log of test commit showing correctly formatted `AW-Run:` and `AW-Item:` trailers and path-scoped contents.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: End-to-end runner test with a simulated scope violation verifying containment and subsequent queue progress.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `pytest tests/test_fault_containment.py` passing with test counts pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
