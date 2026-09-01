# IPD: Consolidate artifact_types.py and selectors.py into layout model

- Date: 2026-09-01
- Kind: child
- Concern: `artifact_types.py` and `selectors.py` maintain separate hardcoded sets of artifact types, aliases, and excluded directories. Sourcing them from `layout.py` removes duplication while maintaining exact backward compatibility.
- Scope: Refactor `agent_workflows/artifact_types.py` and `agent_workflows/selectors.py` to import constants and helper logic from `agent_workflows/layout.py`.
- Scope-Paths: agent_workflows/artifact_types.py, agent_workflows/selectors.py
- Item-Dependencies: none
- Status: approved
- Approval: human (attested by antigravity: user directive to implement all 5 with orchestrator 00)
- Set: wslayout
- Order: 2
- Highest E allocated: 02
- Author: antigravity
- Id: zvk796
- From-Spec: kw5y2s

## Workflow history

- 2026-09-01 draft (antigravity): created child plan.
- 2026-09-01 to-review (antigravity): authored complete plan.
- 2026-09-01 approved (antigravity): human approval attested per user directive.

## Goal

Consolidate `artifact_types.py` and `selectors.py` to consume the single source of truth in `layout.py` without breaking any existing imports or tests.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an E-* item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Refactor artifact_types.py

- [ ] E-01 Update `agent_workflows/artifact_types.py` to derive `ARTIFACT_TYPES`, `_ALIASES`, `is_type_token()`, and `normalize_type()` directly from `agent_workflows/layout.py`, preserving all function signatures and exception types.
  - Depends on: none
  - Expected outcome: `artifact_types.py` re-exports the layout model definitions seamlessly.
  - Execution state: pending

### Task group 2: Refactor selectors.py

- [ ] E-02 Update `agent_workflows/selectors.py` to source `KNOWN_PRIMARY_TYPES` and `EXCLUDED_RECORD_DIRS` from `agent_workflows/layout.py`.
  - Depends on: E-01
  - Expected outcome: `selectors.py` uses the canonical layout exclusions and types.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_workflows/artifact_types.py`: closed TYPE-noun vocabulary.
- `agent_workflows/selectors.py`: shared selector resolver.

## Findings

- `artifact_types.py` is imported across the CLI and test suite; re-exporting ensures zero downstream breakage.

## Proposed changes (ordered, validatable)

1. Refactor `agent_workflows/artifact_types.py` (E-01).
2. Refactor `agent_workflows/selectors.py` (E-02).

## Deferred / out of scope (with reason)

- Refactoring `record_producers.py` and `project_schema.py` is in Order 03 (rodj06).

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `pytest tests/test_awcmdsurf_vocab_and_parsers.py tests/test_selector_resolver_matrix.py` passing.

## Spec / documentation sync

- Implements Spec `kw5y2s` Section 5.1.

## Open questions

- none.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a V-* item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `pytest tests/test_awcmdsurf_vocab_and_parsers.py` passes cleanly.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `pytest tests/test_selector_resolver_matrix.py` passes cleanly.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
