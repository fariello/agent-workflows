# IPD: Item-dependencies syntax parser, pure graph evaluator, and phased check/lint rules

- Date: 2026-08-30
- Kind: child
- Concern: Cross-item prerequisite relationships currently rely on implicit Set/Order sequencing or prose rather than an explicit, machine-enforced graph.
- Scope: Implement the mandatory id6-grounded `Item-Dependencies` metadata grammar, pure shared DAG evaluator, the 6 stable `check.ipd-dependency-*` rules in `check_engine.py`, phased `ipd_lint.py` enforcement, the `aw ipd dependencies set` CLI tool, and the opt-in `ipd-dependency-statement-gate` commit hook. Implements spec 25kzda Sections 2.7-2.11 and 4.3.
- Scope-Paths: agent_workflows/artifact_dependencies.py, agent_workflows/ipd_schema.py, agent_workflows/ipd_lint.py, agent_workflows/check_engine.py, agent_workflows/engine.py, agent_workflows/cli.py, tests/test_item_dependencies.py
- Item-Dependencies: none
- Status: to-review
- Set: detrun
- Order: 1
- Highest E allocated: 08
- Author: antigravity
- Id: bmh754
- Blocks-Release: next

## Workflow history

- 2026-08-30 draft (antigravity): created.
- 2026-08-30 to-review (antigravity): authored from approved spec 25kzda (20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md).

## Goal

Provide a single, pure, canonical `Item-Dependencies` parser and graph evaluator that enforces explicit prerequisite edges across IPDs, specs, and backlog items, ensuring no IPD can be reviewed or executed with missing, malformed, cyclic, or unsatisfied prerequisites.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Grammar parser and canonical serialization

- [ ] E-01 Create `agent_workflows/artifact_dependencies.py` implementing the canonical `Item-Dependencies` grammar parser and serializer supporting `none`, `executed:<id6>`, `exists:<type>:<id6>`, and `state:<type>:<status>:<id6>` with strict canonical sort ordering.
  - Depends on: none
  - Expected outcome: Parser parses valid edges into typed dataclasses, validates id6 alphabet (6 lowercase chars), checks legal types and status tokens, rejects duplicates and self-edges, and round-trips through serializer.
  - Execution state: pending

- [ ] E-02 Add metadata recognition for `Item-Dependencies` in `agent_workflows/ipd_schema.py` and wire metadata parser to `artifact_dependencies.py`.
  - Depends on: E-01
  - Expected outcome: `ipd_schema.py` accepts `Item-Dependencies` as a valid recognized metadata field immediately following `Scope-Paths`.
  - Execution state: pending

### Task group 2: Pure shared graph evaluator and consistency rules

- [ ] E-03 Implement `evaluate_item_dependencies()` in `agent_workflows/artifact_dependencies.py`: a pure, shared graph evaluator that resolves references against a repository snapshot or staged overlay, constructs a directed graph, detects cycles using Tarjan's/Kosaraju's SCC algorithm, and evaluates edge satisfaction.
  - Depends on: E-01
  - Expected outcome: Evaluator returns structured findings for missing, unresolved, malformed, dangling, ambiguous, and cyclic dependency statements.
  - Execution state: pending

- [ ] E-04 Register the 6 stable dependency rules in `agent_workflows/check_engine.py` (`check.ipd-missing-dependency-statement`, `check.ipd-dependency-unresolved`, `check.ipd-dependency-malformed`, `check.ipd-dependency-dangling`, `check.ipd-dependency-ambiguous`, `check.ipd-dependency-cycle`) delegating directly to the shared evaluator.
  - Depends on: E-03
  - Expected outcome: `aw check plans` and `aw check all` evaluate repository-wide IPD dependencies and emit deterministic findings with exact recovery commands.
  - Execution state: pending

### Task group 3: Phased linting and grandfathering cutover

- [ ] E-05 Integrate `Item-Dependencies` validation into `agent_workflows/ipd_lint.py` across author, review-readiness, pre-execution, and pre-transition phases, honoring grandfathering rules for pre-cutover terminal plans.
  - Depends on: E-03
  - Expected outcome: `unresolved` is advisory at author phase but blocking at review-readiness/pre-execution; missing field on post-cutover plans is an error; pre-cutover terminal plans in `executed/` receive grandfathered advisory.
  - Execution state: pending

### Task group 4: Tooling and pre-commit hook

- [ ] E-06 Add the `aw ipd dependencies set <selector> <edges...>` command in `agent_workflows/cli.py` and `agent_workflows/ipd_cli.py`.
  - Depends on: E-01, E-03
  - Expected outcome: Setter validates input, writes canonical metadata line, appends workflow history receipt, and runs shared evaluator before committing path-scoped changes.
  - Execution state: pending

