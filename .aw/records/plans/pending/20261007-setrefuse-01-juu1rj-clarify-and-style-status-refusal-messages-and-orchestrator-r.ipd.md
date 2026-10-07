# IPD: Clarify and style status refusal messages and orchestrator readiness gates

- Date: 2026-10-07
- Kind: child
- Concern: Status refusal messages in `aw set` and `aw ipd set` (notably for orchestrator readiness and approval gates) are confusing, un-skimmable, and factually misleading. When attempting to approve orchestrator `itamry`, the setter printed `Orchestrator itamry is not ready for review:` even though it was already reviewed and was awaiting approval, dumped raw internal linter codes (`IPD-Q501`) without extracting the actual blocking question, and failed to explain the parent-child relationship. Furthermore, across `status_set.py` and `plan_readiness.py`, refusal messages are dense, unbulleted run-on sentences lacking ANSI color or bold highlighting on id6s, setids, and status words.
- Scope: Make `orchestrator_readiness.render_human` target-status-aware (`approved`, `reviewed`, `to-review`) and state the causal parent-child constraint clearly. Extract and display the title/text of child blocking open questions. Add ANSI bold and color styling for id6s, setids, and statuses across `orchestrator_readiness.py` and `status_set.py`. Polish and bulletize refusal messages for single-plan approval gates, backward transitions without `--message`, terminal reopenings, and priority backstops. Add regression tests verifying all revised outputs.
- Scope-Paths: agent_workflows/orchestrator_readiness.py, agent_workflows/status_set.py, agent_workflows/plan_readiness.py, tests/test_orchestrator_readiness.py, tests/test_status_set.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: hf5cc4
- Set: setrefuse
- Order: 1
- Highest E allocated: 05
- Author: antigravity
- Id: juu1rj

## Workflow history

- 2026-10-07 to-review (antigravity): authored review-ready plan in an isolated worktree from backlog hf5cc4.
- 2026-10-07 draft (antigravity): created via aw ipd scaffold.

## Goal

Provide clear, skimmable, and visually styled error and refusal messages in `aw set` and `aw ipd set`, ensuring that orchestrator readiness checks reflect the requested target status (such as `approved`), explain parent-child blocking relationships plainly, extract blocking question text, and highlight all id6s, setids, and lifecycle statuses in bold colors.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Orchestrator readiness and causal child error rendering

- [ ] E-01 Make `orchestrator_readiness.render_human` status-aware, causal, and styled with ANSI colors.
  - Depends on: none
  - Expected outcome: `orchestrator_readiness.render_human(result, target_status=None, term=None)` accepts the target status and an optional `Term` instance. When `target_status` is `"approved"` (or `"reviewed"`), the header reads `Refusing to set {target_status} for orchestrator {id6} (set {setid}):` instead of `Orchestrator {id6} is not ready for review:`. For child lint findings caused by an open blocking question (`IPD-Q501`), the renderer parses the child plan text to extract the question identifier (`OQ-NN`) and its question title/text, rendering them as a clear sub-bullet rather than dumping raw linter diagnostic strings. All id6s and setids are highlighted in bold cyan/yellow and status tokens are formatted in their canonical lifecycle colors when color is enabled, falling back cleanly to unstyled text when color is disabled.
  - Execution state: pending

- [ ] E-02 Pass `target_status` and `term` from `status_set.run_set_command` to `render_human`.
  - Depends on: E-01
  - Expected outcome: In `agent_workflows.status_set.run_set_command` (orchestrator readiness reporting loop), update the unready orchestrator reporting loop to call `term.line(_orch_readiness.render_human(r, target_status=target_status, term=term))`. Ensure structured JSON and agent outputs in lines 2985-3016 also carry `target_status` and structured child finding metadata.
  - Execution state: pending

### Task group 2: Approval gate, demotion, reopen, and backstop message polish

