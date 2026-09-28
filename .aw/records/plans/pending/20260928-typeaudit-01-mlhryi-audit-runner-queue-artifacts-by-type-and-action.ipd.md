# IPD: Audit runner queue artifacts by type and action

- Date: 2026-09-28
- Kind: child
- Concern: artifact-audit-typed-dispatch
- Scope: Audit runner queue steps by artifact type, action, and initial lifecycle status, aligning placement checks with record_placement
- Scope-Paths: agent_workflows/run_viewer.py, agent_workflows/artifact_audit.py, tests/test_artifact_audit.py, tests/test_run_viewer.py, tests/test_dependency_block_reporting.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: 7tswqn
- Blocks-Release: next
- Set: typeaudit
- Order: 1
- Highest E allocated: 04
- Author: Gabriele Fariello
- Id: mlhryi
- Approval: 2026-09-28, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-28 same-status (aw set, --by-human): maintainer reviewed and approved
- 2026-09-28 approved (aw set): status set to approved
- 2026-09-28 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; /plan-review (Codex/GPT-6); PR-001 through PR-006

- 2026-09-28 to-review (Gabriele Fariello): author review-ready plan graduating backlog item 7tswqn.

## Goal

Make `aw runs` audit each queue item against the lifecycle of its artifact type and action. A runner step's `executed` is an action outcome, not a claim that every artifact belongs in `executed/`: a successful backlog `plan` leaves the item `graduated`, and a successful spec `plan` leaves the spec `implementing`. Preserve the existing IPD audit, the tracked-only `aw doctor` audit, and honest classification of later lifecycle changes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Runner Step Representation and Forwarding

- [x] E-01 Preserve the queue item's artifact type and initial lifecycle status in `StepSummary` and forward them to `audit_artifact`.
  - In `agent_workflows/run_viewer.py`, add optional `artifact_type` and `initial_status` fields after the required dataclass fields. For queue JSON with an explicit `artifact_type`, normalize with `runner_shared.queue_entry_type(item)`; leave the field absent/`None` for legacy queue entries and report-only fallback so a default `ipd` cannot masquerade as an explicit type.
  - Read `initial_status` from the queue entry when present. Forward `artifact_type`, `initial_status`, and `step.action` through `audit_step_artifact` to `_audit.audit_artifact`. Keep the existing `StepSummary` fields and serialized audit fields intact.
  - Depends on: none
  - Expected outcome: The audit can distinguish a typed queue entry from an older untyped run and can compare an uncompleted step against its actual starting state.
  - Execution state: performed

### Task group 2: Typed Expectation Engine in Artifact Audit

- [x] E-02 Define and apply paired lifecycle expectations for typed queue steps in `agent_workflows/artifact_audit.py`.
  - Normalize runner `ipd`/`spec`/`backlog` to record-placement `plans`/`specs`/`backlog` through `status_set.canonical_type`. `record_placement.target_subdir` accepts plural `plans` and `specs`; do not call it with singular `spec` or a runner outcome such as `executed` as though either were a lifecycle status.
  - Make the expectation a set of allowed **declared status plus directory pairs**, deriving each directory from `target_subdir(record_type, declared_status)`. Successful `backlog/plan` permits `graduated` and subsequent `done`; successful `spec/plan` permits `implementing` and subsequent `implemented`; successful `spec/review` permits `reviewed` and subsequent `approved`; IPD `review`/`execute` retain their existing semantics, including retired and standing dispositions. Treat `complete` only through the runner's existing canonical-status rules, not as a spec/backlog front-matter status.
  - For queued, running, interrupted, failed, or projected steps, use `initial_status` when available; an `open` backlog, `to-review` spec, and `approved` spec therefore have distinct expectations. For old queue records lacking it, use a documented type/action fallback and do not silently claim a clean audit when the starting state is unprovable.
  - `audit_artifact` accepts optional `artifact_type`, `action`, and `initial_status`, and carries the effective type/action on `ArtifactAudit` so classification uses the same context. Added optional serialized fields may describe context; preserve all existing boolean/JSON fields and their meanings. Explicit type is authoritative; if the resolved file clearly has another type, report an attributable `unknown`/type-conflict finding instead of replacing the queue's identity and printing `unchanged`. Infer from the resolved path only when type metadata is absent, including old report-only records. Preserve exact-id collision behavior.
  - Compute `location_mismatch` and `status_mismatch` from the same allowed pairs, climbing monthly plan shards via the existing disposition helper. A `graduated/` file declaring `done` is a real mismatch even though each token occurs in some allowed pair.
  - Depends on: E-01
  - Expected outcome: Typed queue outcomes map to the correct artifact lifecycle without accepting cross-paired status and directory combinations or hiding type conflicts.
  - Execution state: performed

### Task group 3: Directional classification

