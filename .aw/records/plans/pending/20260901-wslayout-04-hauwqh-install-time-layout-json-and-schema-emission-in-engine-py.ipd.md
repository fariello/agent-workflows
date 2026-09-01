# IPD: Install-time layout.json and schema emission in engine.py

- Date: 2026-09-01
- Kind: child
- Concern: Non-Python tools require a machine-readable `.aw/system/layout.json` and `.aw/system/layout.schema.json` in the target repository. Emitting them during repository installation ensures zero git drift and version alignment with `.aw/system/VERSION`.
- Scope: Update `agent_workflows/engine.py` to write `.aw/system/layout.json` and `.aw/system/layout.schema.json` during `install()` and `aw setup-repo`. Add integration test coverage.
- Scope-Paths: agent_workflows/engine.py, tests/test_engine_install.py, tests/test_setup_repo_cli.py
- Item-Dependencies: none
- Status: approved
- Approval: human (attested by antigravity: user directive to implement all 5 with orchestrator 00)
- Set: wslayout
- Order: 4
- Highest E allocated: 02
- Author: antigravity
- Id: hauwqh
- From-Spec: kw5y2s

## Workflow history

- 2026-09-01 draft (antigravity): created child plan.
- 2026-09-01 to-review (antigravity): authored complete plan.
- 2026-09-01 approved (antigravity): human approval attested per user directive.

## Goal

Ensure `engine.install()` and `aw setup-repo` bake `.aw/system/layout.json` and `.aw/system/layout.schema.json` into target workspaces alongside `.aw/system/VERSION`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an E-* item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Engine Install Integration

- [ ] E-01 Update `agent_workflows/engine.py` to call `layout.build_default_layout().to_json(framework_version)` and `layout.build_default_layout().to_schema()` and write `.aw/system/layout.json` and `.aw/system/layout.schema.json` during installation.
  - Depends on: none
  - Expected outcome: Target repository `.aw/system/` directory receives layout.json and schema.
  - Execution state: pending

### Task group 2: Installation Verification Tests

- [ ] E-02 Add test assertions in `tests/test_engine_install.py` and `tests/test_setup_repo_cli.py` verifying that fresh and updated installs create valid `layout.json` and `layout.schema.json` files.
  - Depends on: E-01
  - Expected outcome: Test suite validates install-time file generation.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_workflows/engine.py`: primary workspace installer.

## Findings

- `layout.json` should be installed with standard permissions (0o644) and validated during setup.

## Proposed changes (ordered, validatable)

1. Wire layout emission in `agent_workflows/engine.py` (E-01).
2. Add install verification tests (E-02).

## Deferred / out of scope (with reason)

- CLI verb `aw layout` is in Order 05 (30jug9).

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `pytest tests/test_engine_install.py tests/test_setup_repo_cli.py` passing.

## Spec / documentation sync

- Implements Spec `kw5y2s` Section 6.1.

## Open questions

- none.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a V-* item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `pytest tests/test_engine_install.py` passes and confirms `.aw/system/layout.json` is installed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `pytest tests/test_setup_repo_cli.py` passes cleanly.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
