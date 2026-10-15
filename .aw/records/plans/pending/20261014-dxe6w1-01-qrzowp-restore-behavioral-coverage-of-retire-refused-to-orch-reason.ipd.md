# IPD: Restore behavioral coverage of RETIRE_REFUSED to ORCH_REASON translation and the unrecognized-reason fallback

- Date: 2026-10-14
- Kind: child
- Concern: Two properties of the orchestrator refusal path lost their only guard when `tests/test_orchestrator_deferral_reporting.py` was deleted in `19313eed7` (yuhl6o sites S-10, S-11): (a) `runner_shared.decide_orchestrator_dispatch` translates every `RETIRE_REFUSED_*` value produced by `evaluate_set_retirement` into an `ORCH_REASON_*` value that `orchestrator_refusal_text` maps, including the near-miss pair `unfinished-children` versus `children-unfinished`; and (b) `orchestrator_refusal_text` reports an unrecognized or empty code verbatim with a non-empty, renderable reason and remedy instead of raising.
- Scope: Add one new behavioral test module that builds temp-repo Set fixtures, drives the real `evaluate_set_retirement`, `decide_orchestrator_dispatch`, `dispatch_orchestrator_item`, and `orchestrator_refusal_text`, and asserts on their returned values and the item's rendered `Refusal`. Test-only; no production change.
- Scope-Paths: tests/test_orchestrator_refusal_reason_translation.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: dxe6w1
- Set: dxe6w1
- Order: 1
- Highest E allocated: 04
- Author: OpenCode Claude Opus
- Id: qrzowp

## Workflow history
- 2026-10-15 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006

- 2026-10-15 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006
- 2026-10-14 draft (OpenCode Claude Opus): created.
- 2026-10-14 to-review (OpenCode Claude Opus): authored from backlog `dxe6w1`; Step 0 evidence gathered; ready for `/plan-review`.

## Goal

Restore, as behavior-only tests, the guard that the retirement-refusal vocabulary (`RETIRE_REFUSED_*`) never reaches the reporting mapping untranslated, and that the reporting mapping's unknown-code fallback is verbatim, non-empty, and non-raising (yuhl6o S-10 and S-11).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Translation at the dispatch decision (S-10)

- [ ] E-01 Create `tests/test_orchestrator_refusal_reason_translation.py` with a temp-repo fixture helper (pattern: `tests/test_orchestrator_not_approved_reason.py` `_make_repo`, writing plans under `.aw/records/plans/pending/` with `- Id:`, `- Set:`, `- Order:`, `- Kind:`, `- Status:` and, where the branch needs one, an orchestrator child table under the EXACT heading `## Child IPDs, sequence, and dependencies` (`runner_shared._CHILD_IPDS_HEADING`) with an `| Order | Id | Child |` header and one row per declared Order; a shorter `## Child IPDs` heading is NOT parsed and refuses every Set as `unauthored-child-rows`, verified at review) and a table-driven test, one `subTest` per retirement-refusal branch, that builds the Set shape which makes `runner_shared.evaluate_set_retirement` refuse with each of its four reasons: no orchestrator (children only), no children (orchestrator only), unauthored child row (table declares Orders `01` and `02` while only the Order-01 child exists on disk with `- Status: executed`, because the unfinished-children check runs BEFORE the unauthored-row check and a non-terminal child would mask it; verified during authoring), and unfinished children (one `approved` child on disk, present in the queue with run status `queued`, table declaring only Order `01`). For each, assert that `evaluate_set_retirement(repo, setid).reason` is the expected `RETIRE_REFUSED_*` constant (compared to the module constant, never to a string literal), that `decide_orchestrator_dispatch(...)` (with `terminal_states=runner_shared.TERMINAL_STATES`, `success_states=oc_runipd.EXECUTION_SUCCESS_STATES`) returns the expected `ORCH_REASON_*` constant and outcome (`ORCH_DISPATCH_TERMINATE` for the first three, `ORCH_DISPATCH_RECONSIDER` for unfinished), and that `orchestrator_refusal_text(decision.reason)[0]` does not contain `THIS VERSION OF THE RUNNER DOES NOT RECOGNIZE`. Add one control subtest: the Order-01-only table with that child `executed` makes `evaluate_set_retirement(...).eligible` True, proving the fixture's table is parsed (so the unauthored-row subtest refuses because of the missing Order-02 child and not because of an unparseable table). Expected mapping, measured at review on `461fdf679`: `no-orchestrator -> no-orchestrator`, `no-children -> no-children`, `unauthored-child-rows -> unauthored-child-rows` (all TERMINATE), `unfinished-children -> children-unfinished` (RECONSIDER).
  - Depends on: none
  - Expected outcome: every refusal that `evaluate_set_retirement` can produce reaches the reporting mapping as a mapped code with the expected outcome; the unfinished-children branch observably yields `ORCH_REASON_UNFINISHED_CHILDREN` (RECONSIDER) from an input of `RETIRE_REFUSED_UNFINISHED_CHILDREN`; the eligible control passes.
  - Execution state: pending

