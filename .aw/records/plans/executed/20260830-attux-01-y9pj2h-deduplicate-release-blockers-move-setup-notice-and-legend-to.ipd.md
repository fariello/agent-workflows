# IPD: Deduplicate release blockers, move setup notice and legend to bottom, and bold interactive section headers

- Date: 2026-08-30
- Kind: child
- Concern: The `aw attention` board lists release-blocking items redundantly in both their native readiness section (e.g. ready/blocked) and in the release-blockers section; notices (setup required) and the legend occupy prominent space at the very top of the board; and interactive section headers use raw markdown "## " markers rather than clean bold styling.
- Scope: Update `agent_workflows/attention.py` so that items qualifying as release-blockers are rendered exclusively in the `release-blockers` section, move the setup required note and legend to the bottom of the output, eliminate superfluous blank lines, drop the "## " prefix in interactive colored mode in favor of bold colored section headers (while preserving "## " in uncolored machine/markdown mode), and update unit tests.
- Scope-Paths: agent_workflows/attention.py, tests/test_attention.py
- Item-Dependencies: none
- Status: executed
- Set: attux
- Order: 1
- Highest E allocated: 03
- Author: antigravity
- Id: y9pj2h

## Workflow history
- 2026-08-31 executed (antigravity): Refine attention board layout: deduplicate blockers, footer notice/legend, and bold interactive headers [Scope reconciliation - in-scope-unmodified agent_workflows/attention.py: acknowledged; in-scope-unmodified tests/test_attention.py: acknowledged]

- 2026-08-30 draft (antigravity): created.
- 2026-08-30 to-review (antigravity): authored complete plan.
- 2026-08-30 approved (antigravity): human approval attested per user directive.

## Goal

Refine the `aw attention` board layout by deduplicating release blockers so they appear only once under `release-blockers`, moving the setup-needed notice and legend to the bottom footer, removing extra blank lines, and styling interactive headers with bold/color without markdown "## " prefixes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Deduplicate Release Blockers from Main Readiness Sections

- [x] E-01 Update `attention.run` to partition scanned items such that live items in `release_blockers` are excluded from the `active`/`ready`/`blocked` sections rendered by `render_board` and appear only in `release-blockers`.
  - Depends on: none
  - Expected outcome: Release-blocking items are listed exactly once in the board output.
  - Execution state: performed

### Task group 2: Footer Placement & Header Styling

- [x] E-02 Move `setup_needed` notice and `legend` string to the bottom of the output in `agent_workflows/attention.py`, strip excessive blank lines, and format interactive section headers with bold styling and no "## " prefix (retaining "## " in uncolored/machine output).
  - Depends on: E-01
  - Expected outcome: Clean interactive header styling and footer placement with no duplicate spacing.
  - Execution state: performed

### Task group 3: Unit Tests & Regression Verification

- [x] E-03 Update unit tests in `tests/test_attention.py` to assert deduplicated blocker rendering, footer notice/legend order, and colored vs uncolored header formatting.
  - Depends on: E-01, E-02
  - Expected outcome: Full pytest suite passes cleanly.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `agent_workflows/attention.py`: `render_board`, `_render_item_row`, `release_blockers`, and `run`.
- `tests/test_attention.py`: Unit test assertions for colored and plain board output.

## Findings

- Separating `blockers` from `main_items` before passing to `render_board` ensures that items with live release gates are never printed twice.
- Retaining `## ` in `color=False` (uncolored mode) preserves compatibility for scripts, agents, and markdown parsers that rely on fixed markdown headings.

## Proposed changes (ordered, validatable)

1. Partition items in `attention.run` so blockers are excluded from main classes (E-01).
2. Update header rendering in `render_board` and footer assembly in `attention.run` (E-02).
3. Update assertions and add tests in `tests/test_attention.py` (E-03).

## Deferred / out of scope (with reason)

- none.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_attention.py` passing.
- Interactive CLI check on live repo.

## Spec / documentation sync

- N/A (CLI presentation refinement).

## Open questions

- none.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Test asserting release-blocking items do not appear in ready/active/blocked sections when blockers section is present.
  - Observed evidence: Verified via `test_run_deduplicates_release_blockers` in `tests/test_attention.py`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Output assertions confirming legend and setup notice appear at the bottom, and interactive headers are bold without "## ".
  - Observed evidence: Verified via `test_footer_placement_and_interactive_headers` and `test_render_board_colored_human_view` in `tests/test_attention.py`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Full repository test suite passes cleanly.
  - Observed evidence: `3816 passed, 3 skipped, 4 xfailed in 45.79s` and clean leak check.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