- [ ] E-03 Polish and style single-plan approval gate refusals in `plan_readiness.py` and `status_set.py`.
  - Depends on: none
  - Expected outcome: When `agent_workflows.plan_readiness.approval_refusals` reports an unresolved blocking question, extract the question heading or question text from the plan so the message displays both the ID and the question itself. In `agent_workflows.status_set.validate_transition_allowed`, format the refusal with clean bullet points, styled id6 and target status, and eliminate run-on sentences and double periods (`..`).
  - Execution state: pending

- [ ] E-04 Polish backward demotion, terminal reopen, and priority backstop refusal messages in `status_set.py`.
  - Depends on: none
  - Expected outcome:
    1. In `agent_workflows.status_set.run_set_command` (backward demotion missing `--message`), list the specific plan(s) being demoted and their transition (e.g. `- 62pkkg: approved -> to-review`) in human terminal output, and provide a copy-paste retry command with `--message "<reason>"`.
    2. In `agent_workflows.status_set.run_set_command` (terminal reopen check), condense the verbose policy paragraph into a clear summary, listing affected plan IDs with their current terminal status, and display clear next actions for writing a corrective IPD or passing `--allow-terminal-reopen`.
    3. In `agent_workflows.status_set.validate_transition_allowed` (priority/work-kind undecided backstop), format missing fields as a clean bulleted list showing valid choices and the exact remedial command.
  - Execution state: pending

### Task group 3: Regression tests

