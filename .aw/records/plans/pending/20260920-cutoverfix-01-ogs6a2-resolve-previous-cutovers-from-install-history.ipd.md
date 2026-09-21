# IPD: Resolve previous cutovers from install history

- Date: 2026-09-20
- Kind: child
- Concern: Hardcoded calendar cutover dates in check_engine.py violate repo-independence and break external target repositories upon install or upgrade.
- Scope: Replace static module constants for previous cutovers (spec_id6, carrier_obligations, dependency_schema) with dynamic resolution derived from the target repository's installation history or committed project configuration.
- Scope-Paths: agent_workflows/config.py, agent_workflows/project_schema.py, agent_workflows/engine.py, agent_workflows/install_wizard.py, agent_workflows/check_engine.py, agent_workflows/artifact_naming.py, .aw/config/project.json, AGENTS.md, .aw/records/specs/20260817-2147-01-uniform-artifact-naming-grammar.spec.md, tests/test_config.py, tests/test_check_engine.py, tests/test_durable_capture.py, tests/test_spec_id6_filenames.py, tests/test_runner_item_dependencies.py
- Item-Dependencies: none
- Status: approved
- Set: cutoverfix
- Order: 1
- Highest E allocated: 05
- Author: antigravity
- Id: ogs6a2
- Approval: 2026-09-21, human ("approved"): Approved by maintainer: resolve previous cutovers from install history

## Workflow history
- 2026-09-21 approved (aw set, --by-human): Approved by maintainer: resolve previous cutovers from install history

- 2026-09-20 to-review (antigravity): authored complete review-ready IPD for dynamic install-based cutover resolution.
- 2026-09-20 draft (antigravity): created via aw ipd scaffold.

## Goal

Eliminate hardcoded calendar dates for previous enforcement cutovers (including `SPEC_ID6_CUTOVER_DATE` and `CARRIER_CUTOVER_DATE` in `check_engine.py`, and un-stamped `dependency_schema_cutover` in `config.py`). Replace them with a unified dynamic cutover resolver that binds enforcement boundaries to the date of the install or update that introduced each requirement into the target repository, preserving portability and fail-open grandfathering across all repos.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Unified cutover resolution & install history inspection

- [ ] E-01 Implement dynamic cutover resolver and install history reader in `agent_workflows/config.py` and `agent_workflows/project_schema.py`.
  - Depends on: none
  - Expected outcome: Add typed `cutovers` support in `ProjectPolicySchema`. Implement `resolve_cutover_date(repo_root: Path, feature: str, compact: bool = True) -> Optional[str]` in `config.py` resolving with precedence: (1) `.aw/config/project.json` under `cutovers.<feature>` or legacy keys; (2) target repository install history in `.aw/state/history/installs.jsonl` matching the install that introduced the feature; (3) fail-open `None`. Implement `sync_cutovers_on_install(repo_root: Path, install_timestamp: Optional[str] = None)` to stamp missing cutover dates into `project.json`.
  - Execution state: pending
- [ ] E-02 Wire cutover synchronization into framework install and update in `agent_workflows/engine.py` and `agent_workflows/install_wizard.py`.
  - Depends on: E-01
  - Expected outcome: `install_into_repo` and `install_wizard.py` invoke `sync_cutovers_on_install` so any known cutover feature missing from `project.json` is stamped with the date of the install containing that feature (or the current install date if newly added), preserving existing dates across subsequent installs.
  - Execution state: pending

### Task group 2: Check engine refactoring & retirement of hardcoded dates

- [ ] E-03 Refactor spec id6 cutover in `agent_workflows/check_engine.py` and `agent_workflows/artifact_naming.py` to use dynamic cutover.
  - Depends on: E-01
  - Expected outcome: Refactor `_spec_requires_id6` and `check_names` to take `repo_root` and resolve the date via `resolve_cutover_date(repo_root, "spec_id6")`. Retain `SPEC_ID6_CUTOVER_DATE` as an importable deprecated alias returning the resolved date or historical fallback for external caller compatibility, while internal checks execute dynamically. Update `artifact_naming.py` docstrings.
  - Execution state: pending
