# IPD: Formatted exit summary table for runner with metrics and signal safety

- Date: 2026-08-30
- Kind: child
- Concern: Runners currently lack a structured, visually compelling summary table at exit that reports statusbar metrics (duration, spend, tokens breakdown), per-item results, and diagnostic details across all termination pathways including SIGINT (Ctrl-C), SIGTERM, and errors.
- Scope: Implement `format_duration` and `render_run_summary_table` in `agent_workflows/render_stream.py`, wire exit table rendering into `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` across all completion and interrupt/signal pathways, install SIGTERM signal handling for clean exit, and add unit tests in `tests/test_run_summary_table.py`.
- Scope-Paths: agent_workflows/render_stream.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_run_summary_table.py
- Item-Dependencies: none
- Status: approved
- Approval: human (attested by antigravity: user requested implementation)
- Set: exittbl
- Order: 1
- Highest E allocated: 04
- Author: antigravity
- Id: bds6nd

## Workflow history

- 2026-08-30 draft (antigravity): created.
- 2026-08-30 to-review (antigravity): authored complete spec with visual layout, box drawing art, and signal safety.
- 2026-08-30 approved (antigravity): human approval attested per user directive.

## Goal

Provide a structured, visually compelling summary table at runner exit that aggregates total runtime, cost, token usage (total, input, output, cache), progress bar, per-item status, duration, spend, and tokens, with guaranteed rendering on normal completion, deliberate stop levels 1-4, SIGINT/Ctrl-C, SIGTERM, and driver errors.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Stream and Table Renderer

- [x] E-01 Implement `format_duration` and `render_run_summary_table` in `agent_workflows/render_stream.py` with box-drawing border alignment, top summary banner, per-item status and metrics columns, total row, and failure diagnostics.
  - Depends on: none
  - Expected outcome: `render_run_summary_table` returns an aligned, colorized, and robust table for any state dict.
  - Execution state: performed

### Task group 2: OpenCode and Antigravity Driver Integration

- [x] E-02 Wire exit table rendering into `agent_workflows/oc_runipd.py` across `run_queue`, `locked_run`, and `main`, and install SIGTERM signal handling that triggers clean shutdown and displays the table.
  - Depends on: E-01
  - Expected outcome: `aw oc run` displays the summary table on successful completion, deliberate stop, SIGINT/Ctrl-C, SIGTERM, and DriverError.
  - Execution state: performed

- [x] E-03 Wire exit table rendering symmetrically into `agent_workflows/agy_runipd.py` across all exit and signal pathways.
  - Depends on: E-01, E-02
  - Expected outcome: `aw agy run` displays the summary table symmetrically on all exit pathways.
  - Execution state: performed

### Task group 3: Comprehensive Test Coverage

- [x] E-04 Create `tests/test_run_summary_table.py` testing table rendering, column alignments, token calculations, empty/partial queues, and interrupt/signal safety.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: Full unit test coverage passing with 0 failures.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `render_stream.py`: Shared interactive streaming renderer module holding `Palette`, `format_compact_tokens`, `format_progress_bar`, and status colors.
- `locked_run`: Context manager holding the run lock and invoking `clean_shutdown` in a `finally` block.
- `Palette`: Colorizer honoring color enablement, ANSI stripping, and status color mapping.

## Findings

- During interactive or batch runs, when an operator interrupts a run via Ctrl-C (SIGINT) or SIGTERM, the live statusline was cleared without leaving a persistent record of the run metrics, total spend, tokens consumed, or completed items in the terminal output.
- A post-exit summary table provides immediate visibility into cost, duration, and queue disposition without requiring manual inspection of JSON state files.

## Proposed changes (ordered, validatable)

1. Add `format_duration` and `render_run_summary_table` to `agent_workflows/render_stream.py` (E-01).
2. Wire summary table rendering and SIGTERM handler in `agent_workflows/oc_runipd.py` (E-02).
3. Wire summary table rendering and SIGTERM handler in `agent_workflows/agy_runipd.py` (E-03).
4. Author unit test suite in `tests/test_run_summary_table.py` (E-04).

## Deferred / out of scope (with reason)

- **Modifying on-disk state schema**: State format is already expressive; this feature is pure display and exit-signal presentation.

## Scope check

- Over-scope: none. Strictly implements exit summary table and signal exit rendering.
- Under-scope: none. Full parity across both OpenCode and Antigravity runners.

## Required tests / validation

- `python3 -m pytest tests/test_run_summary_table.py` passing.
- `python3 -m pytest tests/test_oc_runipd.py tests/test_run_viewer.py` passing.

## Spec / documentation sync

- Updates driver exit reporting behavior and documentation.

## Open questions

### OQ-01: Does printing the summary table on interrupt interfere with lane worktree reclamation?

- Blocking: no
- Status: resolved
- Owner: resolved from architecture
- Resolution or deferral rationale: RESOLVED - No. Lane reclamation runs first during interrupt handling to preserve worktrees and files on disk; the summary table is rendered after state is updated and before process termination.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Test showing `render_run_summary_table` produces exact-length borders and correct metrics aggregation.
  - Observed evidence: `test_render_run_summary_table_borders_and_alignment` in `tests/test_run_summary_table.py` asserted all 5 border lines have identical width (115 chars) and all 14 rows match width exactly.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Test verifying `oc_runipd` outputs the summary table on normal completion and interrupt.
  - Observed evidence: `test_oc_runipd_print_status_renders_table` and `test_oc_runipd_main_sigterm_and_sigint_handling` in `tests/test_run_summary_table.py` passed with 130 and 143 return codes and table output.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Test verifying `agy_runipd` outputs the summary table on normal completion and interrupt.
  - Observed evidence: `test_agy_runipd_print_status_renders_table` and `test_agy_runipd_main_sigterm_and_sigint_handling` in `tests/test_run_summary_table.py` passed with 130 and 143 return codes and table output.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: `pytest tests/test_run_summary_table.py` passes with all test counts pasted.
  - Observed evidence: `9 passed in 2.38s` in `tests/test_run_summary_table.py` and full suite `3602 passed, 3 skipped, 4 xfailed in 53.85s`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
