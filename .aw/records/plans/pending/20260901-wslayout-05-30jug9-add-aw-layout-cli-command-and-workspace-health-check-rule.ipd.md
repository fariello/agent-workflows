# IPD: Add aw layout CLI command and workspace health check rule

- Date: 2026-09-01
- Kind: child
- Concern: Workspace layout inspection needs a dedicated CLI verb (`aw layout`) and workspace health check in `aw check` per Spec kw5y2s.
- Scope: Add `aw layout` command (supporting `--json`, `--schema`) to `agent_workflows/cli.py`, add layout consistency checking to `check_engine.py` / `doctor.py`, and author unit tests in `tests/test_cli_layout.py`.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/check_engine.py, agent_workflows/doctor.py, tests/test_cli_layout.py
- Item-Dependencies: none
- Status: to-review
- Set: wslayout
- Order: 5
- Highest E allocated: 03
- Author: antigravity
- Id: 30jug9
- From-Spec: kw5y2s

## Workflow history

- 2026-09-01 draft (antigravity): created child plan.
- 2026-09-01 to-review (antigravity): authored complete plan.

## Goal

Provide user-facing and agent-facing inspection via `aw layout` and automated health verification during `aw check`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an E-* item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: CLI Verb Implementation

- [ ] E-01 Add `layout` subcommand to `agent_workflows/cli.py` supporting `--json`, `--schema`, and formatted human inspection.
  - Depends on: none
  - Expected outcome: `aw layout` command works in human and agent modes.
  - Execution state: pending

### Task group 2: Workspace Health Check

- [ ] E-02 Add layout verification rule (`check.system-layout-missing` / `check.system-layout-drift`) to `agent_workflows/check_engine.py` and `doctor.py`.
  - Depends on: E-01
  - Expected outcome: `aw check` verifies that installed `.aw/system/layout.json` exists and is valid.
  - Execution state: pending

### Task group 3: Unit Tests

- [ ] E-03 Author unit tests in `tests/test_cli_layout.py` covering `aw layout`, `aw layout --json`, and `aw layout --schema`.
  - Depends on: E-01, E-02
  - Expected outcome: `pytest tests/test_cli_layout.py` passes cleanly.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_workflows/cli.py`: main CLI surface.
- `agent_workflows/check_engine.py`: consistency check engine.

## Findings

- `aw layout` provides direct stdout inspection without requiring non-Python tools to parse the filesystem if they choose to shell out.

## Proposed changes (ordered, validatable)

1. Add `layout` parser and runner in `agent_workflows/cli.py` (E-01).
2. Add check rule in `check_engine.py` (E-02).
3. Add unit test suite in `tests/test_cli_layout.py` (E-03).

## Deferred / out of scope (with reason)

- none.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `pytest tests/test_cli_layout.py` passing.
- Full repository test suite passing bare.

## Spec / documentation sync

- Implements Spec `kw5y2s` Section 6.2.

## Open questions

- none.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a V-* item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `aw layout --json` and `aw layout --schema` emit expected JSON documents.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `aw check` includes layout verification rule.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `pytest tests/test_cli_layout.py` passes cleanly.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
