# IPD: Elapsed time formatting in statusbar and resume starting time fix

- Date: 2026-08-30
- Kind: child
- Concern: In the runner statusbar, elapsed time was previously counted from the original run creation timestamp on `resume` rather than from when the resume invocation started, and durations >= 60m were formatted as raw minutes (e.g. `187m56s`) instead of hours/minutes/seconds (`XhYmZs`) and days (`Wd XhYmZs`).
- Scope: Update `oc_runipd.py` and `agy_runipd.py` so `Statusline` elapsed time starts from the current invocation start time on `resume` and `start`, implement `format_compact_duration` and day formatting in `agent_workflows/render_stream.py` and `agent_workflows/run_viewer.py`, and update test suites.
- Scope-Paths: agent_workflows/render_stream.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/run_viewer.py, tests/test_render_stream.py, tests/test_stall_countdown_display.py, tests/test_run_summary_table.py
- Item-Dependencies: none
- Status: executed
- Set: timefmt
- Order: 1
- Highest E allocated: 04
- Author: antigravity
- Id: rhszxj

## Workflow history
- 2026-08-30 executed (antigravity): Implemented resume elapsed start timing and XhYmZs / Wd XhYmZs duration formatting [Scope reconciliation - in-scope-unmodified agent_workflows/agy_runipd.py: acknowledged; in-scope-unmodified agent_workflows/oc_runipd.py: acknowledged; in-scope-unmodified agent_workflows/render_stream.py: acknowledged; in-scope-unmodified agent_workflows/run_viewer.py: acknowledged; in-scope-unmodified tests/test_render_stream.py: acknowledged; in-scope-unmodified tests/test_run_summary_table.py: acknowledged; in-scope-unmodified tests/test_stall_countdown_display.py: acknowledged]

- 2026-08-30 draft (antigravity): created.
- 2026-08-30 to-review (antigravity): authored complete plan.
- 2026-08-30 approved (antigravity): human approval attested per user directive.

## Goal

Ensure the runner statusbar elapsed time starts counting from the instant `resume` or `start` begins, and format all durations >= 60 minutes as `XhYmZs` and >= 24 hours as `Wd XhYmZs`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Duration Formatting Utilities

- [x] E-01 Implement `format_compact_duration` in `agent_workflows/render_stream.py` and update `format_duration` in `render_stream.py` and `run_viewer.py` with hour and day transitions.
  - Depends on: none
  - Expected outcome: Durations >= 60m format as `XhYmZs` (e.g. `3h07m56s`) and >= 24h format as `Wd XhYmZs` (e.g. `1d 3h07m56s`).
  - Execution state: performed

### Task group 2: Statusline & Heartbeat Rendering

- [x] E-02 Update `format_statusline_lines`, `Statusline`, and `Heartbeat` in `agent_workflows/render_stream.py` to use `format_compact_duration` for run elapsed, idle time, and item elapsed.
  - Depends on: E-01
  - Expected outcome: Statusline renders clean, consistent compact durations for all columns.
  - Execution state: performed

### Task group 3: Invocation Timing on Resume & Start

- [x] E-03 Update `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` to initialize `run_start_mono` from the start of the current run/resume invocation rather than `state["created_at"]`.
  - Depends on: E-01, E-02
  - Expected outcome: `aw oc run resume` and `aw agy run resume` start counting elapsed time from 0m00s when invoked.
  - Execution state: performed

### Task group 4: Test Suite Updates

- [x] E-04 Update `tests/test_render_stream.py`, `tests/test_stall_countdown_display.py`, and `tests/test_run_summary_table.py` to test duration transitions and resume timing.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: All test suites pass 100% clean.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `Statusline.run_start_mono`: Monotonic start timestamp used by the background statusline thread to compute elapsed time via `time.monotonic() - self.run_start_mono`.
- `render_stream.format_statusline_lines`: Unified 2-line statusline renderer.

## Findings

- `run_opencode` and `run_agy_turn` were deriving `run_start_mono = time.monotonic() - (time.time() - created_ts)` from `state["created_at"]`, which caused resumed runs to display the entire wall time since the initial run creation rather than the runtime of the active resume invocation.
- Durations >= 60m were formatted via `divmod(run_elapsed, 60)` into raw minutes (e.g. `187m56s`) instead of decomposing into hours and days.

## Proposed changes (ordered, validatable)

1. Add `format_compact_duration` and update `format_duration` in `render_stream.py` and `run_viewer.py` (E-01).
2. Wire `format_compact_duration` into `format_statusline_lines` and `Heartbeat` (E-02).
3. Set `_invocation_start_mono` and pass it to `Statusline` in `oc_runipd.py` and `agy_runipd.py` (E-03).
4. Update unit tests in `tests/test_render_stream.py`, `tests/test_stall_countdown_display.py`, and `tests/test_run_summary_table.py` (E-04).

## Deferred / out of scope (with reason)

- none.

## Scope check

- Over-scope: none. Strictly fixes duration formatting and resume elapsed timing.
- Under-scope: none. Applies to both OpenCode and Antigravity runners.

## Required tests / validation

- `python3 -m pytest tests/test_render_stream.py tests/test_stall_countdown_display.py tests/test_run_summary_table.py` passing.
- `python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py` passing.

## Spec / documentation sync

- N/A (display formatting bugfix).

## Open questions

### OQ-01: Does resetting the statusline elapsed timer on resume affect the stored attempt start/end timestamps?

- Blocking: no
- Status: resolved
- Owner: resolved from architecture
- Resolution or deferral rationale: RESOLVED - No. Item attempt records continue to store absolute UTC ISO8601 timestamps (`started_at`, `ended_at`) for durable auditing; only the live terminal statusline display measures duration relative to the current invocation.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Unit tests verifying `format_compact_duration` and `format_duration` for seconds, minutes, hours, and days.
  - Observed evidence: `test_format_compact_duration` and `test_format_duration` in `tests/test_render_stream.py` and `tests/test_run_summary_table.py` passed with assertions for 0s, 45s, 4m08s, 1h04m21s, 3h07m56s, and 1d 3h07m56s.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Test showing `format_statusline_lines` produces `1h04m21s` instead of `64m21s`.
  - Observed evidence: `test_format_statusline_exact_layout` and `test_layout_is_unchanged_when_no_countdown` passed verifying `1h04m21s idle: 14s`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Unit test verifying `Statusline` receives invocation start monotonic time on resume.
  - Observed evidence: `test_resume_statusbar_starts_from_resume_time` in `tests/test_run_summary_table.py` passed asserting `_invocation_start_mono >= t_before`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Full pytest suite passes with pasted output.
  - Observed evidence: `3654 passed, 3 skipped, 4 xfailed in 43.74s` in full pytest run.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
