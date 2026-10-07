# IPD: Record the findings when a finalize or retirement lint refuses

- Date: 2026-10-06
- Kind: child
- Concern: When the post-transition lint refused the retirement of `1f4faf` on 2026-10-06, the run recorded only "the lifecycle commit f723865c6304 exists but post-transition validation failed", with no finding code or message, so finding the cause took a reconstruction of the run's start-time code. The findings existed: `ipd_lifecycle._complete_after_commit` returns them in the result's `findings` tuple and in `evidence["post_transition"]["diagnostics"]`, but its message text omits them, and `runner_shared.dispatch_orchestrator_item` records only `result.message` (as `retirement transition refused: {why}`). The child finalize path ALREADY carries them: `ipd_lifecycle.run_finalize`'s `_emit` turns every `result.findings` entry into an `IPD-FINALIZE` diagnostic (printed as `  <rule> <detail>` in human mode, and in the `--json` payload), and `runner_shared.driver_finalize` re-appends each diagnostic's rule and detail to the recorded refusal. So the gap is ONLY the in-process retirement caller. Spec `25kzda` 4.1 as amended by Order 01 (A.3) requires every lint refusal at begin, finalize or retirement to carry each finding's code and message in the refusal text, the durable refusal record and `aw runs`.
- Scope: IN: in `runner_shared`, one helper that renders a refusal's findings as a single line (`findings (N): <f1>; <f2>; ...`, capped at 20 with `; ... and K more`), applied in `dispatch_orchestrator_item`'s RETIRE-refused branch so the `retirement transition refused: ...` detail (and therefore the recorded `Refusal` reason, `orchestrator_refusal_detail`, and the `orchestrator-deferred` event detail) names every finding; confirm by observation that `aw runs` and the run summary's diagnostics block render it; tests, including a guard that the child `aw ipd finalize` path prints each finding exactly once. OUT: changing any `FinalizeResult.message` in `ipd_lifecycle` (the CLI already renders `findings` as diagnostics, so appending them to the message would print every finding twice; review PR-001); changing which findings a lint produces; changing any renderer (measured at review: neither truncates a refusal reason); the restart (Order 03).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_finalize_refusal_findings.py
- Item-Dependencies: executed:0bjke0
- Status: reviewed
- Readiness: go-pending-approval
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

- 2026-10-07 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED
- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-10-06 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 04 of Set `runfresh`. Implements spec `25kzda` 4.1 as amended by Order 01 (A.3). Independent of Orders 02 and 03.

## Goal

Make every finalize or retirement refusal caused by a lint checkpoint say which findings caused it, wherever the refusal is shown.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: carry the findings

- [ ] E-01 In `runner_shared`, add one helper `refusal_findings_text(findings, cap=20)` that returns `""` for no findings and otherwise ONE line, `findings (N): <f1>; <f2>; ...`, listing at most `cap` findings (each already a `"<code> <message>"` string, as `FinalizeResult.findings` carries them) and ending `; ... and K more` when capped. One line, not one per finding, because the run summary's diagnostics block renders a reason inside a single `  • <id6>: <status> (<reason>)` line (`render_stream.render_run_summary_table`), and `render_stream.refusal_of_item`'s legacy arm already flattens multi-line reasons for exactly that reason. Then, in `dispatch_orchestrator_item`'s RETIRE branch where `why` is built from `result.message`, append `" " + refusal_findings_text(getattr(result, "findings", ()) or ())` when it is non-empty, so the `retirement transition refused: ...` detail, and through it the `Refusal` reason, `orchestrator_refusal_detail`, and the `orchestrator-deferred` event detail, name every finding. Use `getattr` because the existing test double in `tests/test_orchestrator_retirement.py` (the `_No` class in the four-causes test) has no `findings` attribute. Typed rollup refusals (`ROLLUP_REFUSED_*` codes such as `set-ineligible`) are findings too and will be listed the same way; that is intended. Do NOT change any `FinalizeResult.message` in `ipd_lifecycle` (review PR-001).
  - Depends on: none
  - Expected outcome: a retirement refused at post-transition lint with three findings records a detail whose text is the unchanged `retirement transition refused: <message>` followed by `findings (3): ...` naming each code and message; a result with no findings records exactly the old detail.
  - Execution state: pending