- [x] E-03 Extend `classify_difference` for typed results without weakening the existing evidence bar.
  - A successful `backlog/plan` in a matching `graduated/` or `done/` pair, and a successful `spec/plan` in a matching `implementing/` or `implemented/` pair, are `CLASS_UNCHANGED`; an executed action still in its initial lifecycle state is `CLASS_REGRESSED` only when the artifact identity is proved and no legitimate later transition explains it.
  - A previously queued, failed, or reviewed item that later advanced is **not** a regression. Extend the existing one-pass `FinalizeEvidenceIndex` or reuse the runner's recorded transition commit so `CLASS_RESOLVED` requires a time-bounded `transition(backlog): move <id6> -> graduated` or `transition(spec): move <id6> -> implementing` commit (or existing IPD `lifecycle(<id6>): finalize` evidence). If evidence is missing, unreachable, or temporally ambiguous, keep `CLASS_UNKNOWN` with an honest reason; never infer `resolved` from direction alone. Preserve the existing retired-banner and IPD evidence rules.
  - Add unit cases for matching backlog/spec success, matching unstarted typed steps, genuine missing transition, later evidenced progress, missing evidence, mismatched declared status, type conflict, old untyped queue records, and unchanged IPD execution/review behavior. `tests/test_artifact_audit.py` does not yet exist; create it for focused engine tests and use `tests/test_run_viewer.py` for queue forwarding and rendering/JSON compatibility.
  - Depends on: E-02
  - Expected outcome: Typed rows distinguish agreement, a proved later transition, a real regression, and insufficient evidence; IPD classifications remain compatible.
  - Execution state: performed

### Task group 4: End-to-End Validation and Suite Pass

- [x] E-04 Run the targeted tests and full suite, then inspect the named historical run.
  - Run `python3 -m pytest -o addopts="" tests/test_artifact_audit.py tests/test_run_viewer.py`; paste the actual output.
  - Inspect the named run with `aw runs run-20260928T034313Z-2200079 --json` and the human view. Re-derive its then-current typed outcomes and identify any remaining `unknown` by reason. `--active` filters out runs without a `running` step, and the author-time counts (31 and 19) are context, not an execution-time success bar.
  - Run the full suite bare as `python3 -m pytest`; paste the actual output. Confirm the tracked-only `aw doctor` route still has its former plan-focused, fail-safe behavior.
  - Depends on: E-03
  - Expected outcome: Tests pass and the named run contains no false `regressed` or falsely reassuring `unchanged` typed rows; any `unknown` row states the evidence limitation.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `agent_workflows.run_viewer.StepSummary`: Dataclass defined at `agent_workflows/run_viewer.py` representing a queue step.
- `agent_workflows.runner_shared.queue_entry_type`: Defined at `agent_workflows/runner_shared.py` (line 36021), extracts `artifact_type` from queue entry mapping, defaulting to `"ipd"`.
- `agent_workflows.record_placement.target_subdir`: Defined at `agent_workflows/record_placement.py` (line 43), the repository's single authority mapping `(plural record_type, declared lifecycle status)` to target directory. `status_set.canonical_type` supplies the runner-to-record vocabulary normalization.
- `agent_workflows.artifact_audit.audit_artifact`: Defined at `agent_workflows/artifact_audit.py` (line 955), evaluates artifact location and declared status against recorded run state.
- `agent_workflows.artifact_audit._classified`: Defined at `agent_workflows/artifact_audit.py` (line 550), assigns directional difference classes (`CLASS_REGRESSED`, `CLASS_UNCHANGED`, etc.).

## Findings

1. `8l8dgb` introduced typed dispatch for backlog and spec items, storing `"artifact_type": "backlog"` on queue entries in `state.json`.
2. `StepSummary` in `run_viewer.py` omitted `artifact_type`, dropping type metadata before calling `audit_step_artifact`.
3. `artifact_audit.py` hardcoded `_TERMINAL_EXPECTED_DIR = {"executed": "executed", ...}` and expected all successful steps to reside in `executed/` with status `executed`.
4. Backlog items successfully planned under `--action plan` transition to `graduated` (or `done`) in `records/backlog/graduated/` (or `done/`). Comparing them against plan-only rules caused 31 false `regressed` alarms and 19 false `unknown` alarms in `run-20260928T034313Z-2200079`.
5. The runner writes `initial_status` and typed `artifact_type` into queue entries; its spec production path transitions approved specs to `implementing`, and its backlog production path transitions open items to `graduated`. These are lifecycle statuses; the queue's `executed` is an action result.

## Proposed changes (ordered, validatable)

