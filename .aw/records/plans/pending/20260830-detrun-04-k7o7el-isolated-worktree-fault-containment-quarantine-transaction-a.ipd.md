# IPD: Isolated worktree fault containment, quarantine transaction, and commit gateway trailers

- Date: 2026-08-30
- Kind: child
- Concern: Worktree mutation failures currently risk leaving dirty paths in the main working tree or aborting entire multi-item runs rather than containing errors item-locally.
- Scope: Implement worktree allocation with path leases, the 7-step deterministic containment transaction for failed/out-of-scope mutations, the quarantine bundle directory, the exhaustive 6-class `ABORT RUN` engine, and the commit gateway appending `AW-Run:` and `AW-Item:` trailers. Implements spec 25kzda Sections 4.1, 4.2, 5.1, and 5.7.
- Scope-Paths: agent_workflows/worktree_containment.py, agent_workflows/commit_gateway.py, agent_workflows/orchestrate_isolation.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_fault_containment.py
- Item-Dependencies: executed:kaygwo
- Status: reviewed
- Set: detrun
- Order: 4
- Highest E allocated: 07
- Author: antigravity
- Id: k7o7el
- Blocks-Release: next

## Workflow history
- 2026-08-30 /plan-review (OpenCode its_direct/pt3-claude-opus-5-1m-us): PR-006 fix. Normalized this history block to NEWEST-FIRST, the order `ipd_lifecycle._plan_status_events` assumes (it reverses to derive oldest-first). As authored the block was oldest-first, so the derived event stream read `to-review -> draft` and `aw check plans` reported `check.lifecycle-transition-invalid` ("backwards transition") on all 6 detrun plans. Verified pre-existing at pre-review commit `d4d265b6` (6 findings) and 0 after this fix. Content of every entry is unchanged; only line order.
- 2026-08-30 reviewed (aw set): plan-review: REJECT - NEEDS REPLAN (most of Set already shipped; collides with 3 approved Sets)
- 2026-08-30 /plan-review (OpenCode its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN; PR-001/PR-003. E-01 duplicates the APPROVED 7-plan `wtiso` Set and the shipped `orchestrate_isolation.py` (1152 lines) that this plan's own conventions section names as the canonical lease manager. E-05 collides with APPROVED `rununify` (`5e4sb6`). Depends on child 03, itself REPLAN. Genuine residue: the `AW-Run:`/`AW-Item:` trailers (zero hits today) plus CommitGateway, and the 7-step containment transaction / 6-class abort classifier, as an EXTENSION of `orchestrate_isolation.py`. Gate closed. NO-GO.
- 2026-08-30 to-review (antigravity): deepened 7-step containment transaction, quarantine bundle hashing, abort escalation rules, and commit gateway trailers.
- 2026-08-30 to-review (antigravity): authored from approved spec 25kzda (20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md).
- 2026-08-30 draft (antigravity): created.

## Goal

**REPLAN - DO NOT EXECUTE (/plan-review 2026-08-30, PR-001/PR-003 BLOCKER).** Verified at HEAD
`d4d265b6`:

- E-01 (`WorktreeContext`, worktree allocation, path leases) overlaps the entire APPROVED `wtiso` Set
  (7 plans, `bl9q3d` orchestrator), which owns worktree isolation and the driver-owned control plane,
  and the shipped `agent_workflows/orchestrate_isolation.py` (1152 lines), which already provides lane
  requests, concurrency-conflict detection, isolation contexts, host isolation capabilities, and an
  integration gate. This plan's own `## Project conventions discovered` even names
  `orchestrate_isolation.py` as "the canonical worktree lease manager", yet E-01 proposes a new
  `worktree_containment.py` to do it again.
- E-05 integrates into BOTH `oc_runipd.py` and `agy_runipd.py`, fighting `rununify` (`5e4sb6`,
  approved). See parent-Set OQ-03.
- The plan claims `Item-Dependencies: executed:kaygwo`, so it inherits every blocker of child 03.

What IS genuinely unbuilt and worth keeping: the `AW-Run:`/`AW-Item:` commit trailers (E-04) grep to
ZERO hits in `agent_workflows/`, and the `CommitGateway` that emits them is real, needed work; the
7-step containment transaction (E-02) and the 6-class `ABORT RUN` classifier (E-03) are specified
precisely in spec 25kzda 4.1 and are not obviously shipped. That residue should EXTEND
`orchestrate_isolation.py` and the shipped ledger, be reconciled with `wtiso` ownership, and be
sequenced after `rununify` so trailers are added once to a unified runner rather than twice.

Original goal, retained for the record: provide a robust worktree isolation and fault-containment
system that isolates mutations, quarantines and rolls back out-of-scope or failed item mutations,
restricts run aborts to six fatal integrity violations, and formats commit trailers immutably.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Worktree allocation and path lease management

- [ ] E-01 Implement `WorktreeContext` in `agent_workflows/worktree_containment.py` integrating with `orchestrate_isolation.py` to allocate clean, isolated worktrees under `.aw/state/worktrees/` and acquire single-writer path leases before mutation starts.
  - Depends on: none
  - Expected outcome: Mutating actions run in an isolated worktree; coordinator-owned paths and non-leased paths are protected.
  - Execution state: pending

### Task group 2: Deterministic containment transaction

- [ ] E-02 Implement `contain_item_failure()` in `agent_workflows/worktree_containment.py` executing the 7-step containment transaction (terminate worker, freeze/hash quarantine bundle, restore baseline, verify clean worktree, release leases).
  - Depends on: E-01
  - Expected outcome: Out-of-scope changes or failed validation restore isolated worktree to baseline with `contained: true` evidence, writing `.aw/records/runs/<run-id>/quarantine/<item-id6>/` bundle, allowing independent queue items to proceed.
  - Execution state: pending

- [ ] E-03 Implement the exhaustive 6-class `ABORT RUN` classifier and containment escalation engine in `agent_workflows/worktree_containment.py` (corrupt ledger, lease conflict, unknown outcome, push attempt, hook bypass, identity ambiguity).
  - Depends on: E-02
  - Expected outcome: Only the 6 enumerated fatal classes abort the full run; containment failures escalate to `ownership_conflict` or `unknown_outcome` when baseline restoration cannot be proven.
  - Execution state: pending

### Task group 3: Commit gateway and trailers

- [ ] E-04 Implement `CommitGateway` in `agent_workflows/commit_gateway.py` executing path-scoped `git commit -- <paths>` with appended `AW-Run: <run-id>` and `AW-Item: <id6>` trailers while respecting commit hooks and conventional commit syntax.
  - Depends on: E-01
  - Expected outcome: Commits are created only by the engine gateway, scoped to action-owned paths, with verifiable run/item trailers separated by a blank line at the end of the commit body.
  - Execution state: pending

### Task group 4: Runner integration

- [ ] E-05 Integrate worktree isolation, containment rollback, and commit gateway into `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: Runner executes items in confined worktrees, invokes commit gateway for lifecycle transitions, and executes containment on check failures.
  - Execution state: pending

### Task group 5: Test suite coverage and edge cases

- [ ] E-06 Create `tests/test_fault_containment.py` covering worktree allocation, baseline restoration on scope violation, quarantine bundle generation, abort classification, and commit trailer formatting.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: Full pytest suite passes with comprehensive fault containment and commit gateway coverage.
  - Execution state: pending

- [ ] E-07 Add adversarial containment tests: pre-existing dirty file conflict, untracked file deletion safety, containment escalation on failed rollback, and trailer formatting with multiline commit bodies.
  - Depends on: E-06
  - Expected outcome: All adversarial edge case tests assert correct containment receipts and fail-closed escalation.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `orchestrate_isolation.py` defines the canonical worktree lease manager for parallel lanes.
- Commit trailers must follow Git trailer conventions (`Key: Value` at the end of the commit body, separated by a blank line).
- Quarantine bundles live under `.aw/records/runs/<run-id>/quarantine/<item-id6>/`.

## Findings

- If an agent modifies an out-of-scope file today, the runner aborts without cleanly isolating and rolling back the untracked or modified files created in that turn.
- A failed containment must escalate to a run-wide abort rather than risking corrupted workspace state.

## Proposed changes (ordered, validatable)

1. Implement `WorktreeContext` in `worktree_containment.py` (E-01).
2. Implement 7-step `contain_item_failure()` transaction and quarantine bundles (E-02).
3. Implement 6-class `ABORT RUN` classifier and escalation (E-03).
4. Implement `CommitGateway` with `AW-Run:`/`AW-Item:` trailers (E-04).
5. Integrate with runner dispatch loop (E-05).
6. Cover with comprehensive unit and adversarial tests in `test_fault_containment.py` (E-06, E-07).

## Deferred / out of scope (with reason)

- **Skeptical verifier session launch**: Deferred to child plan `detrun-05` (`7f7782`).
- **Ledger hash chaining**: Deferred to child plan `detrun-05` (`7f7782`).

## Scope check

- Over-scope: none. Strictly implements worktree isolation, containment, and commit gateway mechanics.
- Under-scope: none. Covers all 7 steps of the containment transaction, quarantine bundles, and the 6 abort classes.

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
  - Required evidence: Test session showing out-of-scope mutation rolled back to baseline with `contained: true` and quarantine bundle written to disk.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Test demonstrating only the 6 fatal classes aborting the run, with other failures cascading item-locally, and escalation on failed restoration.
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

- [ ] V-07 validates E-07
  - Required evidence: Adversarial test suite asserting clean rollback and escalation on simulated dirty state conflicts.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

**GATE: CLOSED. `REJECT - NEEDS REPLAN` (/plan-review 2026-08-30).** Do NOT execute and do NOT approve.
E-01 duplicates the approved `wtiso` Set and the shipped `orchestrate_isolation.py`; E-05 collides with
approved Set `rununify` (`5e4sb6`); the plan depends on child 03, which is itself REPLAN. Blocked by
parent-Set OQ-03. See `## Goal`. An executor reaching this gate must STOP and report. Retire with the
parent Set `detrun` (`r4mbcw`); do not file under `executed/`. The commit-trailer/gateway work (E-04)
and the containment transaction (E-02/E-03) are the salvageable residue.
