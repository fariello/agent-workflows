# IPD: Host Session Adapters and Capability Gated Launchers

- Date: 2026-08-23
- Kind: child
- Concern: Launch structured fresh workers across coding hosts without duplicating semantics.
- Scope: Generic runner, OpenCode/Codex/Claude/Antigravity/Kiro/Gemini adapters, capability evidence, structured streams, and fresh verification.
- Status: to-review
- Set: execset
- Order: 4
- Highest E allocated: 03
- Author: OpenAI GPT 5.6 Sol
- Id: 31744f

## Workflow history
- 2026-08-23 to-review (aw set): Authored from current runtime, lifecycle, isolation, and cross-host capability research; ready for plan review.

- 2026-08-23 draft (OpenAI GPT 5.6 Sol): created from official host documentation and repository capability audit.

## Goal

Provide one evidence-gated worker interface that can start, monitor, resume, cancel, and verify isolated tasks on each supported host while keeping the Set coordinator authoritative.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Generic structured runner

- [ ] E-01 Implement `agent_workflows/host_runner.py` with bounded task packets, structured streaming, timeouts, cancellation, session identity, actual-diff capture, stderr/status parsing, and validated terminal envelopes; do not reuse benchmark live gates.
  - Depends on: none
  - Expected outcome: the coordinator receives facts, not free-form completion claims.
  - Execution state: pending

### Material change 2: Capability-gated adapters

- [ ] E-02 Add thin OpenCode, Codex, Claude Code, Antigravity/agy, Kiro, and Gemini launchers generated through existing adapter/shim code; advertise native subagents, model flags, resume, JSON, worktrees, or permissions only with current positive and fail-closed probe evidence.
  - Depends on: E-01
  - Expected outcome: unsupported/unverified capabilities use a safe external-process fallback or explicit refusal.
  - Execution state: pending

### Material change 3: Fresh verification and host tests

- [ ] E-03 Require distinct executor/verifier sessions, task-local resume for correction, host-specific greenwashing checks, exact model-role binding, and isolated positive/negative probes including the currently missing Kiro matrix row.
  - Depends on: E-02
  - Expected outcome: no same-session audit or host success exit can finalize work without evidence.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Extend `host_adapters.py`, `host_capability_registry.py`, and `engine.py` generators; do not fork wrapper generation.
- OpenCode and Codex are v1 skill targets; other hosts remain unverified until probes.
- `agy_run.py` same-conversation review is legacy and cannot be authoritative beside `agy_verifier.py`.
- Host native teams/subagents differ; set-level orchestration must not depend on them.

## Findings

OpenCode is strong for heterogeneous model routing but needs external worktree/integration control. Claude has mature subagents/worktrees/hooks but Agent Teams are experimental. Antigravity supports fresh asynchronous/branch workers, but soft-denied tools may still yield exit 0. Codex can use fresh `codex exec` sessions with external worktrees; native delegation remains capability-gated.

## Proposed changes (ordered, validatable)

Worker terminal states: `completed`, `deferred_partial`, `deferred_ipd`, `failed_retryable`, `failed_final`, `blocked_required_input`. Every result carries changed files, checks with exit/log evidence, decisions, questions, deferred scope, and blocking question. Workers cannot ask users directly.

Prefer one fresh process/session per lane; resume it for corrections; start a distinct clean verifier. The coordinator owns worktrees unless a probed native worktree mode is selected, never both.

## Deferred / out of scope (with reason)

- Host-native experimental team orchestration is optional acceleration only.
- Live paid-model benchmarks remain operator-run and separate.

## Scope check

- Over-scope: none.
- Under-scope: redact secrets/paths and bind any local server to loopback with authentication.

## Required tests / validation

Use model-free doubles plus isolated operator probes for missing binary, denied permissions, soft denial with exit 0, malformed output, timeout, lost background result, stale session, same-session verifier, path escape, server auth, and exact model routing.

## Spec / documentation sync

Generate the support matrix from unexpired evidence and document fallback behavior, not aspirational capability.

## Open questions

### OQ-01: One implementation per host?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: one semantic runner plus thin adapters; separate implementations would drift.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: runner-double tests prove malformed/free-form/timeout/success-without-diff outcomes cannot become completed.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: generated adapter and capability-fixture tests prove only unexpired positive probes advertise each feature, missing/negative evidence selects the documented safe fallback, and semantic digests remain in parity.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: executor and verifier session IDs differ; soft-denied exit-zero, malformed envelope, wrong model, missing diff/check, timeout, and stale-session fixtures all fail without terminal completion.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: exactly three changes build the runner, adapters, and independent verification proof.

Requires executed Order 03 and explicit approval. Do not run live models in agent-executed tests or claim support without current probe evidence.