- [ ] E-07 Add the opt-in `ipd-dependency-statement-gate` local pre-commit hook in `agent_workflows/engine.py` and wire `aw hooks install ipd-dependency-statement-gate`.
  - Depends on: E-03
  - Expected outcome: Pre-commit hook checks staged `.ipd.md` files against HEAD overlay, preventing invalid or cyclic dependency edits from being committed.
  - Execution state: pending

### Task group 5: Test suite coverage

- [ ] E-08 Create `tests/test_item_dependencies.py` covering parser round-trips, canonical sorting, satisfaction semantics, cycle detection, dangling links, phased linting, grandfathering, setter CLI, and pre-commit hook.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: Comprehensive test suite passes with full branch coverage.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `ipd_schema.META_RECOGNIZED` contains recognized front-matter fields; `Item-Dependencies` must be recognized as valid optional/required metadata directly after `Scope-Paths`.
- `check_engine.py` registers rules via `RuleSpec` table with unique identifiers, severity levels, and descriptive messages; all 6 dependency rules must be added there.
- Grandfathering precedent: `Scope-Paths: grandfathered` or cutoff-commit checks allow existing terminal plans to pass lint while requiring active plans to conform.

## Findings

- Prerequisite execution between child plans currently depends on sequential Set/Order numbering; an out-of-order dependency or cross-set prerequisite cannot be explicitly stated.
- `ipd_lint.py` and `check_engine.py` have no mechanism to detect circular dependencies between plans or verify that prerequisite artifacts are executed before execution begins.

## Proposed changes (ordered, validatable)

1. Add pure parser/serializer in `agent_workflows/artifact_dependencies.py` (E-01).
2. Register `Item-Dependencies` in `ipd_schema.py` (E-02).
3. Implement pure DAG evaluator and cycle detector (E-03).
4. Register the 6 `check.ipd-dependency-*` rules in `check_engine.py` (E-04).
5. Add phased validation in `ipd_lint.py` (E-05).
6. Implement `aw ipd dependencies set` CLI (E-06).
7. Implement opt-in pre-commit hook in `engine.py` (E-07).
8. Cover everything with comprehensive tests in `test_item_dependencies.py` (E-08).

## Deferred / out of scope (with reason)

- **Source-side dependencies on specs and backlog items**: Deferred per spec Section 2.8; specs and backlog items serve as targets in v1.
- **DAG queue scheduling and execution**: Deferred to child plan `detrun-03` (`kaygwo`).

## Scope check

- Over-scope: none. Strictly implements the `Item-Dependencies` data layer, rules, and linter gates.
- Under-scope: none. All 6 rules from spec Section 2.10 are implemented and tested.

## Required tests / validation

- `python3 -m pytest tests/test_item_dependencies.py` passing.
- `python3 -m agent_workflows.cli check plans` passing.
- `python3 -m agent_workflows.cli ipd lint --phase author <path>` passing.

## Spec / documentation sync

- Implements spec `25kzda` (`20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`) Sections 2.7-2.11 and 4.3.
- Updates `.aw/records/plans/README.md` to document the `Item-Dependencies` metadata field syntax and rules.

## Open questions

### OQ-01: Should `executed:<id6>` accept an executed plan whose status text says executed but lacks valid finalization evidence?

- Blocking: no
- Status: resolved
- Owner: resolved from spec 25kzda Section 2.7
- Resolution or deferral rationale: RESOLVED - No. `executed:<id6>` requires both status `executed` in `executed/` AND valid finalization/terminal lint evidence. Mere status text without valid location/evidence fails satisfaction.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Python test showing parser accepting all 4 edge types, canonical sorting, and rejecting invalid tokens.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pytest showing `ipd_schema.py` recognizing `Item-Dependencies` without `IPD-M103` unknown field error.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Test session demonstrating cycle detection (2-node and 3-node cycles) and satisfaction checking for `executed:`, `exists:`, and `state:`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `aw check plans` output demonstrating all 6 `check.ipd-dependency-*` rules firing appropriately on synthetic fixtures.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `aw ipd lint` runs across author, review-readiness, pre-execution, and pre-transition showing expected error/advisory dispositions.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: CLI session running `aw ipd dependencies set` on a test plan, verifying resulting file format and workflow history.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Hook execution test showing `ipd-dependency-statement-gate` blocking a cyclic commit and permitting a valid commit.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: `pytest tests/test_item_dependencies.py` passing with test counts pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
