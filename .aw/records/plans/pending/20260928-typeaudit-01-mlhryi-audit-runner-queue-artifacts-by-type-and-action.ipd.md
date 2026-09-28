# IPD: Audit runner queue artifacts by type and action

- Date: 2026-09-28
- Kind: child
- Concern: artifact-audit-typed-dispatch
- Scope: Audit runner queue steps by artifact type and action, aligning expectations with record_placement
- Scope-Paths: agent_workflows/run_viewer.py, agent_workflows/artifact_audit.py, tests/test_artifact_audit.py, tests/test_run_viewer.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: 7tswqn
- Blocks-Release: next
- Set: typeaudit
- Order: 1
- Highest E allocated: 04
- Author: Gabriele Fariello
- Id: mlhryi

## Workflow history

- 2026-09-28 to-review (Gabriele Fariello): author review-ready plan graduating backlog item 7tswqn.

## Goal

Make `agent_workflows.artifact_audit` and `agent_workflows.run_viewer` aware of artifact types (`backlog`, `spec`, `ipd`) and runner actions (`plan`, `review`, `execute`), resolving directory expectations through `agent_workflows.record_placement` so that graduated backlog items and typed queue steps are audited against their actual lifecycle contracts rather than false plan-only assumptions.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Runner Step Representation and Forwarding

- [ ] E-01 Retain artifact type on `StepSummary` and forward type and action to `audit_artifact`.
  - In `agent_workflows/run_viewer.py`, add `artifact_type: str = "ipd"` to the `StepSummary` dataclass.
  - When constructing `StepSummary` in `RunSummary.from_run_dir` (within `run_viewer.py`), extract the step's artifact type from the queue entry JSON via `runner_shared.queue_entry_type(item)`.
  - Update `audit_step_artifact(step, repo_root, evidence)` in `run_viewer.py` to forward `artifact_type=step.artifact_type` and `action=step.action` into `_audit.audit_artifact`.
  - Depends on: none
  - Expected outcome: `StepSummary` accurately records whether an entry is an IPD, backlog item, or spec, and passes this context into the audit engine.
  - Execution state: pending

### Task group 2: Typed Expectation Engine in Artifact Audit

- [ ] E-02 Implement typed expectation mapping in `agent_workflows/artifact_audit.py` leveraging `record_placement`.
  - In `agent_workflows/artifact_audit.py`, import `target_subdir` from `agent_workflows.record_placement`.
  - Add helper `expected_artifact_state(artifact_type: str, action: str, run_status: str)` defining valid target directories and declared statuses:
    - For `artifact_type == "backlog"` under `action == "plan"`:
      - When `run_status in ("executed", "complete")`: valid directories are `{"graduated", "done"}` and valid declared statuses are `{"graduated", "done"}`.
      - When `run_status in ("queued", "running", "interrupted", "fail-gate", "fail-begin", "fail-lane", "fail-verify", "fail-depend", "fail-merge", "not-run", "failed", "cancelled", "abandoned")`: valid directories are `{"open", "blocked"}` and valid declared statuses are `{"open", "blocked", "parked"}`.
    - For `artifact_type in ("ipd", "plans")`:
      - When `run_status in ("executed", "complete")`: valid directories are `{"executed", "superseded", "not-executed", "reusable"}` and valid declared statuses are `{"executed", "complete"}`.
      - When `run_status == "retired"`: valid directories and statuses are `{"superseded", "not-executed"}`.
      - When `run_status == "reviewed"`: valid directory is `{"pending"}` and valid statuses are `{"reviewed", "approved"}`.
      - Pre-terminal outcomes: valid directory is `{"pending"}` and valid statuses are `{"approved", "to-review", "draft", "reviewed", "queued", "running"}`.
    - For other types, delegate directory resolution to `record_placement.target_subdir(artifact_type, run_status)`.
  - Update `audit_artifact` to accept `artifact_type: str = ""` and `action: str = ""`. If `artifact_type` is omitted or defaults to `"ipd"` but the resolved artifact path sits under `records/backlog/` or has a `.backlog.md` extension, infer `artifact_type = "backlog"`.
  - Update `location_mismatch` and `status_mismatch` evaluation in `audit_artifact` to check against the typed valid directories and statuses.
  - Depends on: E-01
  - Expected outcome: `audit_artifact` evaluates backlog items, specs, and plans against their own family lifecycle directories and statuses.
  - Execution state: pending