- [ ] E-02 Add a test in the same file proving the translation end to end through the read surface: drive the real `runner_shared.dispatch_orchestrator_item` for the unfinished-children fixture (orchestrator `queued`, child `queued`, `state.json` written as in `test_case_08_read_surface_via_dispatch_orchestrator_item`), then assert the returned decision's `outcome` is `runner_shared.ORCH_DISPATCH_RECONSIDER` and `orch_item["status"]` is still `queued` (RECONSIDER writes no status), `render_stream.refusal_of_item(orch_item)` is not None, its `code` equals `runner_shared.ORCH_REASON_UNFINISHED_CHILDREN`, its `code` does not equal `runner_shared.RETIRE_REFUSED_UNFINISHED_CHILDREN`, and its `reason` does not contain `NOT RECOGNIZE`; and that `runner_shared.orchestrator_refusal_text(runner_shared.RETIRE_REFUSED_UNFINISHED_CHILDREN)[0]` DOES contain `NOT RECOGNIZE`, which demonstrates that forwarding the untranslated value would degrade the rendered refusal to the fallback.
  - Depends on: E-01
  - Expected outcome: the refusal an operator reads for a deferred orchestrator carries the translated, mapped code, and the untranslated value is observably not mapped.
  - Execution state: pending

### Task group 2: Unrecognized-reason fallback (S-11)

- [ ] E-03 Add a test calling `runner_shared.orchestrator_refusal_text("some-future-reason")` and asserting: the call does not raise; both returned strings are non-empty after `strip()`; the reason contains `THIS VERSION OF THE RUNNER DOES NOT RECOGNIZE` and the verbatim code `some-future-reason`; the remedy contains the verbatim code and `events.jsonl`; and `render_stream.Refusal(code="some-future-reason", reason=reason, remedy=remedy)` constructs without raising and round-trips the code.
  - Depends on: none
  - Expected outcome: an unknown code produces a loud, actionable, renderable record rather than an exception or generic prose.
  - Execution state: pending

- [ ] E-04 Add a test calling `runner_shared.orchestrator_refusal_text` with `""` and with `None` and asserting each returns two non-empty strings, the reason contains `(no reason recorded)` and `NOT RECOGNIZE`, and the pair constructs a `render_stream.Refusal` without raising (use `code="(no reason recorded)"` or any non-empty code for the record itself: `Refusal` refuses an empty `code`, verified at review, so the test must not pass the raw `""` as `code`).
  - Depends on: E-03
  - Expected outcome: an empty or missing reason is handled by the fallback rather than raising or producing an empty field that `Refusal` would refuse.
  - Execution state: pending

## Project conventions discovered (Step 0)

