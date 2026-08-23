# IPD: Parallel Scheduler Worktree Integration and Model Routing

- Date: 2026-08-23
- Kind: child
- Concern: Execute all provably independent Set work concurrently and integrate it safely.
- Scope: Coordinator, ready queue, path leases, worktrees, model roles, merge/revalidation, lifecycle, and resume.
- Status: to-review
- Set: execset
- Order: 3
- Highest E allocated: 03
- Author: OpenAI GPT 5.6 Sol
- Id: m2wwns

## Workflow history
- 2026-08-23 to-review (aw set): Authored from current runtime, lifecycle, isolation, and cross-host capability research; ready for plan review.

- 2026-08-23 draft (OpenAI GPT 5.6 Sol): created over existing run/isolation/recovery foundations.

## Goal

Implement the single-writer Set coordinator that schedules every safe lane, routes it to the right model role, integrates results deterministically, and resumes without replaying completed side effects.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Scheduler and model roles

- [ ] E-01 Implement `agent_workflows/ipd_set_executor.py` with a dependency-aware ready queue, `coding|human_prose|mixed|verifier` classification, configurable host/model bindings, robust-decision/defer handling, a write-ahead `decision_proposal -> coordinator record -> decision_authorized` worker handshake, and maximal batches approved by `analyze_concurrency_eligibility()`.
  - Depends on: none
  - Expected outcome: every ready node is running, deferred with a record, or deterministically serialized; none is silently ignored.
  - Execution state: pending

### Material change 2: Isolation and integration

- [ ] E-02 Allocate a fresh session and separate worktree for every write lane, enforce exclusive ownership leases, and integrate returned path-scoped commits in topological/IPD/lane order through `execute_merge_and_revalidate_gate()`.
  - Depends on: E-01
  - Expected outcome: no concurrent worker writes the coordinator checkout or an overlapping/shared surface.
  - Execution state: pending

### Material change 3: Lifecycle and recovery

- [ ] E-03 Drive pre-execution lint, per-node/IPD evidence, fresh verification, pre/post-transition gates, partial outcomes, crash recovery, answer/resume, evidence invalidation, and final combined-HEAD validation from the ledger.
  - Depends on: E-02
  - Expected outcome: executed IPDs transition truthfully; deferred IPDs remain pending; restart reconstructs state without duplicate effects.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Reuse `run_engine`, `run_state`, `run_packet`, `run_evidence`, `run_recovery`, `verify_roles`, `orchestrate_isolation`, and `ipd-lifecycle`; do not create a second engine.
- The current runtime mutates/inspects pre-created ledgers but lacks an end-to-end run creator and worker dispatcher.
- Coordinator/runtime alone may write authoritative ledger/IPD state and terminal transactions.

## Findings

Parallel mutation is safe only with worktrees, dependency independence, disjoint writes/generated/shared surfaces, exclusive leases, and full integrated revalidation. A worker's green tests or exit code do not prove the merged result.

## Proposed changes (ordered, validatable)

Routing rules: code/tests/config/schemas/APIs/comments/docstrings/CLI help/self-documentation/agent documentation use `coding`; website/marketing/policy/narrative human content uses `human_prose`; split `mixed` into technical-fact then prose lanes when possible; `verifier` is always a fresh context.

Workers never edit `events.jsonl`, source IPDs, history, backlog, walkthrough, or main worktree. They return commits and envelopes. A consultation-preferred choice pauses as a proposal; the coordinator records its disposition before authorizing mutation. Unexpected actual file overlap rejects/serializes integration and invalidates stale evidence.

## Deferred / out of scope (with reason)

- Remote multi-machine scheduling is deferred.
- Host process flags are Order 04.

## Scope check

- Over-scope: none.
- Under-scope: cap concurrency and resource use; timeouts/missing results are failures, never completion.

## Required tests / validation

Test full parallel waves, serial fallback, decision proposal/authorization and post-hoc rejection, overlap/path escape/shared surfaces, stale base, lane timeout, merge conflict, combined regression, mixed split, retries, crash/unknown outcome, lifecycle move, and partial Set completion.

## Spec / documentation sync

Document scheduling, lease, model-role, integration, and recovery contracts; generate run-state views from events.

## Open questions

### OQ-01: Should model IDs be hard-coded defaults?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: no. Store operator/host bindings in local configuration or CLI flags; evidence-backed examples may be suggested defaults only.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: scheduler tests show every node reaches a recorded running/deferred/serialized disposition and all provably safe lanes share a wave.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: concurrent fixture lanes use distinct worktrees and leases; overlapping or undeclared writes are rejected/serialized; commits integrate deterministically and the merged HEAD reruns affected checks.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: crash/resume fixtures reconstruct leases and node states without replay, invalidate stale evidence after integration, preserve deferred IPDs, and allow terminal transition only after fresh combined-HEAD verification.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: exactly three changes implement scheduling, isolation/integration, and lifecycle/recovery over one coordinator.

Requires executed Orders 01-02 and explicit approval. Never push, publish, deploy, or approve; never allow a worker to terminally transition its own IPD.
