# IPD: Per-host capability descriptor, probe harness, and fail-closed action gating

- Date: 2026-08-30
- Kind: child
- Concern: Runners currently assume host assistants (OpenCode, Antigravity) provide uniform execution, sandboxing, and isolation capabilities, which can lead to silent failure, unconfined mutations, or unverifiable execution on degraded hosts.
- Scope: Implement the `HostCapabilityDescriptor` schema, on-disk descriptor cache, live and mock probe harnesses for `oc` and `agy` (worktree isolation, commit gateway, push denial, session separation, argv capture, timeout), action-level capability requirement mapping, and the fail-closed `RUN-HOST-CAPABILITY` preflight gate. Implements spec 25kzda Sections 5.2 and 4.2.
- Scope-Paths: agent_workflows/host_capabilities.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/cli.py, tests/test_host_capabilities.py
- Item-Dependencies: executed:bmh754
- Status: reviewed
- Set: detrun
- Order: 2
- Highest E allocated: 07
- Author: antigravity
- Id: a54m79
- Blocks-Release: next

## Workflow history
- 2026-08-30 /plan-review (OpenCode its_direct/pt3-claude-opus-5-1m-us): PR-006 fix. Normalized this history block to NEWEST-FIRST, the order `ipd_lifecycle._plan_status_events` assumes (it reverses to derive oldest-first). As authored the block was oldest-first, so the derived event stream read `to-review -> draft` and `aw check plans` reported `check.lifecycle-transition-invalid` ("backwards transition") on all 6 detrun plans. Verified pre-existing at pre-review commit `d4d265b6` (6 findings) and 0 after this fix. Content of every entry is unchanged; only line order.
- 2026-08-30 reviewed (aw set): plan-review: REJECT - NEEDS REPLAN (most of Set already shipped; collides with 3 approved Sets)
- 2026-08-30 /plan-review (OpenCode its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN; PR-001/PR-002. E-01..E-03 largely duplicate the shipped `host_capability_registry.py` (1593 lines, TTL expiry, unverified default, fail-closed migration, degraded/fail-closed-verified states, 9-class negative probes). The typed host capability contract is ALSO claimed by APPROVED `wtiso-07` (`1o4eif`), so two approved plans would own one contract (BLOCKING OQ-02). E-05 adds code to both runners, fighting APPROVED `rununify` (`5e4sb6`) (BLOCKING OQ-03). Genuine residue: the runner-safety capability vocabulary (greps to zero hits) and the action-to-capability map with fail-closed preflight, as an EXTENSION of the shipped registry. Gate closed. NO-GO.
- 2026-08-30 to-review (antigravity): deepened probe specifications, mock injection harness, degraded assurance states, and CLI introspection.
- 2026-08-30 to-review (antigravity): authored from approved spec 25kzda (20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md).
- 2026-08-30 draft (antigravity): created.

## Goal

**REPLAN - DO NOT EXECUTE (/plan-review 2026-08-30, PR-001/PR-002 BLOCKER).** This plan is PARTLY
shipped and PARTLY owned by an approved sibling Set. Verified at HEAD `d4d265b6`:

- E-01 (descriptor schema, cache, TTL) and E-02/E-03 (positive and negative probe harnesses) largely
  duplicate the shipped `agent_workflows/host_capability_registry.py` (1593 lines, awoptimize Order
  `4fttzq`), which already provides a capability-evidence registry with an `unverified` default,
  TTL-based expiry (`DEFAULT_EVIDENCE_TTL_DAYS`), fail-closed migration from static matrices,
  `STATUS_DEGRADED`/`STATUS_FAIL_CLOSED_VERIFIED` states, secret redaction, host version detection,
  and a 9-class negative probe harness. Creating a new `host_capabilities.py` beside it would give the
  repo two capability registries (violates GUIDING_PRINCIPLES P8).
- The typed host capability contract plus fail-closed dispatch is ALSO explicitly claimed by
  `wtiso-07` (`1o4eif`), which is APPROVED. Two approved plans must not own one contract. This is
  BLOCKING open question OQ-02 on the parent Set and needs a maintainer decision.
- E-05 wires the preflight into BOTH `oc_runipd.py` and `agy_runipd.py`, which fights `rununify`
  (`5e4sb6`, approved), whose whole purpose is to collapse the ~93 percent duplication between those
  two files. Sequencing is BLOCKING open question OQ-03 on the parent Set.

What IS genuinely unbuilt and worth keeping: the runner-safety capability VOCABULARY
(`isolated_worktree`, `commit_gateway`, `deny_push`, `fresh_verifier_session`, `argv_capture`,
`timeout_cancel`) greps to ZERO hits anywhere in `agent_workflows/`, so the shipped registry does not
cover these specific guarantees; and the action-to-capability requirement map (E-04) with its
fail-closed `RUN-HOST-CAPABILITY` preflight is real, needed work. That residue should EXTEND the
shipped registry rather than replace it, and only after OQ-02 assigns ownership.

Original goal, retained for the record: provide a rigorous per-host capability descriptor and probe
system that evaluates whether an agent host (`oc` or `agy`) can enforce required safety guarantees
before starting work, failing closed item-locally when required guarantees cannot be proven.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Capability descriptor data model and storage

- [ ] E-01 Create `agent_workflows/host_capabilities.py` defining `HostCapability`, `CapabilityAssurance`, `HostCapabilityEntry`, and `HostCapabilityDescriptor` with atomic serialization and cache persistence at `.aw/state/host_capabilities.json`.
  - Depends on: none
  - Expected outcome: Dataclasses serialize to/from JSON, compute cryptographic evidence digests, enforce TTL/staleness checks (default 24h), record positive/negative probe results, and support thread-safe cache reads/writes.
  - Execution state: pending

### Task group 2: Probe harness for OpenCode and Antigravity

- [ ] E-02 Implement probe runners in `agent_workflows/host_capabilities.py` for standard execution guarantees: `isolated_worktree`, `commit_gateway`, `deny_push`, `fresh_verifier_session`, `argv_capture`, and `timeout_cancel` for both OpenCode and Antigravity.
  - Depends on: E-01
  - Expected outcome: Probe suite executes active and synthetic verification checks against the local host installation, recording positive/negative results and evidence hashes in the descriptor.
  - Execution state: pending

- [ ] E-03 Implement a mock probe injection harness in `agent_workflows/host_capabilities.py` to allow testing degraded, unsupported, and expired host capability scenarios in unit and integration test suites without live binaries.
  - Depends on: E-02
  - Expected outcome: Test harnesses can inject synthetic capability states to verify fail-closed execution paths deterministically.
  - Execution state: pending

### Task group 3: Action requirements and fail-closed preflight

- [ ] E-04 Define the action capability requirement mapping table (`ACTION_REQUIRED_CAPABILITIES`) and implement `check_action_capabilities(host, version, mode, action)` in `agent_workflows/host_capabilities.py`.
  - Depends on: E-01, E-02
  - Expected outcome: Action types (read-only classification, review, authoring, execution, contract prompt, contractless prompt) declare exact required host guarantees and evaluate against the cached descriptor.
  - Execution state: pending

- [ ] E-05 Wire the `RUN-HOST-CAPABILITY` preflight check into `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`.
  - Depends on: E-04
  - Expected outcome: Runner evaluates host descriptor before spawning executor session; unproven or stale capabilities fail item-locally with `host_capability_unavailable` without aborting independent items.
  - Execution state: pending

### Task group 4: CLI and probe management

- [ ] E-06 Add `aw host probe <host>` and `aw host capabilities [host]` commands to `agent_workflows/cli.py`.
  - Depends on: E-01, E-02
  - Expected outcome: Users and automated runners can inspect host capability status, trigger on-demand re-probing, and view evidence digests in human table or JSON format.
  - Execution state: pending

### Task group 5: Test suite coverage

- [ ] E-07 Create `tests/test_host_capabilities.py` covering descriptor schema, cache TTL/staleness, mock and live probes, action requirement mapping, fail-closed preflight refusal, degraded capability handling, and CLI commands.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06
  - Expected outcome: Full pytest suite passes with 100% branch coverage on capability evaluation logic.
  - Execution state: pending

## Project conventions discovered (Step 0)

- State directory: `.aw/state/` is gitignored and stores local runner state, caches, and process locks.
- Fail-closed principle: a missing, expired, or failed capability probe must never be treated as supported.
- Capability assurance levels: `hardened` (enforced at OS/tool level), `mediated` (enforced via driver interception), `observed` (verified via empirical tests).

## Findings

- `oc_runipd.py` and `agy_runipd.py` currently assume the host environment supports worktree isolation and full subshell capture without verifying the host binary's actual runtime capabilities.
- Different host versions and run modes (e.g. OpenCode CLI vs server, Antigravity CLI vs IDE) provide asymmetric security and sandboxing primitives.

## Proposed changes (ordered, validatable)

1. Implement `HostCapabilityDescriptor` and cache storage in `host_capabilities.py` (E-01).
2. Implement probe harnesses for `oc` and `agy` (E-02).
3. Implement mock probe injection harness for testing (E-03).
4. Implement action requirement mapping and preflight check (E-04).
5. Integrate preflight into runner dispatch loops (E-05).
6. Add CLI inspection/probing commands (E-06).
7. Cover with comprehensive tests in `test_host_capabilities.py` (E-07).

## Deferred / out of scope (with reason)

- **Kernel-level eBPF sandboxing**: Hardware/kernel sandboxing is an OS-level concern; host capability probes verify tool policy denial and credential withholding at the agent execution boundary.
- **DAG queue cascade logic**: Propagating `host_capability_unavailable` skips down the dependency graph is implemented in child plan `detrun-03` (`kaygwo`).

## Scope check

- Over-scope: none. Strictly implements host capability detection and action-level gating.
- Under-scope: none. Covers both OpenCode and Antigravity hosts across all action types and capability dimensions.

## Required tests / validation

- `python3 -m pytest tests/test_host_capabilities.py` passing.
- `aw host capabilities oc` and `aw host capabilities agy` returning structured table.

## Spec / documentation sync

- Implements spec `25kzda` (`20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`) Section 5.2.
- Updates runner documentation to describe capability probing, cache TTLs, and troubleshooting missing guarantees.

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
  - Required evidence: Test verifying mock probe injection allowing synthetic degraded or missing capabilities in test environments.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Truth table test verifying action requirement matching across all action types and capability combinations.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Test running runner with missing capability fixture, verifying item fails with `RUN-HOST-CAPABILITY` and independent items continue.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: CLI session showing `aw host capabilities` and `aw host probe` formatting human-readable and JSON output.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: `pytest tests/test_host_capabilities.py` passing with test counts pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

**GATE: CLOSED. `REJECT - NEEDS REPLAN` (/plan-review 2026-08-30).** Do NOT execute and do NOT approve.
Blocked by parent-Set open questions OQ-02 (who owns the host capability contract: this Set,
`wtiso-07`, or the shipped registry) and OQ-03 (sequencing against `rununify`), both of which require a
maintainer decision. See `## Goal` for evidence. An executor reaching this gate must STOP and report.
Retire with the parent Set `detrun` (`r4mbcw`); do not file under `executed/`.