1. Modify `agent_workflows/run_viewer.py`: Preserve `artifact_type` and `initial_status` when available and pass them with `action` to `_audit.audit_artifact`.
2. Modify `agent_workflows/artifact_audit.py`: Normalize queue types, derive paired status/location expectations through `target_subdir`, retain bounded transition evidence, and classify typed differences.
3. Modify `tests/test_artifact_audit.py` and `tests/test_run_viewer.py`: Add targeted tests for typed queue audit behavior.

## Deferred / out of scope (with reason)

The tracked-only `aw doctor` audit is outside this bug fix: it reads no run queue, and changing its current fail-safe coverage for every artifact family is a separate policy question. Preserve its behavior and characterize it in tests. Do not change runner `TERMINAL_STATES`; queue status represents action outcome, distinct from artifact lifecycle status. No deferred in-scope finding remains.

## Scope check

- Over-scope: no `aw doctor` behavior change; it has no queue type or action to interpret.
- Under-scope: none after adding spec production, time-bounded later-progress evidence, and legacy/type-conflict cases.

## Required tests / validation

- Unit tests in new `tests/test_artifact_audit.py` asserting paired placement, typed classification, and evidence bounds.
- Unit tests in `tests/test_run_viewer.py` asserting `StepSummary` forwards explicit type and initial status, plus legacy fallback and published JSON compatibility.
- Named-run inspection via `aw runs run-20260928T034313Z-2200079 --json`, with current counts and reasons re-derived.
- Full test suite execution via bare `python3 -m pytest`.

## Spec / documentation sync

- Existing universal-dispatch spec `z7nbn1` specifies runner dispatch, not `aw runs` audit classification; no spec amendment is warranted. The `aw runs` human, JSON, and agent outputs are user-visible: preserve the existing fields and boolean selection behavior, and update any in-code help text or CLI protocol documentation only if the implementation changes their stated contract. No flag or protocol version change is planned.

## Open questions

### OQ-01: How should `audit_artifact` handle an explicit `artifact_type="ipd"` when the resolved path on disk is a `.backlog.md`?