### Task group 3: Classification and Tracked-File Audit

- [ ] E-03 Update `_classified` and `audit_tracked_artifact` in `agent_workflows/artifact_audit.py`.
  - In `_classified`:
    - For backlog artifacts:
      - If `run_status in _RUN_SUCCESS_STATUSES`: classify as `CLASS_UNCHANGED` (or `CLASS_RESOLVED` if finalized after run) when the actual directory is in `{"graduated", "done"}`. Only classify as `CLASS_REGRESSED` if the actual directory is not in `{"graduated", "done"}`.
      - If `run_status` is in-flight (`queued`, `running`) and actual directory is in `{"open", "blocked"}`: classify as `CLASS_UNCHANGED`.
  - In `audit_tracked_artifact` (the `aw doctor` consumer):
    - Determine `record_type` from the artifact path.
    - Use `record_placement.target_subdir(record_type, declared)` to compute expected directory instead of assuming plan-only `_TERMINAL_EXPECTED_DIR`.
  - Add comprehensive unit tests in `tests/test_artifact_audit.py` and `tests/test_run_viewer.py` pinning:
    1. Backlog items with `run_status == "executed"` residing in `graduated/` or `done/` classify as `CLASS_UNCHANGED` (`has_discrepancy == False`).
    2. Backlog items with `run_status == "running"` or `"queued"` residing in `open/` classify as `CLASS_UNCHANGED`.
    3. Backlog items with `run_status == "executed"` still residing in `open/` classify as `CLASS_REGRESSED`.
    4. Plan execution and review audit behaviors remain fully preserved without regressions.
  - Depends on: E-02
  - Expected outcome: Artifact classification handles heterogeneous queue items without false regression alarms, and `aw doctor` accurately checks tracked files across all types.
  - Execution state: pending

### Task group 4: End-to-End Validation and Suite Pass