- [ ] E-05 Add unit tests for all revised refusal and gate output formats.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: New and updated tests in `tests/test_orchestrator_readiness.py` and `tests/test_status_set.py` assert that:
    1. `render_human` with `target_status="approved"` prints `Refusing to set approved for orchestrator ...` and formats child blocking questions with extracted titles.
    2. ANSI styling is applied when `term.color=True` and plain text is emitted when `term.color=False`.
    3. Backward demotion without `--message` names the demoted plan IDs in human terminal output.
    4. Single-plan approval gate refusals format cleanly with quoted blocking questions.
    5. The full test suite (`python3 -m pytest`) passes with zero regressions.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_workflows/orchestrator_readiness.py:render_human` renders human-readable summaries of review readiness using `ReviewReadiness` tuples.
- `agent_workflows/status_set.py:run_set_command` is the unified entry point for `aw set`, `aw ipd set`, `aw specs set`, `aw backlog set`, and `aw prompts set`.
- `agent_workflows/status_set.py:validate_transition_allowed` delegates approval gating to `agent_workflows/plan_readiness.py:approval_refusals`.
- ANSI colors and glyphs are provided by `agent_workflows/term.py:Term`, which provides `color256()`, `status()`, `glyph()`, and lifecycle styling helpers.

## Findings

1. `render_human` in `agent_workflows.orchestrator_readiness.render_human` hardcodes the string `Orchestrator {result.id6} is not ready for review:`, ignoring whether the caller was attempting `aw set to-review`, `aw set reviewed`, or `aw set approved`.
2. When a child fails author lint because of `IPD-Q501` (open blocking question), `render_human` dumps the raw diagnostic `[child-lint-failing] 62pkkg: child 62pkkg fails author lint: IPD-Q501 OQ-06: BLOCKING question is still 'open' ...` without extracting the question title or text.
3. In `agent_workflows.status_set.run_set_command` (orchestrator readiness loop), `run_set_command` calls `_orch_readiness.render_human(r)` without passing `target_status` or the active `term` instance.
4. In `agent_workflows.status_set.run_set_command` (backward plan transition check), the guard fails with a generic summary without naming the demoted plans in human terminal output, forcing the operator to guess which plan triggered the demotion check in a large batch.
5. In `agent_workflows.status_set.validate_transition_allowed` and `agent_workflows.status_set.run_set_command` (terminal reopen check), single-plan approval gate refusals, priority backstops, and terminal reopenings format as dense, unindented run-on strings lacking visual hierarchy.

## Proposed changes (ordered, validatable)

1. Extend `agent_workflows.orchestrator_readiness.render_human` to accept `target_status: str | None = None` and `term: Term | None = None`. Update header and child error formatting to be status-aware, causal, and ANSI styled.
2. In `agent_workflows.orchestrator_readiness`, add a helper to parse and extract the question title/text for `IPD-Q501` child findings.
3. Update `agent_workflows.status_set.run_set_command` to pass `target_status` and `term` into `render_human`.
4. Update `agent_workflows.status_set.validate_transition_allowed`, `agent_workflows.status_set.run_set_command`, and `agent_workflows.plan_readiness.approval_refusals` to produce clean, bulleted, visually styled refusal messages.
5. Add comprehensive unit tests in `tests/test_orchestrator_readiness.py` and `tests/test_status_set.py`.

## Deferred / out of scope (with reason)

- Modifying the underlying validation rules or loosening any approval/orchestrator gates: out of scope; this plan improves message clarity, diagnostic ergonomics, and visual styling without changing the underlying safety invariant.
  - Carrier-Declined: intentional design boundary; this plan focuses solely on refusal message clarity and styling without weakening safety invariants.
- Re-architecting `aw set` selector resolution or dispatch unification (tracked separately in backlog `fcnz1r`): out of scope.
  - Carrier: fcnz1r

## Scope check

- Over-scope: none; confined to message formatting and diagnostic rendering in `orchestrator_readiness.py`, `status_set.py`, `plan_readiness.py`, and test files.
- Under-scope: covers both orchestrator readiness gating (the direct issue encountered) and the surrounding status setter refusal surfaces.

## Required tests / validation

- Unit tests in `tests/test_orchestrator_readiness.py` covering:
  - `render_human` with `target_status="approved"` producing `Refusing to set approved for orchestrator ...`.
  - Child failure formatting explaining parent orchestrator constraint.
  - Blocking question title/text extraction from child plan text.
  - ANSI color formatting enabled vs disabled.
- Unit tests in `tests/test_status_set.py` covering:
  - Backward demotion naming specific demoted plans in human output.
  - Single-plan approval refusal formatting with quoted blocking question.
  - Terminal reopen refusal formatting.
- Bare test suite `python3 -m pytest` passes with zero regressions.

## Spec / documentation sync

- `N/A with reason`: Diagnostic and error message formatting updates do not alter the lifecycle state machine or specification contracts in `specs/`.

## Open questions

### OQ-01: How should `render_human` format output when ANSI colors are disabled or stdout is not a TTY?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED. `render_human` must consult `term.color` (or `sys.stdout.isatty()`). When color is enabled, it applies bold and ANSI 256 colors to id6s, setids, and status tokens. When color is disabled (`--no-color` or piped stdout), it renders clean, plain text without ANSI escape sequences, preserving machine parsability and log readability.

### OQ-02: Should `render_human` read child plan files directly to extract blocking question text?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED. For child plans that fail with `IPD-Q501`, the child file path is already known to `orchestrator_readiness.review_readiness` (via `active_membership.children`). A lightweight helper can extract the question heading (e.g. `### OQ-06: <title>`) from the child plan text. If the file cannot be read or the pattern does not match, it gracefully falls back to the clean diagnostic code without failing.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste python3 session or pytest output demonstrating `render_human` with `target_status="approved"` emitting status-aware header, causal parent-child explanation, extracted blocking question title, and color-styled vs unstyled output.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff -- agent_workflows/status_set.py` showing `target_status` and `term` passed to `render_human` in line 3019, and structured payload updated.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste test output demonstrating single-plan approval refusal formatting with quoted blocking question and clean bulleted layout.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste test output demonstrating backward demotion refusal naming demoted plans, terminal reopen refusal listing affected plans, and priority backstop listing missing fields.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste full pytest output (`python3 -m pytest`) showing new test cases passing and zero regressions across the suite.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is ONE cohesive change addressing the diagnostic clarity and visual ergonomics of refusal messages across the status setter and orchestrator readiness surfaces. Execution requires explicit human approval first; this plan is authored `to-review`. Commit through `aw commit juu1rj -- <paths>` with only this plan's declared paths.