- P16 / AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE": every E-item calls the real functions and asserts on their return values and the rendered refusal record; no `inspect`/`ast`/source reading. The deleted test's bare constant-value assertions (`RETIRE_REFUSED_UNFINISHED_CHILDREN == "unfinished-children"`, the three-shared-values set intersection) pin literals rather than behavior and are deliberately NOT restored; the translation is instead asserted by driving `decide_orchestrator_dispatch` from a real `evaluate_set_retirement` refusal.
- Fixture recipe: `tests/test_orchestrator_not_approved_reason.py` (`TestOrchestratorNotApprovedReason._make_repo`, `_decide`, `test_case_08_read_surface_via_dispatch_orchestrator_item`) builds temp repos and drives `decide_orchestrator_dispatch` / `dispatch_orchestrator_item` with `runner_shared.TERMINAL_STATES` and `oc_runipd.EXECUTION_SUCCESS_STATES`; the new module reuses that recipe (copied, not imported, to keep test modules independent).
- No live `.aw/records/runs/` state is read; that tree is gitignored and absent in lane worktrees (recorded in the deleted module's docstring and `tests/test_run_viewer.py`).
- Suite is run bare: `python3 -m pytest` (repo-local development contract). Narrowed runs use `python3 -m pytest -o addopts="" <file>`.
- Code cited by symbol: `runner_shared.evaluate_set_retirement`, `runner_shared.decide_orchestrator_dispatch`, `runner_shared.dispatch_orchestrator_item`, `runner_shared.orchestrator_refusal_text`, `runner_shared._ORCH_REASON_TEXT`, `render_stream.Refusal`, `render_stream.refusal_of_item`.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The guard was deleted in `19313eed7`. | `git show 19313eed7^:tests/test_orchestrator_deferral_reporting.py` contains `ReasonMappingTests.test_the_mapping_is_keyed_on_ORCH_REASON_and_the_other_vocabulary_is_translated`, `test_an_unknown_code_is_reported_verbatim_and_never_empty`, and `test_an_empty_reason_is_still_handled`. |
| F-2 | yuhl6o recorded S-10 and S-11 as RETIRE-UNGUARDED, removed by `19313eed`. | `.aw/records/plans/executed/20261011-iosmvn-01-yuhl6o-retire-or-repoint-the-residual-dangling-test-citations-in-ru.ipd.md`, S-10 and S-11 rows. |
| F-3 | The only live caller-tests of `orchestrator_refusal_text` assert two mapped codes and only NEGATIVE fallback assertions. | `tests/test_orchestrator_not_approved_reason.py` `test_case_06_orchestrator_refusal_text_new_code`, `test_case_07_orchestrator_refusal_text_old_code_still_mapped`. |
| F-4 | Production comments state the gap explicitly. | `runner_shared` comment above `_ORCH_REASON_TEXT`: "deleted in `19313eed`; no live guard currently asserts this translation"; `orchestrator_refusal_text` docstring: "no live guard currently asserts this fallback". |
| F-5 | The translation is a branch ladder in `decide_orchestrator_dispatch`: `RETIRE_REFUSED_NO_CHILDREN` -> `ORCH_REASON_NO_CHILDREN`, `RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS` -> `ORCH_REASON_UNAUTHORED_CHILD_ROWS`, `RETIRE_REFUSED_NO_ORCHESTRATOR` -> `ORCH_REASON_NO_ORCHESTRATOR`, and the fall-through `RETIRE_REFUSED_UNFINISHED_CHILDREN` split into `ORCH_REASON_CHILDREN_NOT_APPROVED` / `ORCH_REASON_DEAD_CHILDREN` / `ORCH_REASON_UNFINISHED_CHILDREN` / `ORCH_REASON_CHILDREN_NOT_IN_RUN`. | `runner_shared.decide_orchestrator_dispatch` body. |
| F-6 | The fallback names the code verbatim, substitutes `(no reason recorded)` for an empty code, and points at `events.jsonl`. | `runner_shared.orchestrator_refusal_text` body. |

## Proposed changes (ordered, validatable)

1. E-01: table-driven translation test over the four `evaluate_set_retirement` refusal branches.
2. E-02: end-to-end read-surface test through `dispatch_orchestrator_item` and `refusal_of_item`, plus the demonstration that the untranslated code would hit the fallback.
3. E-03: unknown-code fallback test.
4. E-04: empty/None-code fallback test.

## Deferred / out of scope (with reason)

- Editing the production comments saying "no live guard currently asserts this" (the `runner_shared` comment above `_ORCH_REASON_TEXT` and the `orchestrator_refusal_text` docstring): production source outside Scope-Paths and a comment edit, not behavior. The same stale phrase appears in roughly 50 production comments repo-wide (review grep), so editing two of them here would be piecemeal.
  - Carrier-Declined: comment-only text with no behavioral effect; a repo-wide sweep of the `19313eed` "no live guard" comments is a separate housekeeping decision, not an obligation this coverage restoration creates.
- The deleted module's other classes (`DeferralRecordTests`, `TerminateRecordTests`, `StaleDeferralRecordTests`) and the remaining `ReasonMappingTests` prose checks (distinctness, verbs, no `--full-auto`, no host command): not the property this backlog item names (S-10/S-11 only).
  - Carrier-Declined: yuhl6o classified only S-10 and S-11 as needing restoration for this item; the other deleted classes are outside backlog `dxe6w1`'s stated property.
- Literal constant-value pins from the deleted test: code-pinning under P16; replaced by behavioral translation assertions (see Step 0).
  - Carrier-Declined: prohibited by P16 (AGENTS.md "NO CODE-PINNING TESTS"); deliberately never restored.

## Scope check

- Over-scope: none.
- Under-scope: none; S-10 (translation) is asserted at the decision (E-01) and at the read surface (E-02), S-11 (fallback) for unknown (E-03) and empty/None (E-04) codes.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_orchestrator_refusal_reason_translation.py -v` shows every new test passing.
- Mutation check A (S-10; temporary, not committed, reverted): in a scratch edit of `runner_shared.decide_orchestrator_dispatch`, return `reason=decision.reason` on the RECONSIDER branch instead of `ORCH_REASON_UNFINISHED_CHILDREN`, and confirm E-01's unfinished-children subtest and E-02 FAIL; revert and confirm they pass.
- Mutation check B (S-11; temporary, not committed, reverted): in a scratch edit of `runner_shared.orchestrator_refusal_text`, replace the fallback `return (...)` with `raise KeyError(reason)`, and confirm the E-03 and E-04 tests FAIL; revert and confirm they pass.
- After both reverts, `git diff -- agent_workflows/` is empty.
- Full suite bare: `python3 -m pytest` passes with no new failures.

## Spec / documentation sync

N/A: test-only change restoring coverage; no spec or user-facing behavior changes.

## Open questions

### OQ-01: Should the restored coverage revive the deleted file name or live in a new module?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: a new module, `tests/test_orchestrator_refusal_reason_translation.py`, named for the property it guards; reviving `tests/test_orchestrator_deferral_reporting.py` would imply restoring the whole deleted module, which the suite trim deliberately removed and which is out of scope (F-1, Deferred).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_orchestrator_refusal_reason_translation.py -v` output showing the E-01 test PASSED (all four refusal subtests plus the eligible control); plus pasted output of mutation check A (RECONSIDER branch forwarding `decision.reason`) showing the unfinished-children subtest FAILED, then passing after revert, and a pasted empty `git diff -- agent_workflows/` after revert.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output showing the E-02 test PASSED and also FAILING under mutation check A, and the test source excerpt showing the call to `runner_shared.dispatch_orchestrator_item` (the code path producing the dispatch observation) followed by `render_stream.refusal_of_item(orch_item)` and the code/`NOT RECOGNIZE` assertions.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output showing the E-03 unknown-code test PASSED, and FAILING under mutation check B (fallback replaced by `raise KeyError(reason)`) then passing after revert, and the test source excerpt showing the verbatim-code, `events.jsonl`, and `render_stream.Refusal` construction assertions.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted pytest output showing the E-04 empty/None test PASSED, and FAILING under mutation check B then passing after revert, with a pasted empty `git diff -- agent_workflows/` after revert; plus pasted `python3 -m unittest -v tests.test_orchestrator_refusal_reason_translation` output showing the module also runs under stdlib unittest (the suite's dual-runner contract, `pyproject.toml` "also run under `python -m unittest discover`"); plus pasted output of a bare `python3 -m pytest` run showing the `N passed` summary with no new failures; plus pasted `git diff --stat` and new-file content showing no `inspect`/`ast` import and no read of any `agent_workflows/*.py` source file (P16).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

- **Execution contract**: execute `E-01`..`E-04` in dependency order inside an isolated worktree, only after `- Status: approved`. Open questions: OQ-01 is resolved; none remain open. Mark an `E-*` `performed` only after doing it and a `V-*` `pass` only with concrete pasted evidence; paste the ACTUAL runner output for every test claim and never claim a pass you did not run. Run the full suite bare as `python3 -m pytest` (never `-n0`, an extra `-q`, or `-p no:randomly`). The test module is a `unittest.TestCase` subclass (like `tests/test_orchestrator_not_approved_reason.py`). Mutation checks A and B are temporary edits to `agent_workflows/runner_shared.py` and MUST NOT be committed.
- **Scope fence** (a declaration, not a stop condition): the only declared path is `tests/test_orchestrator_refusal_reason_translation.py`. An edit outside it must be justified at finalize with `--scope-reason <path>=<why>`.
- **Commit**: `aw commit qrzowp -- tests/test_orchestrator_refusal_reason_translation.py` (plus this IPD); never `git add -A`, never push.
- **Post-gate lifecycle move**: once every `E-*` is `performed`, every `V-*` is `pass`, and `aw ipd lint --phase pre-transition` reports no errors, the plan must reach `.aw/records/plans/executed/`: under `aw oc run` / `aw agy run` the runner owns that transition; when executed by hand outside a runner, the executor runs `aw ipd finalize qrzowp`. Never hand-`git mv` the plan.
