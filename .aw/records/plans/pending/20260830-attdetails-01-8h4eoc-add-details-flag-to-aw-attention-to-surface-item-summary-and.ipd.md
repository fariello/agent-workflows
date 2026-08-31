# IPD: Add details flag to aw attention to surface item summary and scope lines

- Date: 2026-08-30
- Kind: child
- Concern: The \`aw attention\` board surfaces artifacts by identity stem and status but does not display the summary, scope, or high-level description of items, requiring users to open files individually to inspect what each item is about.
- Scope: Add the \`--details\` (\`-d\`) flag to \`aw attention\` (\`aw att\`), implement a fallback extraction cascade (\`Summary\` -> \`Scope\` -> \`Concern\` -> \`Question\` -> \`Title\` -> \`H1\`) across all artifact trees, render indented detail sub-lines with field tags in \`render_board\` / \`_render_item_row\`, include detail fields in JSON output, and add comprehensive unit tests.
- Scope-Paths: agent_workflows/attention.py, agent_workflows/cli.py, tests/test_attention.py
- Item-Dependencies: none
- Status: approved
- Approval: human (attested by antigravity: user requested --details option B implementation)
- Set: attdetails
- Order: 1
- Highest E allocated: 03
- Author: antigravity
- Id: 8h4eoc

## Workflow history

- 2026-08-30 draft (antigravity): created.
- 2026-08-30 to-review (antigravity): authored complete plan.
- 2026-08-30 approved (antigravity): human approval attested per user directive.

## Goal

Provide a \`--details\` (\`-d\`) option for \`aw attention\` (\`aw att\`) that renders an indented, tagged detail line (\`summary: ...\`, \`scope: ...\`, etc.) under each listed item on the attention board, and populates \`detail_kind\` / \`detail_text\` in JSON output.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an \`E-*\` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Detail Extraction & Item Model

- [ ] E-01 Add \`_extract_detail\` helper and \`detail_kind\` / \`detail_text\` fields to \`Item\` in \`agent_workflows/attention.py\`, populating details for all record types via the cascade \`Summary\` -> \`Scope\` -> \`Concern\` -> \`Question\` -> \`Title\` -> \`H1\`.
  - Depends on: none
  - Expected outcome: All scanned items extract their appropriate summary/scope/concern/question/title line.
  - Execution state: pending

### Task group 2: Board & JSON Rendering

- [ ] E-02 Update \`_render_item_row\`, \`render_board\`, \`render_json\`, and \`run\` in \`agent_workflows/attention.py\` to support \`details=True\` formatting with indented \`      {tag}: {text}\` rows and JSON detail properties.
  - Depends on: E-01
  - Expected outcome: When \`--details\` is enabled, indented tagged detail lines are displayed beneath items in both colored and uncolored board formats, and included in JSON output.
  - Execution state: pending

### Task group 3: CLI Option & Unit Tests

- [ ] E-03 Add \`--details\` (\`-d\`) argument to \`p_attention\` in \`agent_workflows/cli.py\` and author comprehensive unit tests in \`tests/test_attention.py\`.
  - Depends on: E-01, E-02
  - Expected outcome: \`aw attention --details\` and \`aw att -d\` work via CLI and pass test suite with 100% clean verification.
  - Execution state: pending

## Project conventions discovered (Step 0)

- \`agent_workflows/attention.py\`: Core scanner and board renderer for \`aw attention\`.
- \`agent_workflows/cli.py\`: Argparse definition for \`p_attention\` (\`aliases=['att']\`).
- \`tests/test_attention.py\`: Unit tests for attention view, board rendering, and JSON formatting.

## Findings

- A unified fallback cascade (\`Summary\` -> \`Scope\` -> \`Concern\` -> \`Question\` -> \`Title\`) covers all 7 artifact families in \`.aw/records/\`, including Plans (which use \`- Scope:\`) and Research (which use \`- Question:\` or \`- Summary:\`).
- Tagged indentation (\`      summary: ...\` / \`      scope: ...\`) with muted tag styling keeps the board clean, readable, and structured.

## Proposed changes (ordered, validatable)

1. Implement \`_extract_detail\` and extend \`Item\` in \`agent_workflows/attention.py\` (E-01).
2. Update \`_render_item_row\`, \`render_board\`, \`render_json\`, and \`run\` in \`agent_workflows/attention.py\` (E-02).
3. Add \`--details\` / \`-d\` argument in \`agent_workflows/cli.py\` and test cases in \`tests/test_attention.py\` (E-03).

## Deferred / out of scope (with reason)

- none.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- \`python3 -m pytest tests/test_attention.py\` passing.
- \`aw attention --details\` rendering verified on live repository items.

## Spec / documentation sync

- N/A (CLI display option).

## Open questions

### OQ-01: Tag casing and indentation depth?

- Blocking: no
- Status: resolved
- Owner: resolved with user
- Resolution or deferral rationale: RESOLVED - 6 spaces indentation (\`      \`) and lowercase tag prefix (e.g. \`summary:\`, \`scope:\`).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a \`V-*\` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Unit tests verifying cascade extraction for backlog, specs, plans, research, releases.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Output tests verifying exact board formatting with indented tagged lines.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pytest run on \`tests/test_attention.py\` and full suite passes cleanly.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