- [ ] E-02 Confirm by observation, without changing any renderer, that the refusal detail reaches every reading surface: `aw runs --dir <fixture>` (the `Refusals (what the run declined, and what to do):` block from `run_viewer.format_refusal_summary`), `aw runs --json` (`issue_reasons` / `refusal`), and `render_stream.render_run_summary_table`'s diagnostics block. Measured at review against the current code: none truncates a reason. If execution finds one that does, fix only that renderer's handling of the reason and add it to `- Scope-Paths:` with the reason recorded (the finalize scope gate will require a `--scope-reason`).
  - Depends on: E-01
  - Expected outcome: each of the three surfaces shows the `IPD-M103` code and the offending field name for the fixture refusal.
  - Execution state: pending

### Task group 2: pin it

- [ ] E-03 Add `tests/test_finalize_refusal_findings.py` with: (a) a git-backed fixture Set (one `executed` child, an `approved` orchestrator carrying a coverage record written with `coverage_record.write(..., verdict=coverage_record.COVERAGE_PASS, commit=False)` so the retirement re-check asks no model, and an extra unknown front-matter field such as `- Bogus-Field: x`, committed), dispatched through `runner_shared.dispatch_orchestrator_item` with the REAL `retire_orchestrator` and a run dir under `runner_shared.state_root(<fixture>)`, asserting outcome `terminate`/`finalize-refused` and that `refusal_of_item(item).reason`, `item["orchestrator_refusal_detail"]`, the `orchestrator-deferred` event detail in `events.jsonl`, and `aw runs --dir <fixture> --no-color` stdout (subprocess, after writing `state.json`) each contain `IPD-M103` and `Bogus-Field`; (b) a no-findings case (a result double with empty `findings`) whose detail equals the old text exactly; (c) a cap case calling `refusal_findings_text` with 25 findings, asserting 20 listed and `and 5 more`; (d) a child `aw ipd finalize --apply` subprocess on a fixture plan that has a begin receipt but pending `E-*` items, asserting each `IPD-S404` finding line appears in stdout EXACTLY ONCE (guards against the double-print PR-001 removed). The fixture may reuse the plan-writing helpers in `tests/test_orchestrator_retirement.py` (`_write_conforming_plan`, `_init_git_repo`) by import or copy them. Prove the test can fail by removing the E-01 append and pasting the failure.
  - Depends on: E-02
  - Expected outcome: the new file passes; with the append removed, case (a) fails; existing finalize and retirement tests pass unchanged.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE CHILD FINALIZE PATH ALREADY CARRIES FINDINGS, TWICE OVER: `ipd_lifecycle.run_finalize`'s `_emit` renders each `result.findings` entry as an `IPD-FINALIZE` diagnostic (`print(f"  {d.rule} {d.detail}")` in human mode, `diagnostics` in `--json`), and `runner_shared.driver_finalize` reads `parse_finalize_payload(result.stdout)` and appends `f"  {rule} {detail}"` per diagnostic. So appending findings to the MESSAGE would print each one twice on that path. The retirement path calls `retire_orchestrator` in process and has no such step, which is the only gap.
