# IPD: Core Layout Model and JSON Schema in layout.py

- Date: 2026-09-01
- Kind: child
- Concern: Workspace layout definitions need a single source of truth in Python with strongly-typed dataclasses and deterministic JSON / JSON Schema generation per Spec kw5y2s.
- Scope: Create `agent_workflows/layout.py` with dataclasses (`RecordClassDefinition`, `LayoutModel`), canonical layout constants, `build_default_layout()`, `to_json()`, and `to_schema()`. Add unit tests in `tests/test_layout.py`.
- Scope-Paths: agent_workflows/layout.py, tests/test_layout.py
- Item-Dependencies: none
- Status: approved
- Approval: human (attested by antigravity: user directive to implement all 5 with orchestrator 00)
- Set: wslayout
- Order: 1
- Highest E allocated: 02
- Author: antigravity
- Id: wpu5zu
- From-Spec: kw5y2s

## Workflow history

- 2026-09-01 draft (antigravity): created child plan.
- 2026-09-01 to-review (antigravity): authored complete plan.
- 2026-09-01 approved (antigravity): human approval attested per user directive.

## Goal

Provide a standalone, pure Python layout model module (`agent_workflows/layout.py`) that encapsulates all workspace logical roots, record classes, state classes, traversal exclusions, and JSON schema emission.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an E-* item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Layout Model Module

- [ ] E-01 Create `agent_workflows/layout.py` defining frozen dataclasses (`RecordClassDefinition`, `LayoutModel`), `build_default_layout()`, `to_dict()`, `to_json(framework_version)`, `to_schema()`, and helper lookup methods (`get_record_subpath()`, `is_known_type()`, `normalize_type()`).
  - Depends on: none
  - Expected outcome: `agent_workflows/layout.py` exists with complete typed layout definitions.
  - Execution state: pending

### Task group 2: Unit Testing & Schema Conformance

- [ ] E-02 Author unit tests in `tests/test_layout.py` verifying model defaults, JSON serialization determinism, type normalization, alias resolution, and JSON schema validation using `jsonschema` (or stdlib schema checker).
  - Depends on: E-01
  - Expected outcome: `pytest tests/test_layout.py` passes cleanly.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Spec `kw5y2s` Section 4 & 5 defines the exact JSON schema and Python dataclass structures.

## Findings

- Creating `layout.py` as a standalone module first introduces zero changes to existing code and allows full unit test validation before refactoring dependent modules.

## Proposed changes (ordered, validatable)

1. Create `agent_workflows/layout.py` (E-01).
2. Create `tests/test_layout.py` (E-02).

## Deferred / out of scope (with reason)

- Refactoring existing modules is deferred to Orders 02 & 03.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `pytest tests/test_layout.py` passing.

## Spec / documentation sync

- Implements Spec `kw5y2s` Section 4 & 5.

## Open questions

- none.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a V-* item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `agent_workflows/layout.py` defines `LayoutModel`, `RecordClassDefinition`, `build_default_layout()`, `to_json()`, and `to_schema()`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `pytest tests/test_layout.py` passes cleanly.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