- [ ] E-04 Run suite tests and verify active runs in `aw runs --active -s`.
  - Run `tests/test_artifact_audit.py` and `tests/test_run_viewer.py` to confirm all unit tests pass.
  - Run `python3 -m agent_workflows runs --active -s` to confirm that the 31 false "regressed" rows and 19 false "unknown" rows in `run-20260928T034313Z-2200079` are eliminated.
  - Run full test suite with bare `python3 -m pytest`.
  - Depends on: E-03
  - Expected outcome: Full test suite passes cleanly and live runs report zero false artifact regressions.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_workflows.run_viewer.StepSummary`: Dataclass defined at `agent_workflows/run_viewer.py` representing a queue step.
- `agent_workflows.runner_shared.queue_entry_type`: Defined at `agent_workflows/runner_shared.py` (line 36021), extracts `artifact_type` from queue entry mapping, defaulting to `"ipd"`.
- `agent_workflows.record_placement.target_subdir`: Defined at `agent_workflows/record_placement.py` (line 43), the repository's single authority mapping `(record_type, status)` to target directory.
- `agent_workflows.artifact_audit.audit_artifact`: Defined at `agent_workflows/artifact_audit.py` (line 955), evaluates artifact location and declared status against recorded run state.
- `agent_workflows.artifact_audit._classified`: Defined at `agent_workflows/artifact_audit.py` (line 550), assigns directional difference classes (`CLASS_REGRESSED`, `CLASS_UNCHANGED`, etc.).

## Findings

1. `8l8dgb` introduced typed dispatch for backlog and spec items, storing `"artifact_type": "backlog"` on queue entries in `state.json`.
2. `StepSummary` in `run_viewer.py` omitted `artifact_type`, dropping type metadata before calling `audit_step_artifact`.
3. `artifact_audit.py` hardcoded `_TERMINAL_EXPECTED_DIR = {"executed": "executed", ...}` and expected all successful steps to reside in `executed/` with status `executed`.
4. Backlog items successfully planned under `--action plan` transition to `graduated` (or `done`) in `records/backlog/graduated/` (or `done/`). Comparing them against plan-only rules caused 31 false `regressed` alarms and 19 false `unknown` alarms in `run-20260928T034313Z-2200079`.

## Proposed changes (ordered, validatable)

1. Modify `agent_workflows/run_viewer.py`: Add `artifact_type` to `StepSummary`, extract it in `RunSummary.from_run_dir`, and pass `artifact_type` and `action` to `_audit.audit_artifact`.
2. Modify `agent_workflows/artifact_audit.py`: Import `target_subdir` from `agent_workflows.record_placement`, implement `expected_artifact_state`, accept `artifact_type` and `action` in `audit_artifact`, and update `_classified` and `audit_tracked_artifact`.
3. Modify `tests/test_artifact_audit.py` and `tests/test_run_viewer.py`: Add targeted tests for typed queue audit behavior.

## Deferred / out of scope (with reason)

None: all requirements are addressed within the scope of this plan. Modifying runner state machine TERMINAL_STATES in agent_workflows/runner_shared.py is not deferred work but an architectural non-goal; runner queue status represents step execution outcome (executed), which is distinct from artifact lifecycle status (graduated).

## Scope check

- Over-scope: none. Changes are restricted to run viewer parsing and artifact audit classification.
- Under-scope: none. Addresses both live runner auditing (`aw runs`) and tracked artifact inspection (`aw doctor`).

## Required tests / validation

- Unit tests in `tests/test_artifact_audit.py` asserting correct classification of backlog and spec queue steps.
- Unit tests in `tests/test_run_viewer.py` asserting `StepSummary` populates `artifact_type`.
- Live inspection via `aw runs --active -s` demonstrating elimination of false regressions.
- Full test suite execution via bare `python3 -m pytest`.

## Spec / documentation sync

- N/A: internal runtime reporting and audit logic; no user-facing CLI flag or public documentation changes required.

## Open questions

### OQ-01: How should `audit_artifact` handle an explicit `artifact_type="ipd"` when the resolved path on disk is a `.backlog.md`?

- Blocking: no
- Status: resolved
- Owner: Gabriele Fariello
- Resolution or deferral rationale: Resolved by prioritizing the resolved artifact path when it clearly identifies a non-IPD family (e.g. `records/backlog/` or `.backlog.md`), preventing callers that defaulted to `"ipd"` from forcing plan expectations onto a backlog file.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Unit test output showing `StepSummary` captures `artifact_type` from queue entry JSON, and `audit_step_artifact` forwards `artifact_type` and `action`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Unit test output from `tests/test_artifact_audit.py` demonstrating `expected_artifact_state` returns valid directories `{"graduated", "done"}` for `(artifact_type="backlog", action="plan", run_status="executed")` and `{"open", "blocked"}` for in-flight statuses.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Unit test output from `tests/test_artifact_audit.py` demonstrating that a graduated backlog item is classified as `CLASS_UNCHANGED` (`has_discrepancy == False`), while an in-place open backlog item under `executed` is classified as `CLASS_REGRESSED`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted terminal output from `aw runs --active -s` showing zero false regressions on `run-20260928T034313Z-2200079`, and full clean output from bare `python3 -m pytest`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: Commit only scoped paths (`agent_workflows/run_viewer.py`, `agent_workflows/artifact_audit.py`, `tests/test_artifact_audit.py`, `tests/test_run_viewer.py`) through `aw commit mlhryi -- <paths>`. Merge to `main` with integration lock via `aw integration-lock -- git merge --ff-only aw/lane/typeaudit`.
