# IPD: Multi-type selector resolution, mixed-type gate, and DAG queue scheduler

- Date: 2026-08-30
- Kind: child
- Concern: `runipd` currently only resolves and executes single IPDs or IPD queues, without support for specs, backlog items, prompt files, or DAG dependency topological scheduling.
- Scope: Implement multi-type selector resolution across all 7 canonical artifact types, the mixed-type confirmation gate, the unified per-type dispatch table, and the pure DAG queue scheduler with dependency-not-met cascade. Implements spec 25kzda Sections 2.1-2.6, 3.1-3.6, and 5.4.
- Scope-Paths: agent_workflows/run_selector.py, agent_workflows/run_scheduler.py, agent_workflows/run_dispatch.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_run_selector_and_queue.py
- Item-Dependencies: executed:bmh754, executed:a54m79
- Status: reviewed
- Set: detrun
- Order: 3
- Highest E allocated: 08
- Author: antigravity
- Id: kaygwo
- Blocks-Release: next

## Workflow history
- 2026-08-30 reviewed (aw set): plan-review: REJECT - NEEDS REPLAN (most of Set already shipped; collides with 3 approved Sets)

- 2026-08-30 draft (antigravity): created.
- 2026-08-30 to-review (antigravity): authored from approved spec 25kzda (20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md).
- 2026-08-30 to-review (antigravity): deepened selector precedence, mixed-type confirmation, dispatch handlers, tiebreaking rules, and DAG cascade algorithms.
- 2026-08-30 /plan-review (OpenCode its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN; PR-001/PR-003. Least-duplicated child but still not executable: E-05/E-06 duplicate APPROVED `lanetruth-03` (`8guhs0`), which explicitly owns runner consumption of the shared dependency predicate and the 25kzda 2.9/5.4 runtime satisfaction semantics; a DAG release surface also ships (`run_engine.get_runnable_steps`, run_engine.py:273). E-07 collides with APPROVED `rununify` (`5e4sb6`). The three proposed `run_*` modules were authored without inventorying the ELEVEN shipped `run_*` modules. Salvageable residue: E-01..E-04 (multi-type selector, mixed-type gate, dispatch table). Gate closed. NO-GO.

## Goal

**REPLAN - DO NOT EXECUTE (/plan-review 2026-08-30, PR-001/PR-003 BLOCKER).** This is the LEAST
duplicated child of the Set and the most salvageable, but it is still not executable as written.
Verified at HEAD `d4d265b6`:

- E-05/E-06 (DAG queue scheduler and dependency-not-met cascade) collide with `lanetruth-03`
  (`8guhs0`), which is APPROVED and explicitly owns making runner preflight consume the SHARED
  `Item-Dependencies` predicate and implementing the spec 25kzda 2.9/5.4 runtime satisfaction
  semantics in `oc_runipd.py`/`agy_runipd.py`. That plan's Concern notes the runner currently freezes
  every queue item with `dependencies: []`. Two approved plans must not implement one behavior.
  A shipped DAG release surface also already exists (`run_engine.get_runnable_steps`,
  `agent_workflows/run_engine.py:273`).
- E-07 integrates into BOTH `oc_runipd.py` and `agy_runipd.py`, fighting `rununify` (`5e4sb6`,
  approved). See parent-Set OQ-03.
- The three new modules (`run_selector.py`, `run_scheduler.py`, `run_dispatch.py`) must be reconciled
  with the ELEVEN shipped `run_*` modules the Set never inventoried (`run_engine`, `run_state`,
  `run_ledger_schema`, `run_ledger_store`, `run_evidence`, `run_freeze`, `run_gates`, `run_packet`,
  `run_recovery`, `run_cli`, `run_viewer`). `run_scheduler.py` in particular overlaps `run_engine.py`.

What IS genuinely unbuilt and worth keeping: E-01..E-04, the multi-type selector resolution across the
7 canonical artifact types, the mixed-type confirmation gate, and the per-type/status dispatch table
including the spec-to-IPD and backlog-graduation handoffs. A replacement plan should keep those, drop
E-05/E-06 to `lanetruth-03`, and sequence E-07 after `rununify`.

Original goal, retained for the record: provide the core selector resolution, dispatch, and DAG
scheduling layer for `aw <host> run`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Multi-type selector resolution and mixed-type gate

- [ ] E-01 Create `agent_workflows/run_selector.py` implementing pure multi-type selector resolution across all 7 canonical artifact types (`ipd`, `spec`, `backlog`, `prompt`, `research`, `release`, `walkthrough`).
  - Depends on: none
  - Expected outcome: Resolution applies canonical precedence (path, id6, set, status, stem, substring), enforces `all` default (IPDs only unless `--type` specified), rejects ambiguous unique selectors (exit 4), handles zero matches (exit 2), and deduplicates by `(type, stable_id, canonical_path)`.
  - Execution state: pending

- [ ] E-02 Implement the mixed-type confirmation gate in `agent_workflows/run_selector.py` and wire into CLI runner entry points.
  - Depends on: E-01
  - Expected outcome: Prints sorted item count and action breakdown preview; requires exact `run mixed` confirmation interactively and `--allow-mixed` in unattended mode, refusing work with `[RUN-MIXED-TYPES]` if unconfirmed.
  - Execution state: pending

### Task group 2: Per-type and status dispatch table

- [ ] E-03 Create `agent_workflows/run_dispatch.py` implementing the complete per-type lifecycle dispatch table from spec Section 3 for IPDs, specs, backlog items, prompt files, and non-runnable records.
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
  - Expected outcome: Constructs frozen queue DAG, evaluates runtime edge satisfaction, sorts ready items (dependency depth, type rank `spec`->`backlog`->`ipd`->`prompt`, Set, Order, id6), and yields actionable items sequentially.
  - Execution state: pending

- [ ] E-06 Implement the deterministic dependency failure cascade in `agent_workflows/run_scheduler.py`.
  - Depends on: E-05
  - Expected outcome: When a prerequisite item fails, is capability-refused, or stops for input, direct and transitive dependents are marked `skipped` / `dependency_not_met` recording full root cause chains (`root_causes`, `blocking_dependency`, `chain`), while independent items continue.
  - Execution state: pending

### Task group 4: Runner integration and flags

- [ ] E-07 Integrate selector resolution, dispatching, and DAG scheduling into `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`, supporting `--full-auto`, `--unattended`, `--with-dependencies`, and `--follow-generated`.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06
  - Expected outcome: Runners execute multi-item queues with full flag parity across interactive and unattended modes.
  - Execution state: pending

### Task group 5: Test suite coverage and edge cases

- [ ] E-08 Create `tests/test_run_selector_and_queue.py` covering resolution precedence, mixed-type confirmation, dispatch actions, spec/backlog handoffs, DAG topological scheduling, tiebreaking rules, and cascade propagation.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: Full pytest suite passes with comprehensive coverage across all selector and queue scheduling paths.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Precedence ordering: path -> id6 -> set -> status -> stem -> substring is the house standard across all `aw find` and selector commands.
- Type rankings for scheduler tiebreaking: `spec`, `backlog`, `ipd`, `prompt`.
- `--with-dependencies` expands the selection to the transitive declared dependency closure before freezing.

## Findings

- Currently `oc_runipd.py` and `agy_runipd.py` assume all queue items are IPDs and order queue items solely by filename sort order.
- Closing a backlog item `done` when its plans exist drops the release gate; the scheduler must enforce the `graduated` terminal state on graduation.

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
  - Required evidence: Test showing DAG queue scheduler executing independent nodes in correct topological priority order with tiebreaking rules.
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

**GATE: CLOSED. `REJECT - NEEDS REPLAN` (/plan-review 2026-08-30).** Do NOT execute and do NOT approve.
E-05/E-06 duplicate approved plan `lanetruth-03` (`8guhs0`); E-07 collides with approved Set `rununify`
(`5e4sb6`); the three proposed `run_*` modules were authored without inventorying the eleven shipped
ones. Blocked by parent-Set OQ-03. See `## Goal`. An executor reaching this gate must STOP and report.
Retire with the parent Set `detrun` (`r4mbcw`); do not file under `executed/`. E-01..E-04 are the
salvageable residue and should be re-cut into a smaller plan.
