# IPD: Harden ipdrunner process lifecycle, dependency validation, and directory resolution

- Date: 2026-08-24
- Kind: child
- Concern: Assessment of `tools/ipdrunner/*` identified bugs and resilience gaps in child process termination on signals/interrupts, prerequisite validation when dependencies are not included in the active queue, run directory resolution when relative paths are supplied, POSIX directory descriptor modes during atomic JSON writes, attempt timestamp completeness during interrupted recovery, and session ID key extraction.
- Scope: `tools/ipdrunner/ipdrunner.py`, `tools/ipdrunner/test_ipdrunner.py`, and `tools/ipdrunner/20260823-pending-ipds-overnight-execution-runbook.md`.
- Scope-Paths: grandfathered
- Status: reviewed
- Set: ipdrunner
- Order: 1
- Highest E allocated: 05
- Author: Antigravity
- Id: pr2nd0

## Workflow history
- 2026-08-24 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. All 6 findings (F-01..F-06) VERIFIED accurate against tools/ipdrunner/ipdrunner.py: F-01 run_opencode:537-539 (SIGINT+raise, no wait/escalate = orphan risk); F-02 dependency_status:382 (unqueued dep silently satisfied = fail-open); F-03 resolve_run_dir:774-779 (state_root/run_id only); F-04 atomic_write_json os.open O_DIRECTORY w/o O_RDONLY; F-05 reconcile_interrupted:688 (no interrupted_at); F-06 extract_session_id:361 (sessionID+ses_ only). PR-001 (MEDIUM): removed the spurious linear Depends-on chain - E-01..E-04 are independent single-function fixes, only E-05/tests depends on all four. PR-002 (LOW): added the missing execution contract (scope fence/honesty/path-scoped-never-push/lifecycle). PR-003 (LOW): documented the E-03/E-04 two-fix bundling rationale. PR-004 (LOW): real cohesion rationale + OQ-01 open->deferred (non-blocking). Baseline test suite green (3 tests).

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
  - Depends on: none
  - Expected outcome: running a sub-sequence of plans fail-closes if prerequisite IPDs have not yet executed in the repository.
  - Execution state: pending

### Task group 3: CLI path resolution and session ID extraction

- [ ] E-03 Enhance `resolve_run_dir` in `tools/ipdrunner/ipdrunner.py` to directly accept existing run directory paths (whether relative or absolute) containing a valid `state.json` as well as bare run IDs under `state_root(repo)`. Update `extract_session_id` to inspect `sessionID`, `sessionId`, and `session_id` fields and accept valid string identifiers. (F-03 and F-06 are two small, independent single-function fixes bundled here because each is a 1-2 line change in the same file with no shared logic; they are verified by distinct assertions in V-03.)
  - Depends on: none
  - Expected outcome: `ipdrunner status` and `resume` commands accept printed directory paths directly, and session extraction supports multiple JSON key conventions.
  - Execution state: pending

### Task group 4: POSIX atomic write mode and crash recovery timestamps

- [ ] E-04 Fix `os.open` in `atomic_write_json` to include explicit `os.O_RDONLY` when opening directory file descriptors for `os.fsync`. Update `reconcile_interrupted` to record `interrupted_at: utc_now()` on any unclosed attempt records in `item["attempts"]` during crash recovery. (F-04 and F-05 are two small, independent single-function fixes bundled here on the same rationale as E-03; verified by distinct assertions in V-04.)
  - Depends on: none
  - Expected outcome: atomic JSON writes conform strictly to POSIX open mode requirements and interrupted attempt schemas maintain timestamp integrity.
  - Execution state: pending

### Task group 5: Regression testing and test suite expansion

- [ ] E-05 Expand `tools/ipdrunner/test_ipdrunner.py` with test cases for child-process termination/pipe-cleanup on interrupt (E-01), unqueued dependency blocking/satisfaction (E-02), direct directory path resolution in `resolve_run_dir` + multi-key session ID extraction (E-03), and atomic-write directory fsync + attempt record reconciliation timestamps (E-04).
  - Depends on: E-01, E-02, E-03, E-04
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
- Status: deferred
- Owner: author
- Resolution or deferral rationale: DEFERRED (non-blocking). 5 seconds for SIGINT and 2 seconds for SIGTERM is a standard, safe default for interactive and headless CLI drivers; CLI flags can be added later in a follow-up if a real need arises. Does not gate execution of this plan.

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
- Cohesion rationale: one concern - hardening the `tools/ipdrunner/` execution driver - across six independently-verified correctness/lifecycle bug fixes (F-01..F-06), all localized to that directory, each a small single-function change. E-01..E-04 are independent and may be executed in any order; E-05 adds the regression tests that validate all four.

### Execution contract

1. Open questions RESOLVED: OQ-01 (SIGKILL timeout configurability) is non-blocking and resolved as deferred (fixed 5s/2s defaults; CLI flags may be added later if needed). No blocking open question remains.
2. Scope fence: touch ONLY `tools/ipdrunner/ipdrunner.py`, `tools/ipdrunner/test_ipdrunner.py`, and `tools/ipdrunner/20260823-pending-ipds-overnight-execution-runbook.md` (and `tools/README.md` only if a doc line genuinely drifts). Do NOT change `agent_workflows/` package code or any other tool. If a fix seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests/checks passed, paste the ACTUAL runner output (`python3 tools/ipdrunner/test_ipdrunner.py` and `pre-commit run --files tools/ipdrunner/*`); never claim a pass from narration or an unchecked box.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push. A concurrent agent may be active in this tree - leave its edits and staged state untouched.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit (via the existing lifecycle workflow).