- `runner_shared.finalize_refusal_is_retryable` parses finding lines out of the child finalize refusal by their `IPD-` prefix; this plan does not touch that text, so the retry classifier is unaffected.
- `refusal_of_item` IS THE ONE READER of a recorded refusal (`render_stream`), used by `aw runs` and the run summary.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The findings are computed and dropped. `_complete_after_commit` sets `evidence["post_transition"]["diagnostics"]` and returns them as `FinalizeResult.findings`, while its message says only "post-transition validation failed". | `_complete_after_commit` |
| F-02 | The retirement caller records only the message. `dispatch_orchestrator_item` builds `detail=f"retirement transition refused: {why}"` from `result.message`. | `dispatch_orchestrator_item`'s RETIRE branch |
| F-03 | The 2026-10-06 record confirms it: the `orchestrator-deferred` event for `1f4faf` and its `state.json` refusal carry no finding code. | `run-20261006T134924Z-332833/events.jsonl` and `state.json` (the run dir lives in the main checkout's state root; not present in a review lane) |
| F-04 | Reproduced at review: a fixture orchestrator carrying `- Bogus-Field: x`, dispatched through `dispatch_orchestrator_item` with the real `retire_orchestrator`, returned `findings=('IPD-M103 Bogus-Field: unknown field',)` while the recorded detail, the `Refusal` reason, the `orchestrator-deferred` event and `aw runs`' Refusals block all read only "post-transition validation failed". `aw runs` printed the reason in full (no truncation). | review probe, `/plan-review` round 1 |
| F-05 | The CLI already prints findings: `run_finalize`'s `_emit` emits one `  IPD-FINALIZE <finding>` line per `result.findings` entry, so the message must not also carry them. | `ipd_lifecycle.run_finalize` `_emit`; `runner_shared.driver_finalize` |

## Proposed changes (ordered, validatable)

1. One single-line findings helper in `runner_shared`, appended to the retirement refusal detail in `dispatch_orchestrator_item` (E-01).
2. Confirm by observation that `aw runs`, `aw runs --json` and the run summary show it (E-02).
3. Tests with the 2026-10-06 shape and a mutation proof (E-03).

## Deferred / out of scope (with reason)

- RE-RUNNING A REFUSED RETIREMENT AUTOMATICALLY. Measured: the 2026-10-06 refusal was caused by outdated in-process code, which a retry in the same process repeats exactly; Order 03 fixes the cause.
  - Carrier-Declined: a retry on the same code cannot change the answer

## Scope check

- Over-scope: none. One production module, one test file. (Editing `ipd_lifecycle` messages was removed at review: PR-001.)
- Under-scope: none known.

## Required tests / validation

- Baseline bare `python3 -m pytest` before editing.
- `python3 -m pytest -o addopts="" tests/test_finalize_refusal_findings.py tests/test_orchestrator_retirement.py tests/test_ipd_lifecycle_cli.py tests/test_finalize_sendback.py tests/test_runner_finalize_message.py -q` pasted.
- Mutation run pasted.
- Bare `python3 -m pytest` after, reconciled; `aw ipd lint` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

Implements spec `25kzda` 4.1 as amended by Order 01 (A.3). No spec edited here.

## Open questions

### OQ-01: Why cap at 20 findings?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: 20 keeps a refusal readable in a terminal and in `aw runs` while covering every measured case (the 2026-10-06 refusal had 3); the remainder is counted, and the full list stays in `FinalizeResult.findings` and the finalize evidence for anyone who needs it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the `runner_shared` diff (the helper and the one append in `dispatch_orchestrator_item`), `git diff --stat -- agent_workflows/ipd_lifecycle.py` showing no change, and test output showing a refused retirement's detail beginning with the unchanged `retirement transition refused: ` text followed by `findings (N): ` naming each finding, plus the no-findings case's detail equal to the old text.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste, from the fixture refusal, the `aw runs --dir <fixture> --no-color` Refusals block, the `aw runs --json` `refusal`/`issue_reasons` entry, and the `render_run_summary_table` diagnostics line, each containing `IPD-M103` and the field name; state whether any renderer had to change (expected: none).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the new test file passing with its count; the mutation (E-01 append removed) failing case (a) and the revert passing; case (d)'s assertion that each `IPD-S404` line appears exactly once; existing finalize and retirement tests passing; a grep of the new file for `inspect`, `ast.`, `read_text` on `agent_workflows/` sources returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only declared paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Open questions: all resolved. Scope fence: `- Scope-Paths:` declares the change; an out-of-scope edit (for example a renderer under E-02's contingency) is made and then justified with `--scope-reason` at finalize. Commit only declared paths through `aw commit <plan> -- <paths>`; never push. You MUST paste the actual runner output for every test claim. Lifecycle: under a runner, the runner owns begin/finalize; by hand, finish with `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms; never `git mv` the plan by hand.