- [ ] E-04 Refactor carrier obligations and dependency schema cutovers in `agent_workflows/check_engine.py`.
  - Depends on: E-01
  - Expected outcome: Refactor `carrier_severity_for_plan` and `check_ipd_uncarried_obligations` to query `resolve_cutover_date(repo_root, "carrier_obligations")`. Refactor `_is_grandfathered_plan` and `check_ipd_dependencies` to use `resolve_cutover_date(repo_root, "dependency_schema")`. Retain `CARRIER_CUTOVER_DATE` as an importable deprecated alias for backward compatibility.
  - Execution state: pending

### Task group 3: Repo policy sync & documentation

- [ ] E-05 Synchronize repository configuration, tests, and documentation.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: Update `.aw/config/project.json` with the stamped historical cutover dates corresponding to this repo's actual install history (`spec_id6`: `2026-08-29`, `carrier_obligations`: `2026-09-19`, `dependency_schema`: `2026-09-01`). Update `AGENTS.md` and spec `20260817-2147-01` to document that cutovers are bound to the repository's install date. Update test suites in `tests/test_config.py`, `tests/test_check_engine.py`, `tests/test_durable_capture.py`, `tests/test_spec_id6_filenames.py`, and `tests/test_runner_item_dependencies.py`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- In `agent_workflows/check_engine.py:40`, `SPEC_ID6_CUTOVER_DATE = "20260828"` was hardcoded as a static string constant.
- In `agent_workflows/check_engine.py:4505`, `CARRIER_CUTOVER_DATE = "20260919"` was hardcoded as a static string constant, with a note citing that `config.dependency_cutover_date` returned `None` because the installer never stamped it.
- In `.aw/state/history/installs.jsonl`, actual install records exist with ISO timestamps and file counts (e.g. `2026-08-18`, `2026-08-29`, `2026-09-05`), providing durable local provenance of when updates occurred.
- In `agent_workflows/project_schema.py`, `ProjectPolicySchema` preserves unknown fields on serialization, and modeling `cutovers` makes it a typed, first-class field.
- In `tests/test_durable_capture.py` and `tests/test_spec_id6_filenames.py`, tests import and reference cutover symbols directly, requiring backward-compatible aliases.

## Findings

- Static cutover constants in the Python library cause any target repository installing the framework after that date to treat its own historical pre-existing files as non-conforming.
- Cutovers must be per-repository and portable, living in the committed `.aw/config/project.json`.
- When an installation or update occurs, cutover dates for newly active enforcements must be stamped with the date of that installation or update, or derived from the recorded installation history in `.aw/state/history/installs.jsonl`.

## Proposed changes (ordered, validatable)

1. In `agent_workflows/config.py` and `agent_workflows/project_schema.py`: implement `resolve_cutover_date(repo_root, feature, compact=True)` and `sync_cutovers_on_install(repo_root, install_timestamp)`. Support `spec_id6`, `carrier_obligations`, and `dependency_schema`.
2. In `agent_workflows/engine.py` and `agent_workflows/install_wizard.py`: call `sync_cutovers_on_install` during repository install and update passes.
3. In `agent_workflows/check_engine.py` and `agent_workflows/artifact_naming.py`: replace direct static constant evaluations in `_spec_requires_id6`, `check_names`, `carrier_severity_for_plan`, and `check_ipd_dependencies` with dynamic lookups using `repo_root`, while keeping backward-compatible aliases.
4. In `.aw/config/project.json`: stamp the cutover dates reflecting this repository's install history.
5. In `AGENTS.md` and spec `20260817-2147-01`: document the dynamic install cutover mechanism.
6. In `tests/test_durable_capture.py`, `tests/test_config.py`, `tests/test_check_engine.py`, `tests/test_spec_id6_filenames.py`, and `tests/test_runner_item_dependencies.py`: update tests to assert dynamic cutover resolution.

