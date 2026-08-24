# IPD: Harden ipdrunner process lifecycle, dependency validation, and directory resolution

- Date: 2026-08-24
- Kind: child
- Concern: Assessment of `tools/ipdrunner/*` identified bugs and resilience gaps in child process termination on signals/interrupts, prerequisite validation when dependencies are not included in the active queue, run directory resolution when relative paths are supplied, POSIX directory descriptor modes during atomic JSON writes, attempt timestamp completeness during interrupted recovery, and session ID key extraction.
- Scope: `tools/ipdrunner/ipdrunner.py`, `tools/ipdrunner/test_ipdrunner.py`, and `tools/ipdrunner/20260823-pending-ipds-overnight-execution-runbook.md`.
- Status: to-review
- Set: ipdrunner
- Order: 1
- Highest E allocated: 05
- Author: Antigravity
- Id: pr2nd0

## Workflow history

- 2026-08-24 to-review (Antigravity): assessed tools/ipdrunner/*; proposed 5 changes.

## Goal

Harden `tools/ipdrunner/ipdrunner.py` into a robust, fail-safe execution driver by guaranteeing safe child process termination without orphans on interrupts, enforcing fail-closed dependency validation for prerequisites not present in the queue, supporting flexible directory path inputs, ensuring POSIX-compliant atomic file writes, completing attempt metadata during crash recovery, and adding comprehensive regression tests.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Child process lifecycle and orphan prevention

- [ ] E-01 Implement a resilient child process termination helper in `run_opencode` within `tools/ipdrunner/ipdrunner.py` that intercepts `KeyboardInterrupt` and exceptions, sends `SIGINT`, waits with a short timeout (e.g. 5 seconds), escalates to `SIGTERM` and `SIGKILL` if un-reaped, closes standard stream pipes, and ensures `process.wait()` completes before releasing the driver.
  - Depends on: none
  - Expected outcome: interrupted or failed executions cleanly terminate the underlying OpenCode agent process without leaving background orphans.
  - Execution state: pending

### Task group 2: Prerequisite validation for unqueued dependencies

- [ ] E-02 Update `dependency_status` in `tools/ipdrunner/ipdrunner.py` to check repository executed state for prerequisites not present in the active `state["queue"]` (via `resolve_plan_path` and `plan_bucket == "executed"`), marking items with unexecuted prerequisites as `dependency-blocked` rather than silently assuming satisfaction.
  - Depends on: E-01
  - Expected outcome: running a sub-sequence of plans fail-closes if prerequisite IPDs have not yet executed in the repository.
  - Execution state: pending

### Task group 3: CLI path resolution and session ID extraction

- [ ] E-03 Enhance `resolve_run_dir` in `tools/ipdrunner/ipdrunner.py` to directly accept existing run directory paths (whether relative or absolute) containing a valid `state.json` as well as bare run IDs under `state_root(repo)`. Update `extract_session_id` to inspect `sessionID`, `sessionId`, and `session_id` fields and accept valid string identifiers.
  - Depends on: E-02
  - Expected outcome: `ipdrunner status` and `resume` commands accept printed directory paths directly, and session extraction supports multiple JSON key conventions.
  - Execution state: pending

### Task group 4: POSIX atomic write mode and crash recovery timestamps

- [ ] E-04 Fix `os.open` in `atomic_write_json` to include explicit `os.O_RDONLY` when opening directory file descriptors for `os.fsync`. Update `reconcile_interrupted` to record `interrupted_at: utc_now()` on any unclosed attempt records in `item["attempts"]` during crash recovery.
  - Depends on: E-03
  - Expected outcome: atomic JSON writes conform strictly to POSIX open mode requirements and interrupted attempt schemas maintain timestamp integrity.
  - Execution state: pending

### Task group 5: Regression testing and test suite expansion

- [ ] E-05 Expand `tools/ipdrunner/test_ipdrunner.py` with test cases for unqueued dependency blocking/satisfaction, direct directory path resolution in `resolve_run_dir`, session ID extraction across key formats, and attempt record reconciliation.
  - Depends on: E-04
  - Expected outcome: test suite passes 100% and covers all bug fixes and edge cases.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Project: Agent Workflows toolkit (Python 3.10+).
- Guiding principles: Fail closed (P1), proof not prose (P2), minimal moving parts (P3), durable reference records (P11).
- Contributor contract: Path-scoped commits only, no push, no em/en dashes in user-facing prose.
- Plan lifecycle: `.aw/records/plans/` (`pending/` -> `executed/`).

## Findings

| ID | Severity | Remediation Risk | Persona | Finding |
|---|---|---|---|---|
| F-01 | High | Low | Systems / Software Engineer | `run_opencode` raises on `KeyboardInterrupt` without waiting for child process termination or escalating signals, leaving orphaned coding agent processes running in the repository. |
| F-02 | High | Low | QA / Software Engineer | `dependency_status` checks prerequisites only if present in `state["queue"]` (`if dep in by_id`), silently treating unqueued and unexecuted dependencies as satisfied. |
| F-03 | Medium | Low | Novice User / UI-UX | `resolve_run_dir` concatenates `state_root(repo) / run_id`, failing if the user passes an existing relative or absolute directory path printed by the driver. |
| F-04 | Low | Low | Software Engineer | `atomic_write_json` calls `os.open(path.parent, os.O_DIRECTORY)` without `os.O_RDONLY`, which is non-compliant with POSIX `open(2)` access mode requirements. |
| F-05 | Low | Low | Data-integrity Engineer | `reconcile_interrupted` resets running item status to `interrupted` but leaves `interrupted_at` / `ended_at` unset on the active attempt record. |
| F-06 | Low | Low | Integration Engineer | `extract_session_id` strictly requires `event.get("sessionID")` starting with `ses_`, ignoring alternate camelCase/snake_case JSON keys or non-prefixed provider IDs. |

## Proposed changes (ordered, validatable)

1. Add graceful child process reaping and signal escalation in `run_opencode`.
2. Add repo-backed lifecycle checks for unqueued dependencies in `dependency_status`.
3. Add directory path detection in `resolve_run_dir` and multi-key session ID extraction in `extract_session_id`.
4. Add `os.O_RDONLY` to directory `os.open` and record `interrupted_at` in `reconcile_interrupted`.
5. Add unit tests for all updated behaviors in `tools/ipdrunner/test_ipdrunner.py`.

## Deferred / out of scope (with reason)

None. All findings have Low Remediation Risk and can be addressed safely within `tools/ipdrunner/`.

## Scope check

- Over-scope: none. Changes are localized to `tools/ipdrunner/`.
- Under-scope: none. Covers all identified correctness, lifecycle, and CLI usability issues in the driver.

## Required tests / validation

- Unit tests in `tools/ipdrunner/test_ipdrunner.py` exercising dependency checking, path resolution, atomic writing, and interrupted recovery.
- Verification of clean syntax and formatting via `pre-commit run --files tools/ipdrunner/*`.
- `aw ipd lint` conformance at pre-review phase.

## Spec / documentation sync

- `tools/README.md` and `tools/ipdrunner/20260823-pending-ipds-overnight-execution-runbook.md` reflect existing usage and remain aligned.

## Open questions

### OQ-01: Should the timeout for child termination before SIGKILL be configurable via CLI?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: 5 seconds for SIGINT and 2 seconds for SIGTERM is a standard, safe default for interactive and headless CLI drivers; CLI flags can be added later if needed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: unit test demonstrating child process termination handling and pipe cleanup on signal interruption.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: unit test asserting `dependency_status` flags unexecuted prerequisite as missing when not present in the active queue.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: unit test verifying `resolve_run_dir` successfully accepts existing relative directory path and `extract_session_id` parses alternate JSON keys.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: unit test verifying atomic write directory fsync and attempt `interrupted_at` field population during recovery.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: execution of `python3 tools/ipdrunner/test_ipdrunner.py` with all tests passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This IPD is proposed for human review. In accordance with repository rules, no code changes or plan executions will occur without explicit human approval.
