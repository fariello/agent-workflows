# IPD: Boxed rounded-border statusline layout with split token metrics and countdown headers

- Date: 2026-08-30
- Kind: child
- Concern: The 2-line runner statusline layout lacked enclosing box-art borders, placed the stall countdown and progress source inline within the 'From start' value column causing horizontal drift, and lacked dedicated sub-columns for Total/In/Out/Cache token metrics under a unified 'Tokens' header.
- Scope: Refactor `format_statusline_lines`, `format_statusline`, and `Statusline` in `agent_workflows/render_stream.py` to render the 4-line rounded border table box with dedicated token sub-columns and header countdown positioning, and update test suites.
- Scope-Paths: agent_workflows/render_stream.py, tests/test_render_stream.py, tests/test_stall_countdown_display.py
- Item-Dependencies: none
- Status: approved
- Approval: human (attested by antigravity: user requested implementation)
- Set: boxstat
- Order: 1
- Highest E allocated: 03
- Author: antigravity
- Id: iy5u3m

## Workflow history

- 2026-08-30 draft (antigravity): created.
- 2026-08-30 to-review (antigravity): authored complete plan.
- 2026-08-30 approved (antigravity): human approval attested per user directive.

## Goal

Render runner statusline within a rounded Unicode border box (`╭─┬─╮`, `│ │ │`, `╰─┴─╯`), positioning stall countdowns in the column header and progress source in the value line, with a two-row `Tok` / `ens` column header splitting token metrics into `Total`, `in`, `out`, and `cache`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Statusline Box Renderer

- [ ] E-01 Update `format_statusline_lines` and `format_statusline` in `agent_workflows/render_stream.py` to compute exact column widths, top border, header row, value row, and bottom border with token sub-columns.
  - Depends on: none
  - Expected outcome: `format_statusline_lines` returns `(top, l1, l2, bot)` matching the exact layout specification.
  - Execution state: pending

### Task group 2: Sticky Terminal Redraw Integration

- [ ] E-02 Update `Statusline.redraw`, `Statusline.clear`, and `Statusline.write_event` in `agent_workflows/render_stream.py` to handle the 4-line terminal buffer span (`[3A`).
  - Depends on: E-01
  - Expected outcome: Sticky statusline redraws, clears, and logs events cleanly across all 4 lines without terminal artifacts.
  - Execution state: pending

### Task group 3: Test Suite Updates

- [ ] E-03 Update `tests/test_render_stream.py` and `tests/test_stall_countdown_display.py` to verify the boxed layout, column alignment, color styling, and non-TTY handling.
  - Depends on: E-01, E-02
  - Expected outcome: All unit tests pass 100% clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `render_stream.py`: Shared interactive streaming renderer module holding `Statusline` and `format_statusline_lines`.
- Border characters: Rounded Unicode (`╭`, `┬`, `╮`, `│`, `─`, `╰`, `┴`, `╯`) and ASCII fallback (`+`, `-`, `|`).

## Findings

- Placing countdown in the header line and `(last: <source>)` in the value line gives clean vertical separation and keeps column widths compact and stable throughout a run.

## Proposed changes (ordered, validatable)

1. Update `format_statusline_lines` and `format_statusline` in `render_stream.py` (E-01).
2. Update `Statusline` methods for 4-line box management in `render_stream.py` (E-02).
3. Update unit tests in `tests/test_render_stream.py` and `tests/test_stall_countdown_display.py` (E-03).

## Deferred / out of scope (with reason)

- none.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_render_stream.py tests/test_stall_countdown_display.py` passing.

## Spec / documentation sync

- N/A (interactive terminal display formatting).

## Open questions

### OQ-01: Does format_statusline_lines signature break external callers?

- Blocking: no
- Status: resolved
- Owner: resolved from architecture
- Resolution or deferral rationale: RESOLVED - No. The return type returns the sequence of rendered lines; `format_statusline` joins with `
`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Test showing `format_statusline_lines` generates all 4 lines with exact character-level alignment matching the user template.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Unit test verifying non-TTY and sticky redraw handling with 4 lines.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Full test suite passes with pasted output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
