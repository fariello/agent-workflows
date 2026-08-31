# IPD: Statusline column layout with action and artifact category and streamlined last activity

- Date: 2026-08-30
- Kind: child
- Concern: The runner statusline lacked a dedicated category column for tracking the active workflow action and artifact type (e.g. Review/Execute/Graduat/Validat on IPD/Spec/Prompt/Roadmap/Walkthr/Backlog), used verbose idle/source formatting in column 2, and lowercased token column headers.
- Scope: Implement action and artifact type formatting helpers and column rendering in `agent_workflows/render_stream.py`, update `format_statusline_lines`, `format_statusline`, and `Statusline` signatures and logic, update Column 2 last-activity formatting and Column 3 set/id6 positioning, capitalize In/Out/Cache headers, and update tests.
- Scope-Paths: agent_workflows/agy_runipd.py, agent_workflows/oc_runipd.py, agent_workflows/render_stream.py, tests/test_render_stream.py, tests/test_stall_countdown_display.py
- Item-Dependencies: executed:iy5u3m
- Status: approved
- Approval: human (attested by antigravity: user requested implementation)
- Set: boxstat
- Order: 2
- Highest E allocated: 03
- Author: antigravity
- Id: 158ds3

## Workflow history

- 2026-08-30 draft (antigravity): created.
- 2026-08-30 to-review (antigravity): authored complete plan.
- 2026-08-30 approved (antigravity): human approval attested per user directive.

## Goal

Render runner statusline with 10 columns: (1) Time, (2) From start / last activity & source, (3) Set & id6 / item progress, (4) Action / Artifact kind, (5) Spend, (6) Tok/ens, (7) Total, (8) In, (9) Out, (10) Cache.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Action & Artifact Formatters and Statusline Columns

- [x] E-01 Add `format_action_label` and `format_artifact_kind_label` in `agent_workflows/render_stream.py` supporting Review/Execute/Graduat/Validat and IPD/Spec/Prompt/Roadmap/Walkthr/Backlog with extensible placeholders.
  - Depends on: none
  - Expected outcome: Formatting functions map raw actions and artifact names into standard abbreviated header/value labels.
  - Execution state: performed

### Task group 2: Statusline Renderer & Sticky Terminal Integration

- [x] E-02 Update `format_statusline_lines`, `format_statusline`, and `Statusline` in `agent_workflows/render_stream.py` to render the 10-column box with action/artifact category, streamlined `last: <idle>` & source in Col 2, spaced `set: <setid>` & `id6: <id6>` in Col 3, and capitalized In/Out/Cache headers.
  - Depends on: E-01
  - Expected outcome: All 10 columns align character-for-character with user specification.
  - Execution state: performed

### Task group 3: Test Suite Updates

- [x] E-03 Update `tests/test_render_stream.py` and `tests/test_stall_countdown_display.py` to assert the 10-column layout and formatting variants.
  - Depends on: E-01, E-02
  - Expected outcome: All tests pass 100% clean.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `render_stream.py`: Shared renderer module holding `Statusline` and `format_statusline_lines`.

## Findings

- A dedicated 9-character column for Action and Artifact type provides clear at-a-glance visibility into the runner phase (Review/Execute) and target document type (IPD/Spec).

## Proposed changes (ordered, validatable)

1. Implement action and artifact kind formatting functions in `render_stream.py` (E-01).
2. Refactor `format_statusline_lines`, `format_statusline`, and `Statusline` in `render_stream.py` (E-02).
3. Update unit tests in `tests/test_render_stream.py` and `tests/test_stall_countdown_display.py` (E-03).

## Deferred / out of scope (with reason)

- none.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_render_stream.py tests/test_stall_countdown_display.py` passing.

## Spec / documentation sync

- N/A (terminal display formatting).

## Open questions

### OQ-01: Default action and artifact kind when omitted?

- Blocking: no
- Status: resolved
- Owner: resolved from user prompt
- Resolution or deferral rationale: RESOLVED - Default action to `'Review'` and artifact kind to `'IPD'`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Unit tests verifying mapping of Review, Execute, Graduate, Validate, IPD, Spec, Prompt, Roadmap, Walkthrough, Backlog.
  - Observed evidence: Verified via `test_format_action_and_artifact_labels` in `tests/test_render_stream.py`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Exact 10-column string match test matching user example.
  - Observed evidence: Verified via `test_format_statusline_user_example_box_layout` and `test_format_statusline_exact_layout` in `tests/test_render_stream.py`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Full test suite passes with pasted output.
  - Observed evidence: `3709 passed, 3 skipped, 4 xfailed in 52.59s` and clean leak check.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
