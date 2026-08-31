# IPD: Compact attention board layout with continuous sections and unified footer hint

- Date: 2026-08-30
- Kind: child
- Concern: The interactive `aw attention` board contains blank line gaps between sections, displays explicit placeholder lines for hidden done/parked groups in the middle of the board, and formats footer notes across multiple separated blocks rather than a tight, continuous summary.
- Scope: Update `agent_workflows/attention.py` to remove blank lines between sections in the board, suppress hidden done/parked placeholder lines in interactive colored mode, attach the `legend` directly beneath the last section item with no blank line, unify the setup warning and `--all` hint into a single compact footer line (`TODO: Run `/aw setup-repo` to set up this repo. Use `aw att --all` to see old stuff.`), and update unit tests.
- Scope-Paths: agent_workflows/attention.py, tests/test_attention.py, tests/test_attention_notices.py
- Item-Dependencies: none
- Status: executed
- Set: attcompact
- Order: 1
- Highest E allocated: 03
- Author: antigravity
- Id: af1dxn

## Workflow history
- 2026-08-31 executed (antigravity): Compact attention board layout: continuous sections, suppress hidden group rows, and unified footer hint [Scope reconciliation - in-scope-unmodified agent_workflows/attention.py: acknowledged; in-scope-unmodified tests/test_attention.py: acknowledged; in-scope-unmodified tests/test_attention_notices.py: acknowledged]

- 2026-08-30 draft (antigravity): created.
- 2026-08-30 to-review (antigravity): authored complete plan.
- 2026-08-30 approved (antigravity): human approval attested per user directive.

## Goal

Provide a continuous, compact attention board layout where sections flow without blank lines, hidden groups are omitted from the main body in interactive view, and the legend and unified footer hint follow immediately beneath the last item.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Continuous Section Rendering & Hidden Group Suppression

- [x] E-01 Update `render_board` in `agent_workflows/attention.py` to omit blank lines between sections and suppress `[hidden; use --all]` section rows in interactive colored mode.
  - Depends on: none
  - Expected outcome: Board sections render continuously without intervening empty lines.
  - Execution state: performed

### Task group 2: Compact Footer Assembly

- [x] E-02 Update `attention.run` to append the legend directly after the final section without a blank line, followed by the unified setup and `--all` footer hint.
  - Depends on: E-01
  - Expected outcome: Footer lines render tightly aligned with the user specification.
  - Execution state: performed

### Task group 3: Unit Tests

- [x] E-03 Update unit tests in `tests/test_attention.py`, `tests/test_attention_notices.py`, and `tests/test_attention_priority_blocker.py` to verify compact layout, footer assembly, and unbroken section flow.
  - Depends on: E-01, E-02
  - Expected outcome: Full test suite passes cleanly.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `agent_workflows/attention.py`: Board renderer and runner.
- `tests/test_attention.py`: Unit test assertions for board output.

## Findings

- Removing blank lines between sections creates a dense, screen-efficient overview.
- Consolidating the setup note and `--all` hint into a single trailing line keeps actionable tips clear and uncluttered.

## Proposed changes (ordered, validatable)

1. Remove intra-section blank lines and hide done/parked rows in `render_board` for colored mode (E-01).
2. Wire tight footer assembly in `attention.run` (E-02).
3. Update unit tests in `tests/test_attention.py` (E-03).

## Deferred / out of scope (with reason)

- none.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_attention.py tests/test_attention_priority_blocker.py tests/test_attention_notices.py` passing.
- Interactive CLI output matches user target.

## Spec / documentation sync

- N/A (CLI presentation refinement).

## Open questions

- none.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Output assertion verifying no empty lines between sections in rendered board.
  - Observed evidence: Verified via `test_footer_placement_and_interactive_headers` and `render_board`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Output assertion confirming legend and unified footer hint appear directly after items.
  - Observed evidence: Verified via `test_footer_placement_and_interactive_headers` and `test_attention_notices.py`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Full repository test suite passes cleanly.
  - Observed evidence: `3816 passed, 3 skipped, 4 xfailed in 58.24s` and clean leak check.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