## Deferred / out of scope (with reason)

- Modifying the setid length cutover mechanism: deferred because plan `x75obw` (`setidlen`) already incorporates dynamic install cutover storage.
  - Carrier-Declined: Plan x75obw owns setid length cutovers; this plan unifies previous cutovers.
- Rewriting historical spec filenames: deferred because grandfathering cleanly preserves legacy spec names.
  - Carrier-Declined: Historical specs remain valid and grandfathered under their pre-cutover status.

## Scope check

- Over-scope: none. Focused strictly on previous cutovers (`spec_id6`, `carrier_obligations`, `dependency_schema`).
- Under-scope: avoided by inspecting install history, wiring the installer hook, updating test suites (including `test_durable_capture.py`, `test_spec_id6_filenames.py`, and `test_runner_item_dependencies.py`), and keeping backward-compatible aliases.

## Required tests / validation

- `tests/test_config.py`: unit tests for `resolve_cutover_date` verifying resolution from `project.json`, fallback to `installs.jsonl` history, compact/ISO formatting, and fail-open `None`.
- `tests/test_check_engine.py`: unit tests proving `check_names`, `check_ipd_uncarried_obligations`, and `check_ipd_dependencies` evaluate against the dynamically resolved cutover date.
- `tests/test_durable_capture.py`: suite passes with dynamic cutover integration and verified backward-compatibility aliases.
- `tests/test_spec_id6_filenames.py`: suite passes verifying spec id6 grandfathering against the dynamic cutover.
- `tests/test_runner_item_dependencies.py`: suite passes verifying runner dependency preflight against the dynamic cutover.
- Integration test: verify `install_into_repo` populates missing cutover dates in `project.json` and preserves existing ones.

## Spec / documentation sync

- `AGENTS.md`: update mentions of cutover dates to reflect that they are determined by repository installation/update dates.
- `.aw/records/specs/20260817-2147-01-uniform-artifact-naming-grammar.spec.md`: note that spec id6 cutover is dynamic per repo install.

## Open questions

### OQ-01: What format should the cutovers section use in project.json?

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: A dedicated `"cutovers": { "<feature>": "YYYY-MM-DD" }` object in `.aw/config/project.json`, while maintaining backward-compatible fallback for legacy keys like `"dependency_schema_cutover"`.

### OQ-02: How should cutover dates be resolved when a repo has no installs.jsonl?

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: If neither `project.json` nor `installs.jsonl` has a record, `resolve_cutover_date` returns `None` (fail-open), ensuring an uninitialized or fresh workspace is never broken before `aw install` / `aw setup` runs.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `python3 -m pytest tests/test_config.py` passes, verifying `resolve_cutover_date` against project policy, install history, compact/ISO formatting, and fail-open fallbacks.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Automated test showing `install_into_repo` synchronizes missing cutover dates into `project.json` matching the install timestamp and preserves existing dates on subsequent calls.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: `python3 -m pytest tests/test_check_engine.py tests/test_spec_id6_filenames.py` passes, showing `check_names` honors dynamic `spec_id6` cutover date and that `SPEC_ID6_CUTOVER_DATE` remains importable as a compatible alias.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: `python3 -m pytest tests/test_check_engine.py tests/test_durable_capture.py tests/test_runner_item_dependencies.py` passes, verifying `carrier_severity_for_plan` and `check_ipd_dependencies` evaluate against dynamic cutovers.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: `python3 -m agent_workflows.cli check all` passes with 0 new drift findings, and documentation reflects the dynamic cutover contract.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: execute path-scoped commits for each task group without mutating unrelated files. All automated tests must run and pass. Upon completion, transition via `aw ipd finalize` in a managed lane or report results for maintainer review.
