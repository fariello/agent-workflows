# IPD: Consolidate record_producers.py and project_schema.py into layout model

- Date: 2026-09-01
- Kind: child
- Concern: `record_producers.py` and `project_schema.py` maintain separate `RecordClass`, `DurableStateClass`, `RuntimeStateClass`, and subpath maps. Aligning them with `layout.py` removes duplication.
- Scope: Refactor `agent_workflows/record_producers.py` and `agent_workflows/project_schema.py` to source definitions from `agent_workflows/layout.py` while preserving existing exception types, class enums, and legacy migration path adapters.
- Scope-Paths: agent_workflows/record_producers.py, agent_workflows/project_schema.py
- Item-Dependencies: none
- Status: to-review
- Set: wslayout
- Order: 3
- Highest E allocated: 02
- Author: antigravity
- Id: rodj06
- From-Spec: kw5y2s

## Workflow history

- 2026-09-01 draft (antigravity): created child plan.
- 2026-09-01 to-review (antigravity): authored complete plan.
- 2026-09-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN (Set-level); see orchestrator rh5tt6 OQ-1/OQ-2 and review record 20260901-wslayout-00-rh5tt6-...review.md
  - PR-001 (drops root-level `records` class), PR-002 (tests/test_record_producers.py does not exist), PR-006, PR-007.

## Goal

Consolidate `record_producers.py` and `project_schema.py` to consume `layout.py` without breaking existing record routing, write guards, or migration retention.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an E-* item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Refactor record_producers.py

- [ ] E-01 Update `agent_workflows/record_producers.py` to align `RecordClass`, `DurableStateClass`, `RuntimeStateClass`, and `_RECORD_CLASS_SUBPATHS` with `layout.py` while preserving `_LEGACY_RECORD_CLASS_SUBPATHS` and existing write guard methods.
  - Depends on: none
  - Expected outcome: `record_producers.py` sources subpaths from the layout model.
  - Execution state: pending

### Task group 2: Refactor project_schema.py

- [ ] E-02 Align `LogicalRoot` and `RootClass` enums and constants in `agent_workflows/project_schema.py` with `layout.py`.
  - Depends on: E-01
  - Expected outcome: `project_schema.py` is in 100% sync with the canonical layout model.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_workflows/record_producers.py`: central record routing and write guard.
- `agent_workflows/project_schema.py`: canonical project schema vocabulary.

## Findings

- `_LEGACY_RECORD_CLASS_SUBPATHS` must be retained in `record_producers.py` for legacy `.agents/` migration reads (`resolve_record_read_paths`).

## Proposed changes (ordered, validatable)

1. Refactor `agent_workflows/record_producers.py` (E-01).
2. Refactor `agent_workflows/project_schema.py` (E-02).

## Deferred / out of scope (with reason)

- Install-time emission is in Order 04 (hauwqh).

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `pytest tests/test_record_producers.py tests/test_project_context.py` passing.

## Spec / documentation sync

- Implements Spec `kw5y2s` Section 5.1.

## Open questions

- none.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a V-* item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `pytest tests/test_record_producers.py` passes cleanly.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `pytest tests/test_project_context.py` passes cleanly.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
