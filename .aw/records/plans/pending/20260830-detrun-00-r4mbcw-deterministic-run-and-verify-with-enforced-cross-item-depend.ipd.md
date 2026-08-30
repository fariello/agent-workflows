# IPD: Deterministic run-and-verify with enforced cross-item dependencies and fault containment

- Date: 2026-08-30
- Kind: orchestrator
- Concern: Runner consolidation, multi-type selector resolution, mandatory cross-item `Item-Dependencies` graph enforcement, fail-closed per-host capability gating, worktree fault containment, and deterministic completion verification.
- Scope: Orchestrates the 5 child implementation plans of Set `detrun` implementing approved spec `25kzda` (`20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`). Defines the child plan sequence, dependency graph, integration validation, and Set completion criteria.
- Scope-Paths: agent_workflows/**, tests/**, .aw/records/specs/**
- Item-Dependencies: none
- Status: to-review
- Set: detrun
- Order: 0
- Highest E allocated: 05
- Author: antigravity
- Id: r4mbcw
- Blocks-Release: next

## Workflow history

- 2026-08-30 draft (antigravity): created.
- 2026-08-30 to-review (antigravity): authored from approved spec 25kzda (20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md).
- 2026-08-30 to-review (antigravity): deepened edge case integration, verification evidence matrices, and Set-level validation.

## Goal

Provide the single canonical, deterministic runner verb (`aw oc run` / `aw agy run`) that resolves typed work items, builds and validates their cross-item `Item-Dependencies` DAG, enforces fail-closed host capability guarantees, isolates mutations in disposable worktrees, captures tamper-evident run ledgers, and authorizes completions through deterministic repository checks rather than agent self-reported prose. Implements approved spec `25kzda`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Set orchestration and sequence verification

- [ ] E-01 Execute and verify child plan `detrun-01` (`bmh754`): `Item-Dependencies` syntax parser, pure graph evaluator, and phased check/lint rules.
  - Depends on: none
  - Expected outcome: `Item-Dependencies` grammar (`none`, `executed:<id6>`, `exists:<type>:<id6>`, `state:<type>:<status>:<id6>`) and `From-Spec` link metadata are enforced across `check_engine.py`, `ipd_lint.py`, `aw ipd dependencies set`, and the opt-in commit hook `ipd-dependency-statement-gate`.
  - Execution state: pending

- [ ] E-02 Execute and verify child plan `detrun-02` (`a54m79`): Per-host capability descriptor, probe harness, and fail-closed action gating.
  - Depends on: E-01
  - Expected outcome: `host_capabilities.py` defines positive/fail-closed probe harnesses for OpenCode (`oc`) and Antigravity (`agy`), enforcing action-level capability requirements (`RUN-HOST-CAPABILITY`) with item-local refusal.
  - Execution state: pending

- [ ] E-03 Execute and verify child plan `detrun-03` (`kaygwo`): Multi-type selector resolution, mixed-type gate, and DAG queue scheduler.
  - Depends on: E-01, E-02
  - Expected outcome: Unified `aw <host> run` resolves items across all 7 types (`ipd`, `spec`, `backlog`, `prompt`, `research`, `release`, `walkthrough`), enforces the `run mixed` confirmation gate, and executes ready items in pure DAG topological order with dependency-not-met cascading.
  - Execution state: pending

- [ ] E-04 Execute and verify child plan `detrun-04` (`k7o7el`): Isolated worktree fault containment, quarantine transaction, and commit gateway trailers.
  - Depends on: E-03
  - Expected outcome: Worktree allocation isolates item changes; out-of-scope mutations trigger deterministic containment (quarantine bundle hashing + baseline restoration) without aborting independent items; commits carry immutable `AW-Run:` and `AW-Item:` trailers.
  - Execution state: pending

- [ ] E-05 Execute and verify child plan `detrun-05` (`7f7782`): Fresh skeptical verifier session, tamper-evident run ledger, and deterministic completion checker.
  - Depends on: E-04
  - Expected outcome: Fresh verifier session executes without inherited memory; deterministic checker validates all 13 common checks; append-only ledger verifies run integrity; exit code policy and `--unverifiable-ok` aggregate neutrality are enforced.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | Plan File | What it does | Item-Dependencies |
|---|---|---|---|---|
| 01 | `bmh754` | `20260830-detrun-01-bmh754-item-dependencies-syntax-parser-pure-graph-evaluator-and-pha.ipd.md` | `Item-Dependencies` syntax parser, graph evaluator, `From-Spec` links, phased checks, and setter | `none` |
| 02 | `a54m79` | `20260830-detrun-02-a54m79-per-host-capability-descriptor-probe-harness-and-fail-closed.ipd.md` | Per-host capability descriptor, probe harnesses (`oc`/`agy`), and fail-closed preflight | `executed:bmh754` |
| 03 | `kaygwo` | `20260830-detrun-03-kaygwo-multi-type-selector-resolution-mixed-type-gate-and-dag-queue.ipd.md` | Multi-type selector resolution, mixed-type confirmation gate, and DAG queue scheduler | `executed:bmh754`, `executed:a54m79` |
| 04 | `k7o7el` | `20260830-detrun-04-k7o7el-isolated-worktree-fault-containment-quarantine-transaction-a.ipd.md` | Worktree isolation, fault containment transaction, and commit gateway trailers | `executed:kaygwo` |
| 05 | `7f7782` | `20260830-detrun-05-7f7782-fresh-skeptical-verifier-session-tamper-evident-run-ledger-a.ipd.md` | Skeptical verifier turn, tamper-evident run ledger, and deterministic completion checker | `executed:k7o7el` |

## Completion criteria (the whole Set is done only when)

- All 5 child IPDs are verified `executed` in `.aw/records/plans/executed/`.
- `aw <host> run` resolves IPDs, specs, backlog items, and prompts with deterministic verification.
- `Item-Dependencies` is enforced across `aw check`, `aw ipd lint`, commit hooks, and runner preflight.
- Full pytest test suite passes with zero regressions.
- `aw check all` and `aw sanitize --agent` report clean repository state.

## Cross-IPD validation

- Spec `25kzda` (`20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`) is linked and cited across all child plans.
- Release blocker `- Blocks-Release: next` is preserved across all plans.
- DAG dependency edges between child plans are satisfied sequentially.

## Deferred / out of scope (with reason)

- **Source-side dependency declarations for specs and backlog items**: Spec Section 2.8 explicitly defers source-side `Item-Dependencies` for specs and backlog items to future designs (they serve as targets in v1).
- **Authenticated cryptographic human signatures**: Spec Section 6.1 clarifies that named human approver signatures are an operational extension; `--by-human` attestation remains the speed bump in v1.

## Scope check

- Over-scope: none. All deliverables map 1:1 to approved spec `25kzda`.
- Under-scope: none. All 6 sections of the spec are partitioned across the 5 child plans.

## Required tests / validation

- `python3 -m pytest` full test suite passing with pasted counts.
- `python3 -m agent_workflows.cli check all` passing.
- `python3 -m agent_workflows.cli sanitize --agent` passing.

## Open questions

### OQ-01: How should the dependency-schema cutover commit be configured in the test harness?

- Blocking: no
- Status: resolved
- Owner: resolved from spec 25kzda Section 2.11
- Resolution or deferral rationale: RESOLVED - Use `agent_workflows/config.py` with a helper `dependency_schema_cutover_commit()` that resolves from `.aw/config/project.json` (or defaults to HEAD if unset), allowing unit tests to inject arbitrary mock cutover commits.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste execution receipt of `detrun-01` (`bmh754`) in `executed/` and pytest run for `tests/test_item_dependencies.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste execution receipt of `detrun-02` (`a54m79`) in `executed/` and pytest run for `tests/test_host_capabilities.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste execution receipt of `detrun-03` (`kaygwo`) in `executed/` and pytest run for `tests/test_run_selector_and_queue.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste execution receipt of `detrun-04` (`k7o7el`) in `executed/` and pytest run for `tests/test_fault_containment.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste execution receipt of `detrun-05` (`7f7782`) in `executed/` and pytest run for `tests/test_deterministic_checker.py`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
