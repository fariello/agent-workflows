# IPD: Record the findings when a finalize or retirement lint refuses

- Date: 2026-10-06
- Kind: child
- Concern: When the post-transition lint refused the retirement of `1f4faf` on 2026-10-06, the run recorded only "the lifecycle commit f723865c6304 exists but post-transition validation failed", with no finding code or message, so finding the cause took a reconstruction of the run's start-time code. The findings existed: `ipd_lifecycle._complete_after_commit` returns them in the result's `findings` tuple and in `evidence["post_transition"]["diagnostics"]`, but its message text omits them, and `runner_shared.dispatch_orchestrator_item` records only `result.message` (as `retirement transition refused: {why}`). The child finalize path is better: `driver_finalize` parses the finalize command's `--json` payload and appends each diagnostic's rule and detail. Spec `25kzda` 4.1 as amended by Order 01 (A.3) requires every lint refusal at begin, finalize or retirement to carry each finding's code and message in the refusal text, the durable refusal record and `aw runs`.
- Scope: IN: make every `FinalizeResult` message that reports a lint-checkpoint refusal (the post-transition COMMITTED-INCOMPLETE message in `_complete_after_commit`, and the pre-transition refusal message in the finalize and retirement paths) append its findings, one per line, as `  <code> <message>`, capped at 20 with a count of the rest; make `dispatch_orchestrator_item` include `result.findings` in the refusal detail it records; check that `aw runs` renders the recorded refusal detail without truncating the finding lines (it renders `refusal_of_item`); tests. OUT: changing which findings a lint produces; the restart (Order 03).
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/runner_shared.py, tests/test_finalize_refusal_findings.py
- Item-Dependencies: executed:0bjke0
- Status: to-review
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: runfresh
- Order: 4
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: vvqr34

## Workflow history

- 2026-10-06 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 04 of Set `runfresh`. Implements spec `25kzda` 4.1 as amended by Order 01 (A.3). Independent of Orders 02 and 03.

## Goal

Make every finalize or retirement refusal caused by a lint checkpoint say which findings caused it, wherever the refusal is shown.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: carry the findings

- [ ] E-01 In `ipd_lifecycle`, add one helper `_findings_suffix(findings)` that renders up to 20 findings as `\n  <code> <message>` lines (the findings are already strings of the form `"<code> <message>"` in `evidence[...]["diagnostics"]`) plus `\n  ... and N more` when capped, and append it to every `FinalizeResult` message that reports a lint-checkpoint refusal: the post-transition COMMITTED-INCOMPLETE message in `_complete_after_commit`, and the pre-transition gate refusal messages in `finalize` and `retire_orchestrator`. Leave the first line of each message unchanged so existing callers and tests that match it keep working.
  - Depends on: none
  - Expected outcome: a finalize or retirement that fails post-transition lint with three findings returns a message whose first line is unchanged and whose next three lines name each finding's code and message.
  - Execution state: pending

- [ ] E-02 In `runner_shared.dispatch_orchestrator_item`, when the retirement result is a refusal, include the result's message (now carrying findings) in full in the `retirement transition refused: ...` detail and in the recorded refusal's reason; confirm `aw runs <run-id>` and the run summary's diagnostics block render those lines. If either truncates to one line, make it keep the finding lines (up to the same cap), changing only the rendering of refusal detail.
  - Depends on: E-01
  - Expected outcome: a refused retirement's `state.json` refusal reason, its `orchestrator-deferred` event detail and `aw runs` output each contain every finding code.
  - Execution state: pending

### Task group 2: pin it

- [ ] E-03 Add `tests/test_finalize_refusal_findings.py`: a fixture orchestrator whose Set's children are `executed` and whose file carries a metadata field the linter rejects at post-transition (an unknown field, as on 2026-10-06), retired through `dispatch_orchestrator_item` with the real `retire_orchestrator`, asserting the recorded refusal and the event detail contain the `IPD-M103` code and the field name; a child `aw ipd finalize` subprocess case refusing at pre-transition, asserting its findings appear in the message; a cap case with 25 findings. Prove the test can fail by removing the suffix call and pasting the failure.
  - Depends on: E-02
  - Expected outcome: the new file passes; the mutation fails it; existing finalize and retirement tests pass (their first-line matches are unchanged).
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE CHILD FINALIZE PATH ALREADY CARRIES FINDINGS: `driver_finalize` reads `parse_finalize_payload(result.stdout)` and appends `f"  {rule} {detail}"` per diagnostic. The retirement path calls `retire_orchestrator` in process and has no such step, which is the gap.
- `refusal_of_item` IS THE ONE READER of a recorded refusal (`render_stream`), used by `aw runs` and the run summary.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The findings are computed and dropped. `_complete_after_commit` sets `evidence["post_transition"]["diagnostics"]` and returns them as `FinalizeResult.findings`, while its message says only "post-transition validation failed". | `_complete_after_commit` |
| F-02 | The retirement caller records only the message. `dispatch_orchestrator_item` builds `detail=f"retirement transition refused: {why}"` from `result.message`. | `dispatch_orchestrator_item`'s RETIRE branch |
| F-03 | The 2026-10-06 record confirms it: the `orchestrator-deferred` event for `1f4faf` and its `state.json` refusal carry no finding code. | `run-20261006T134924Z-332833/events.jsonl` and `state.json` |

## Proposed changes (ordered, validatable)

1. One findings-suffix helper appended to every lint-refusal message in `ipd_lifecycle` (E-01).
2. Carry the full message into the retirement refusal record and confirm the renderers show it (E-02).
3. Tests with the 2026-10-06 shape and a mutation proof (E-03).

## Deferred / out of scope (with reason)

- RE-RUNNING A REFUSED RETIREMENT AUTOMATICALLY. Measured: the 2026-10-06 refusal was caused by outdated in-process code, which a retry in the same process repeats exactly; Order 03 fixes the cause.
  - Carrier-Declined: a retry on the same code cannot change the answer

## Scope check

- Over-scope: none. Two production modules, one test file.
- Under-scope: none known.

## Required tests / validation

- Baseline bare `python3 -m pytest` before editing.
- `python3 -m pytest -o addopts="" tests/test_finalize_refusal_findings.py tests/test_orchestrator_retirement.py tests/test_ipd_lifecycle.py -q` pasted (skip any of the latter that does not exist and say so).
- Mutation run pasted.
- Bare `python3 -m pytest` after, reconciled; `aw ipd lint` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

Implements spec `25kzda` 4.1 as amended by Order 01 (A.3). No spec edited here.

## Open questions

### OQ-01: Why cap at 20 findings?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: 20 keeps a refusal readable in a terminal and in `aw runs` while covering every measured case (the 2026-10-06 refusal had 3); the remainder is counted, and the full list stays in the finalize evidence for anyone who needs it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the helper and each message it was appended to, and test output showing a three-finding refusal's full message with its unchanged first line.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `dispatch_orchestrator_item` diff and, from the test, the recorded refusal reason, the event detail, and the `aw runs` output each containing `IPD-M103`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the new test file passing with its count; the mutation failing and the revert passing; existing finalize and retirement tests passing; a grep for source-structure reads returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only declared paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Commit only declared paths through `aw commit <plan> -- <paths>`; never push. Paste actual output. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.
