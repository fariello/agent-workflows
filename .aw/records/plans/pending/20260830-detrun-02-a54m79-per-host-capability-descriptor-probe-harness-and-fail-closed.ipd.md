# IPD: Per-host capability descriptor, probe harness, and fail-closed action gating

- Date: 2026-08-30
- Kind: child
- Concern: Runners currently assume host assistants (OpenCode, Antigravity) provide uniform execution, sandboxing, and isolation capabilities, which can lead to silent failure or unverifiable execution on degraded hosts.
- Scope: Implement the `HostCapabilityDescriptor` schema, on-disk descriptor cache, live/mock probe harnesses for `oc` and `agy`, action-level capability requirement mapping, and the fail-closed `RUN-HOST-CAPABILITY` preflight gate. Implements spec 25kzda Sections 5.2 and 4.2.
- Scope-Paths: agent_workflows/host_capabilities.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_host_capabilities.py
- Item-Dependencies: executed:bmh754
- Status: to-review
- Set: detrun
- Order: 2
- Highest E allocated: 06
- Author: antigravity
- Id: a54m79
- Blocks-Release: next

## Workflow history

- 2026-08-30 draft (antigravity): created.
- 2026-08-30 to-review (antigravity): authored from approved spec 25kzda (20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md).

## Goal

Provide a rigorous per-host capability descriptor and probe system that evaluates whether an agent host (`oc` or `agy`) can enforce required safety guarantees (worktree isolation, commit gateway, push denial, session separation) before starting work, failing closed item-locally when required guarantees cannot be proven.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Capability descriptor data model and storage

- [ ] E-01 Create `agent_workflows/host_capabilities.py` defining `HostCapability`, `CapabilityAssurance`, `HostCapabilityEntry`, and `HostCapabilityDescriptor` with atomic serialization and cache persistence at `.aw/state/host_capabilities.json`.
  - Depends on: none
  - Expected outcome: Dataclasses serialize to/from JSON, compute cryptographic evidence digests, enforce TTL/staleness checks, and support thread-safe cache reads/writes.
  - Execution state: pending

### Task group 2: Probe harness for OpenCode and Antigravity

- [ ] E-02 Implement probe runners in `agent_workflows/host_capabilities.py` for standard execution guarantees: `isolated_worktree`, `commit_gateway`, `deny_push`, `fresh_verifier_session`, `argv_capture`, and `timeout_cancel` for both OpenCode and Antigravity.
  - Depends on: E-01
  - Expected outcome: Probe suite executes active and synthetic verification checks against the local host installation, recording positive/negative results and evidence hashes in the descriptor.
  - Execution state: pending

### Task group 3: Action requirements and fail-closed preflight

- [ ] E-03 Define the action capability requirement mapping table (`ACTION_REQUIRED_CAPABILITIES`) and implement `check_action_capabilities(host, version, mode, action)` in `agent_workflows/host_capabilities.py`.
  - Depends on: E-01, E-02
  - Expected outcome: Action types (review, author, execute, contractless prompt) declare exact required host guarantees and evaluate against the cached descriptor.
  - Execution state: pending

- [ ] E-04 Wire the `RUN-HOST-CAPABILITY` preflight check into `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`.
  - Depends on: E-03
  - Expected outcome: Runner evaluates host descriptor before spawning executor session; unproven or stale capabilities fail item-locally with `host_capability_unavailable` without aborting independent items.
  - Execution state: pending

### Task group 4: CLI and probe management

- [ ] E-05 Add `aw host probe <host>` and `aw host capabilities [host]` commands to `agent_workflows/cli.py`.
  - Depends on: E-01, E-02
  - Expected outcome: Users and automated runners can inspect host capability status, trigger on-demand re-probing, and view evidence digests.
  - Execution state: pending

### Task group 5: Test suite coverage

- [ ] E-06 Create `tests/test_host_capabilities.py` covering descriptor schema, cache TTL/staleness, mock and live probes, action requirement mapping, fail-closed preflight refusal, and CLI commands.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: Full pytest suite passes with 100% branch coverage on capability evaluation logic.
  - Execution state: pending

## Project conventions discovered (Step 0)

- State directory: `.aw/state/` is gitignored and stores local runner state, caches, and process locks.
- Fail-closed principle: a missing, expired, or failed capability probe must never be treated as supported.

## Findings

- `oc_runipd.py` and `agy_runipd.py` currently assume the host environment supports worktree isolation and full subshell capture without verifying the host binary's actual runtime capabilities.

## Proposed changes (ordered, validatable)

1. Implement `HostCapabilityDescriptor` and cache storage in `host_capabilities.py` (E-01).
2. Implement probe harnesses for `oc` and `agy` (E-02).
3. Implement action requirement mapping and preflight check (E-03).
4. Integrate preflight into runner dispatch loops (E-04).
5. Add CLI inspection/probing commands (E-05).
6. Cover with unit and integration tests (E-06).

## Deferred / out of scope (with reason)

- **Network-level hardware sandboxing**: Deep kernel/eBPF network sandboxing is an OS-level concern; host capability probes verify tool policy denial and credential withholding at the agent execution boundary.
- **DAG queue cascade logic**: Propagating `host_capability_unavailable` skips down the dependency graph is implemented in child plan `detrun-03` (`kaygwo`).

## Scope check

- Over-scope: none. Strictly implements host capability detection and action-level gating.
- Under-scope: none. Covers both OpenCode and Antigravity hosts across all action types.

## Required tests / validation

- `python3 -m pytest tests/test_host_capabilities.py` passing.
- `aw host capabilities oc` and `aw host capabilities agy` returning structured table.

## Spec / documentation sync

- Implements spec `25kzda` (`20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`) Section 5.2.
- Updates runner docs to describe capability probing and troubleshooting for missing guarantees.

## Open questions

### OQ-01: What is the default TTL for cached probe evidence?

- Blocking: no
- Status: resolved
- Owner: resolved from spec 25kzda Section 5.2
- Resolution or deferral rationale: RESOLVED - 24 hours default TTL, invalidated immediately if the host binary hash, version string, or configuration file changes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Python test showing `HostCapabilityDescriptor` serializing, deserializing, and enforcing TTL expiry.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Test execution showing probes running against mock/real host binaries and returning structured capability records.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Truth table test verifying action requirement matching across all action types and capability combinations.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Test running runner with missing capability fixture, verifying item fails with `RUN-HOST-CAPABILITY` and independent items continue.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: CLI session showing `aw host capabilities` and `aw host probe` formatting human-readable and JSON output.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `pytest tests/test_host_capabilities.py` passing with test counts pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