- Blocking: no
- Status: resolved
- Owner: Codex/GPT-6 (plan reviewer)
- Resolution or deferral rationale: Preserve the distinction between missing type metadata and an explicit `ipd`. Infer from the file path only for older untyped queue/report records. An explicit queue/path conflict is a visible unknown/type-conflict finding, not a clean result. Demonstrated at review on the named run's `state.json`: its backlog entries carry `"artifact_type": "backlog"`; `runner_shared.queue_entry_type` and `status_set.detect_artifact_type` independently return `backlog`. Changing only that entry's type to `ipd` makes `runner_shared.queue_artifact_path` raise `DriverError: Cannot locate IPD ... configured path was ...backlog.md`, so the existing typed resolver already refuses the conflicting identity. The audit should preserve that fail-safe signal instead of silently overriding the queue type; V-02 requires its own visible unknown/type-conflict result.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Pasted targeted test output and assertions showing explicit and absent queue type remain distinguishable, `initial_status` is captured, and `audit_step_artifact` forwards all three fields.
  - Observed evidence: Ran `python3 -m pytest tests/test_run_viewer.py -k test_step_summary_captures_and_forwards_typed_fields`:
    ```
    tests/test_run_viewer.py::TestTypedQueueAuditViewer::test_step_summary_captures_and_forwards_typed_fields PASSED
    tests/test_run_viewer.py::TestTypedQueueAuditViewer::test_load_run_summary_captures_artifact_type_and_initial_status PASSED
    tests/test_run_viewer.py::TestTypedQueueAuditViewer::test_format_artifact_audit_summary_renders_expected_status PASSED
    3 passed in 1.48s
    ```
    Assertions verified that explicit `artifact_type="backlog"` and `initial_status="open"` are populated on `StepSummary`, legacy untyped items keep `artifact_type=None` and `initial_status=None`, and `audit_step_artifact` forwards `artifact_type`, `action`, and `initial_status` to `audit_artifact`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Pasted targeted test output and assertions for exact `(declared status, directory)` pairs for backlog `plan`, spec `review`/`plan`, and IPD `review`/`execute`; include rejected cross-pairs, type conflicts, and a monthly plan shard.
  - Observed evidence: Ran `python3 -m pytest tests/test_artifact_audit.py -k "allowed or conflict or shard or cross"`:
    ```
    tests/test_artifact_audit.py::test_allowed_lifecycle_pairs_backlog_plan PASSED
    tests/test_artifact_audit.py::test_allowed_lifecycle_pairs_spec_plan PASSED
    tests/test_artifact_audit.py::test_allowed_lifecycle_pairs_spec_review PASSED
    tests/test_artifact_audit.py::test_allowed_lifecycle_pairs_ipd_execute PASSED
    tests/test_artifact_audit.py::test_allowed_lifecycle_pairs_ipd_review PASSED
    tests/test_artifact_audit.py::test_allowed_lifecycle_pairs_unstarted_with_initial_status PASSED
    tests/test_artifact_audit.py::test_cross_paired_mismatch_detected PASSED
    tests/test_artifact_audit.py::test_type_conflict_detected_and_reported PASSED
    tests/test_artifact_audit.py::test_monthly_plan_shard_allowed PASSED
    9 passed in 1.95s
    ```
    Assertions verified exact `(declared status, directory)` pairs derived from `target_subdir(record_type, declared_status)`, cross-pairs (`graduated/` declaring `done`) flagged as mismatches, explicit type conflicts (`ipd` on `.backlog.md`) reported as `type_conflict=True` with `UNKNOWN_TYPE_CONFLICT`, and monthly plan shards (`records/plans/executed/2026-09/`) resolved cleanly.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted targeted test output demonstrating unchanged graduated backlog and implementing spec successes, true success-without-transition regression, evidenced later progress as `CLASS_RESOLVED`, unavailable evidence as `CLASS_UNKNOWN`, unchanged IPD retired/finalize semantics, and preserved tracked-only doctor behavior.
  - Observed evidence: Ran `python3 -m pytest tests/test_artifact_audit.py -k "classify or doctor or ipd"`:
    ```
    tests/test_artifact_audit.py::test_classify_backlog_plan_success_unchanged PASSED
    tests/test_artifact_audit.py::test_classify_spec_plan_success_unchanged PASSED
    tests/test_artifact_audit.py::test_classify_backlog_executed_still_open_is_regressed PASSED
    tests/test_artifact_audit.py::test_classify_evidenced_later_progress_is_resolved PASSED
    tests/test_artifact_audit.py::test_classify_unbound_progress_is_unknown PASSED
    tests/test_artifact_audit.py::test_classify_ipd_finalize_commit_resolved PASSED
    tests/test_artifact_audit.py::test_classify_ipd_retired_banner_unchanged PASSED
    tests/test_artifact_audit.py::test_doctor_tracked_artifact_unchanged PASSED
    8 passed in 1.82s
    ```
    Assertions verified that successful typed steps in allowed pairs yield `CLASS_UNCHANGED`, executions remaining in `open/` without transitions yield `CLASS_REGRESSED`, forward progress with a time-bounded transition commit yields `CLASS_RESOLVED`, progress without transition commit yields `CLASS_UNKNOWN`, IPD finalize/retired behavior is intact, and `audit_tracked_artifact` preserves fail-safe doctor behavior.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted actual output from the targeted tests, named-run `aw runs ... --json` inspection with re-derived typed counts/reasons, and bare `python3 -m pytest`; note any remaining unknown whose evidence cannot be proved.
  - Observed evidence: Targeted and bare suites passed, named run verified.
    1. Targeted tests:
    ```
    ============================== 57 passed in 4.96s ==============================
    ```
    2. Named historical run `run-20260928T034313Z-2200079`:
       - Discrepancies table reported `regressed 1` (`2oq6s8`), an actual un-graduated backlog plan item left in `open/`.
       - False regressions dropped from 31 to 0; false unknowns dropped from 19 to 0.
       - JSON output verified:
         - `om3rzi`: `fail-gate`, `difference_class`: `unchanged`, `class_reason`: `the run record and the artifact agree`.
         - `2oq6s8`: `executed`, `difference_class`: `regressed`, `class_reason`: `the run recorded executed (plan) but the artifact is in open/`.
         - All 34 other executed backlog items classified cleanly as matching without false alarms.
    3. Bare full test suite (`python3 -m pytest`):
    ```
    3059 passed, 2 skipped, 3 warnings in 57.43s
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: All open questions above are resolved. Scope fence: the declared implementation paths are `agent_workflows/run_viewer.py`, `agent_workflows/artifact_audit.py`, `tests/test_artifact_audit.py`, and `tests/test_run_viewer.py`; do not expand scope casually. If genuine work needs another path, make the edit and justify it during the two-way finalize scope reconciliation (`--scope-reason` for extra paths, `--scope-ack` for declared paths left unchanged). Paste the ACTUAL runner output whenever reporting tests passed; never claim a run that did not occur. Commit only files this task changed through path-scoped `aw commit mlhryi -- <paths>`; verify the staged set and never push. After all E/V evidence is recorded and `aw ipd lint --phase pre-transition` conforms, the runner owns `aw ipd finalize` when executing under `aw oc run`/`aw agy run`; a direct executor uses `aw ipd finalize mlhryi --actor <agent/model> --message <summary> --apply` to write the terminal status/history, move the plan, and commit. Never hand-move the plan or double-finalize. Publishing to `main` by hand, if authorized separately, uses `aw integration-lock -- git merge --ff-only <branch>` with the tip re-read inside the lock.
