# IPD: Multi-type selector resolution, mixed-type gate, and DAG queue scheduler

- Date: 2026-08-30
- Kind: child
- Concern: `runipd` currently only resolves and executes single IPDs or IPD queues, without support for specs, backlog items, prompt files, or DAG dependency topological scheduling.
- Scope: Implement multi-type selector resolution across all 7 canonical artifact types, the mixed-type confirmation gate, the unified per-type dispatch table, and the pure DAG queue scheduler with dependency-not-met cascade. Implements spec 25kzda Sections 2.1-2.6, 3.1-3.6, and 5.4.
- Scope-Paths: agent_workflows/run_selector.py, agent_workflows/run_scheduler.py, agent_workflows/run_dispatch.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_run_selector_and_queue.py
- Item-Dependencies: executed:bmh754, executed:a54m79
- Status: to-review
- Set: detrun
- Order: 3
- Highest E allocated: 08
- Author: antigravity
- Id: kaygwo
- Blocks-Release: next

## Workflow history

- 2026-08-30 draft (antigravity): created.
- 2026-08-30 to-review (antigravity): authored from approved spec 25kzda (20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md).

## Goal

Provide the core selector resolution, dispatch, and DAG scheduling layer for `aw <host> run` that parses work items across all artifact types, enforces interactive/unattended mixed-type gates, executes ready items in dependency order, and cascades failure skips deterministically.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Multi-type selector resolution and mixed-type gate

- [ ] E-01 Create `agent_workflows/run_selector.py` implementing pure multi-type selector resolution across all 7 canonical artifact types (`ipd`, `spec`, `backlog`, `prompt`, `research`, `release`, `walkthrough`).
  - Depends on: none
  - Expected outcome: Resolution applies canonical precedence (path, id6, set, status, stem, substring), enforces `all` default (IPDs only unless `--type` specified), rejects ambiguous unique selectors, and deduplicates by identity.
  - Execution state: pending

- [ ] E-02 Implement the mixed-type confirmation gate in `agent_workflows/run_selector.py` and wire into CLI runner entry points.
  - Depends on: E-01
  - Expected outcome: Prints sorted item count and action breakdown preview; requires exact `run mixed` confirmation interactively and `--allow-mixed` in unattended mode.
  - Execution state: pending

### Task group 2: Per-type and status dispatch table

- [ ] E-03 Create `agent_workflows/run_dispatch.py` implementing the complete per-type lifecycle dispatch table from spec Section 3.
  - Depends on: E-01
  - Expected outcome: Evaluates item type and status to choose next legal action packet, handling IPD review/execute, spec review/authoring, backlog graduation, prompt contract verification, and non-runnable skips.
  - Execution state: pending

- [ ] E-04 Implement spec IPD-authoring action (`approved` spec -> author `to-review` IPD with `From-Spec: <id6>` and `Blocks-Release`) and backlog graduation action (`open` backlog -> author spec/IPD with `From-Backlog: <id6>` -> `graduated`).
  - Depends on: E-03
  - Expected outcome: Handoffs generate conformant artifacts, preserve release blocker gates, and perform atomic tool-authored status transitions.
  - Execution state: pending

### Task group 3: Pure DAG queue scheduler and cascade engine

- [ ] E-05 Create `agent_workflows/run_scheduler.py` implementing the pure DAG queue scheduler driven by declared `Item-Dependencies`.
  - Depends on: E-01, E-03
  - Expected outcome: Constructs frozen queue DAG, evaluates runtime edge satisfaction, sorts ready items (dependency depth, type rank, Set, Order, id6), and yields actionable items sequentially.
  - Execution state: pending

- [ ] E-06 Implement the deterministic dependency failure cascade in `agent_workflows/run_scheduler.py`.
  - Depends on: E-05
  - Expected outcome: When a prerequisite item fails, is capability-refused, or stops for input, direct and transitive dependents are marked `skipped` / `dependency_not_met` recording full root cause chains, while independent items continue.
  - Execution state: pending

### Task group 4: Runner integration and flags

- [ ] E-07 Integrate selector resolution, dispatching, and DAG scheduling into `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`, supporting `--full-auto`, `--unattended`, `--with-dependencies`, and `--follow-generated`.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06
  - Expected outcome: Runners execute multi-item queues with full flag parity across interactive and unattended modes.
  - Execution state: pending

### Task group 5: Test suite coverage

- [ ] E-08 Create `tests/test_run_selector_and_queue.py` covering resolution precedence, mixed-type confirmation, dispatch actions, spec/backlog handoffs, DAG topological scheduling, and cascade propagation.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: Full pytest suite passes with comprehensive coverage across all selector and queue scheduling paths.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Precedence ordering: path -> id6 -> set -> status -> stem -> substring is the house standard across all `aw find` and selector commands.
- Type rankings for scheduler tiebreaking: `spec`, `backlog`, `ipd`, `prompt`.

## Findings

- Currently `oc_runipd.py` and `agy_runipd.py` assume all queue items are IPDs and order queue items solely by filename sort order.

## Proposed changes (ordered, validatable)

1. Implement multi-type selector resolution in `run_selector.py` (E-01).
2. Implement mixed-type gate and preview (E-02).
3. Implement dispatch table in `run_dispatch.py` (E-03).
4. Implement spec-to-IPD and backlog graduation dispatch handlers (E-04).
5. Implement DAG queue scheduler in `run_scheduler.py` (E-05).
6. Implement dependency failure cascade (E-06).
7. Wire scheduler into runner entry points (E-07).
8. Cover with comprehensive tests in `test_run_selector_and_queue.py` (E-08).

## Deferred / out of scope (with reason)

- **Isolated worktree management**: Deferred to child plan `detrun-04` (`k7o7el`).
- **Deterministic verification checker**: Deferred to child plan `detrun-05` (`7f7782`).

## Scope check

- Over-scope: none. Strictly implements selector resolution, dispatch routing, and DAG queue scheduling.
- Under-scope: none. All 7 artifact types and dispatch rules from spec Section 3 are covered.

## Required tests / validation

- `python3 -m pytest tests/test_run_selector_and_queue.py` passing.
- `aw oc run all --type ipd --type spec` displaying mixed-type preview.

## Spec / documentation sync

- Implements spec `25kzda` (`20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`) Sections 2.1-2.6, 3.1-3.6, and 5.4.
- Updates CLI help text for `aw oc run` and `aw agy run`.

## Open questions

### OQ-01: Does `--with-dependencies` add dependencies of already satisfied external prerequisites?

- Blocking: no
- Status: resolved
- Owner: resolved from spec 25kzda Section 2.1
- Resolution or deferral rationale: RESOLVED - `--with-dependencies` expands the selection to the transitive dependency closure before freezing; items already satisfied in the repository are evaluated and marked satisfied without re-executing.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Python test verifying selector resolution matching exact paths, id6, set, status, and rejecting ambiguous IDs.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Test verifying interactive `run mixed` requirement and unattended `--allow-mixed` refusal.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Dispatch table unit tests verifying correct action packet emitted for each type/status combination.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Test showing spec authoring an IPD carrying `From-Spec` and backlog graduation setting `graduated`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Test showing DAG queue scheduler executing independent nodes in correct topological priority order.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Test showing a failed parent node cascading `dependency_not_met` to descendants while independent branches finish.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: End-to-end runner test executing a 3-item multi-type queue under `--full-auto`.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: `pytest tests/test_run_selector_and_queue.py` passing with test counts pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
