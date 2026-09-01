# IPD: Update CLI output contract and aw find to emit plain token-efficient paths for discovery

- Date: 2026-09-01
- Kind: child
- Concern: For file path discovery (e.g. searching artifacts by id6, Set, or selector via `aw find`), wrapping outputs in verbose JSON schemas consumes excess tokens and LLM parsing effort. Plain, newline-delimited repo-relative paths are strictly more token-efficient and ergonomic for agents.
- Scope: Update `docs/cli-output-contract.md` to clarify the boundary between verification/mutation receipts and path discovery. Update `aw find` in `agent_workflows/cli.py` to support `--paths` (`-p`) and emit clean repo-relative paths (e.g. `.aw/records/...`) when querying paths or under `--agent` / `--paths`, while preserving `--json` and human interactive table views. Add unit test coverage.
- Scope-Paths: docs/cli-output-contract.md, agent_workflows/cli.py, tests/test_cli_find.py
- Item-Dependencies: none
- Status: approved
- Approval: human (attested by antigravity: user directive to update contract and aw find)
- Set: findpaths
- Order: 1
- Highest E allocated: 03
- Author: antigravity
- Id: v8xdz4

## Workflow history

- 2026-09-01 draft (antigravity): created.
- 2026-09-01 to-review (antigravity): authored complete plan.
- 2026-09-01 approved (antigravity): human approval attested per user directive.

## Goal

Enable token-efficient, bare repo-relative path output for `aw find` across all artifact types, and document the architectural distinction in `docs/cli-output-contract.md`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Output Contract Documentation

- [ ] E-01 Update `docs/cli-output-contract.md` to document the distinction between verification/mutation envelopes (`aw.agent/v1` JSON receipts) and discovery/path resolution verbs (`aw find` path output).
  - Depends on: none
  - Expected outcome: Output contract clearly documents token-efficient bare path output for discovery.
  - Execution state: pending

### Task group 2: `aw find` Path Output Implementation

- [ ] E-02 Add `-p` / `--paths` argument to `aw find` (and `aw search`) in `agent_workflows/cli.py`, extract repo-relative paths in `_find_type_records`, and emit bare newline-delimited paths when `--paths` or `--agent` is active.
  - Depends on: E-01
  - Expected outcome: `aw find <selector> --paths` and `aw find <selector> --agent` output clean `.aw/records/...` paths.
  - Execution state: pending

### Task group 3: Unit Tests & Verification

- [ ] E-03 Add unit test assertions in `tests/test_cli_find.py` covering bare path output under `--paths` and `--agent`, `--json` structured dictionary output, and standard human table output.
  - Depends on: E-01, E-02
  - Expected outcome: Full pytest suite passes cleanly bare.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_workflows/cli.py`: `_run_find`, `_find_type_records`, and verb argument parser loop around line 2540.
- `docs/cli-output-contract.md`: CLI output contract standard.

## Findings

- `_find_type_records` previously emitted formatted strings with ANSI padding. Extracting exact `rel_path` alongside the formatted line allows clean path emission without regex stripping.

## Proposed changes (ordered, validatable)

1. Update `docs/cli-output-contract.md` (E-01).
2. Wire `--paths` / `--agent` bare path emission in `agent_workflows/cli.py` (E-02).
3. Add unit test suite in `tests/test_cli_find.py` (E-03).

## Deferred / out of scope (with reason)

- none.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_cli_find.py` passing.
- Full repository test suite passing bare.

## Spec / documentation sync

- `docs/cli-output-contract.md` updated in E-01.

## Open questions

- none.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `docs/cli-output-contract.md` contains path discovery contract.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `aw find lanectn --paths` and `aw find lanectn --agent` emit bare `.aw/records/...` paths.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Full repository pytest suite passes cleanly bare.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
