# IPD: Parallel Scheduler Worktree Integration and Model Routing

- Date: 2026-08-23
- Kind: child
- Concern: Execute all provably independent Set work concurrently and integrate it safely.
- Scope: Coordinator, ready queue, path leases, worktrees, model roles, merge/revalidation, lifecycle, and resume.
- Status: approved
- Set: execset
- Order: 3
- Highest E allocated: 03
- Author: OpenAI GPT 5.6 Sol
- Id: m2wwns

## Workflow history
- 2026-08-24 approved (aw set, --by-human): status set to approved
- 2026-08-23 /plan-review focused (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (worktree/session allocation + per-path lease are net-new, not isolation-module reuse), PR-002 (ready queue must compose RunEngine.get_runnable_steps, not re-derive), PR-003 (integration-triggered evidence invalidation is net-new; reuse correction/invalidates_seq primitive), PR-004 (decision-handshake record kinds are Order 02's; consume not redefine), PR-005 (verifier fresh-context already exists; work-class classifier + bindings net-new), PR-006 (worker path-fencing enforcement is net-new). V-02/V-03 strengthened.
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-003 (OQ-02 human-resolved: keep exception-sized E-01, strengthen V-01 to independently verify scheduler, classifier, model routing, and decision handshake).
- 2026-08-23 to-review (aw set): Authored from current runtime, lifecycle, isolation, and cross-host capability research; ready for plan review.

- 2026-08-23 draft (OpenAI GPT 5.6 Sol): created over existing run/isolation/recovery foundations.

## Goal

Implement the single-writer Set coordinator that schedules every safe lane, routes it to the right model role, integrates results deterministically, and resumes without replaying completed side effects.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Scheduler and model roles

- [ ] E-01 Implement `agent_workflows/ipd_set_executor.py` with a dependency-aware ready queue, `coding|human_prose|mixed|verifier` classification, configurable host/model bindings, robust-decision/defer handling, a write-ahead `decision_proposal -> coordinator record -> decision_authorized` worker handshake, and maximal batches approved by `analyze_concurrency_eligibility()`.
  - Depends on: none
  - Note (verified - compose, do not re-derive; and cross-plan dependency): (1) READY QUEUE - `RunEngine.get_runnable_steps()` (`run_engine.py:273`) already computes DAG + gate readiness at step granularity; COMPOSE it and add the lane/wave batching that `analyze_concurrency_eligibility()` (which operates on `LaneRequest`s) needs - do NOT re-derive DAG readiness (two readiness computations would drift). (2) DECISION HANDSHAKE - the `decision_proposal`/`decision_authorized` records and the `investigator` role are NET-NEW ledger surface OWNED BY Order 02 (`3m4e54`, whose `RECORD_KINDS` is closed today); this E-01 CONSUMES those kinds and MUST NOT redefine them (hence `Depends on: Orders 01-02` at the gate). (3) VERIFIER - the `verifier` fresh-context is already satisfied by `agy_verifier.py` + `verify_roles.build_verifier_packet` (reuse it); only the `coding|human_prose|mixed` work-class classifier and the configurable work-class->host/model binding config are net-new (no runtime model-binding config exists today - fail closed on a missing binding per OQ-01).
  - Expected outcome: every ready node is running, deferred with a record, or deterministically serialized; none is silently ignored.
  - Execution state: pending

### Material change 2: Isolation and integration

- [ ] E-02 Allocate a fresh session and separate worktree for every write lane, enforce exclusive ownership leases, and integrate returned path-scoped commits in topological/IPD/lane order through `execute_merge_and_revalidate_gate()`.
  - Depends on: E-01
  - Note (verified - what is reuse vs net-new): the INTEGRATION is genuine reuse - `execute_merge_and_revalidate_gate()` (`orchestrate_isolation.py:947`) already merges in a caller-provided `merge_order`, rejects on conflict/file-overlap/scope-violation/stale-base, and reruns `full_validation_runner` on the combined HEAD (fails closed); consume its `IntegrationGateResult`. BUT the ALLOCATION and LEASING are NET-NEW: `orchestrate_isolation.py` only ANALYZES eligibility and CARRIES a caller-supplied `worktree_path`/`session_id` - it never creates a git worktree or session, and there is NO per-path exclusive-ownership lease (the only "lease" in the tree is the single-writer LEDGER lock `run_ledger_store.writer_lock`, a different concept). E-02 must build: (1) real `git worktree` create/teardown per write lane, (2) fresh session allocation, and (3) a per-path/per-lane exclusive-ownership lease primitive. Worker path-fencing (workers never touch events.jsonl/source IPDs/history/backlog/walkthrough/main worktree) is enforced BY this worktree isolation + lease and is likewise net-new (the return types model it but nothing fences a worker process today).
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

Workers never edit `events.jsonl`, source IPDs, history, backlog, walkthrough, or main worktree. They return commits and envelopes (reuse the existing `run_packet.StepOutcomeEnvelope` + `orchestrate_isolation` `HandoffPacket`/`LaneOutcome` descriptors - these already exist). A consultation-preferred choice pauses as a proposal; the coordinator records its disposition before authorizing mutation. Unexpected actual file overlap rejects/serializes integration and invalidates stale evidence. NOTE (verified): the merge gate already REJECTS on overlap/conflict, and the invalidation PRIMITIVE exists (`correction` with `invalidates_seq` in `run_recovery`, `run_freeze.Revision.invalidated_evidence`, and HEAD/worktree-bound evidence envelopes with `EV-STALE-HEAD`), but there is NO existing trigger that invalidates evidence ON integration overlap - wiring that invalidation to the integration path is NET-NEW work this plan owns (reuse the `correction`/`invalidates_seq` primitive; do not invent a parallel one).

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

### OQ-02: Is E-01 conceptually over-dense (should it be split)?

- Blocking: no
- Status: resolved
- Owner: human
- Resolution or deferral rationale: RESOLVED by human decision (2026-08-23, /plan-review): KEEP E-01 as one exception-sized item (its four parts - ready queue, classifier, model routing, decision handshake - share one data structure, so splitting them into independent passes would introduce integration seams and shared-state re-litigation that REDUCE execution fidelity). Instead, V-01 was strengthened to require INDEPENDENT, concrete evidence for each of the four bundled sub-deliverables (scheduler/queue, work-class classifier, model-role routing/bindings, and the write-ahead decision handshake), closing the greenwashing gap without fragmenting cohesive logic.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence (each sub-deliverable proven INDEPENDENTLY - E-01 is exception-sized and bundles four concerns; do not mark done without all four): (a) SCHEDULER/QUEUE: tests show every node reaches a recorded running/deferred/serialized disposition and all provably safe lanes share a wave; (b) WORK-CLASS CLASSIFIER: a fixture set exercises `coding|human_prose|mixed|verifier` classification and asserts the correct class per node (including a `mixed` split case); (c) MODEL-ROLE ROUTING/BINDINGS: a test proves each work class routes to its configured host/model binding (and that an absent binding fails closed rather than defaulting silently); (d) DECISION HANDSHAKE: a test proves the write-ahead `decision_proposal -> coordinator record -> decision_authorized` sequence - a worker mutation without a prior recorded authorization is rejected, and a consultation-preferred choice pauses as a proposal until the coordinator records disposition.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: concurrent fixture lanes use distinct worktrees and leases; overlapping or undeclared writes are rejected/serialized; commits integrate deterministically and the merged HEAD reruns affected checks. SPECIFICALLY: (a) a test proves a real `git worktree` is created per write lane and torn down, and that the per-path exclusive lease actually PREVENTS a second lane from claiming an owned path (net-new primitives, not just the eligibility analyzer); (b) a test drives `execute_merge_and_revalidate_gate()` and asserts its `IntegrationGateResult` rejects on conflict/overlap/scope-violation/stale-base and that a per-lane-green-but-combined-red case fails closed.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: crash/resume fixtures reconstruct leases and node states without replay (via `run_recovery.resume`, which fails closed on unknown outcomes rather than re-running), invalidate stale evidence after integration, preserve deferred IPDs, and allow terminal transition only after fresh combined-HEAD verification. SPECIFICALLY: a test proves the NET-NEW integration-triggered invalidation - after an integration that supersedes a prior HEAD, evidence bound to the stale HEAD is invalidated via a `correction`/`invalidates_seq` record (reused primitive) and cannot satisfy a later terminal transition.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: exactly three changes implement scheduling, isolation/integration, and lifecycle/recovery over one coordinator.

Requires executed Orders 01-02 and explicit approval. Never push, publish, deploy, or approve; never allow a worker to terminally transition its own IPD.
