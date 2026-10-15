# IPD: Restore behavioral coverage of perform_gate_answer baseline non-refusal and not-mine outcome equivalence

- Date: 2026-10-14
- Kind: child
- Concern: The maintainer's binding ruling (2026-09-08, reaffirmed 2026-09-20) that no programmatic check may refuse a gate-answer verdict on the strength of a suite baseline has had zero behavioral test coverage since commit `19313eed` deleted `tests/test_suite_baseline.py` (class `NothingRefusesOnTheBaseline`); plan `yuhl6o` recorded sites S-16, S-20 and S-21 as RETIRE-UNGUARDED for exactly this property.
- Scope: Add one new behavioral test module that calls `runner_shared.perform_gate_answer` with a stub `ask` and asserts on the returned `GateAnswerOutcome` (`release` and `record`) across corroborating, contradicting, absent and unsupplied baselines, for `not-mine` and `mine` answers, and correct the one now-stale sentence in `runner_shared.perform_gate_answer`'s docstring that says no live guard asserts this property. No behavior change; no source-reading assertions.
- Scope-Paths: tests/test_gate_answer_baseline_indifference.py, agent_workflows/runner_shared.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: xhrpeg
- Set: xhrpeg
- Order: 1
- Highest E allocated: 05
- Author: OpenCode Claude Opus
- Id: tosnwd

## Workflow history
- 2026-10-15 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006

- 2026-10-15 draft (OpenCode Claude Opus): created.
- 2026-10-15 to-review (OpenCode Claude Opus): authored review-ready plan graduating backlog xhrpeg.

## Goal

Restore regression coverage so that any change making `perform_gate_answer` refuse (or rescue) a verdict because of what the baseline contains, or letting the baseline alter any outcome field other than the `suite_baseline` audit record, turns the suite red. Only behavioral outcomes are restored; the deleted file's AST/`inspect` pins (for example `test_NO_CODE_PATH_compares_the_baseline_to_the_post_work_SET`) are deliberately NOT restored (P16).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: not-mine equivalence

- [ ] E-01 Create `tests/test_gate_answer_baseline_indifference.py` with fixtures: `_suite_result()` building `oc_runipd.SuiteCheckResult(passing=False, exit_code=1, ..., failures=("FAILED tests/test_pre_existing.py::T::test_already_red - assert 1 == 2",))`; `_completed(failures)` building `runner_shared.SuiteBaseline(state=runner_shared.SUITE_BASELINE_COMPLETED, ...)`; and `_perform(answer, baseline)` that, in a `tempfile.TemporaryDirectory`, passes an `ask` stub writing `{"schema_version": 1, "disposition": "executed", runner_shared.GATE_ANSWER_KEY: answer}` to the outcome path (every `answer` dict MUST carry a non-empty `reason`: `validate_gate_answer` fails closed on a `not-mine` with no reason, which would make the test fail for the wrong reason) and returning `(0, "ses-1", path, ["stub"])`, then calls `runner_shared.perform_gate_answer(suite_result=..., changed_files=("agent_workflows/term.py",), ask=ask, outcome_path=path, session_id="ses-1", baseline=baseline)`. Add a test that, for `{"answer": "not-mine", ...}`, runs four baselines: corroborating (contains the failing id), contradicting (contains only a different id), `runner_shared.suite_baseline_absent("...")`, and `None`; asserts `release is True` and `record["answer"] == "not-mine"` for all four; and asserts (as `subTest`s per field) that `answer`, `reason`, `usable`, `integrates`, `refuses`, `released`, `awaits_human_decision`, `violation`, `recheck_attempts`, `recheck_passed` and `failing_tests` are equal across all four records.
  - Depends on: none
  - Expected outcome: The test passes against current code. At authoring a prototype of exactly this shape printed `True True True True` for the four releases.
  - Execution state: pending

- [ ] E-02 In the same module, add a test asserting that between a `not-mine` outcome with a completed baseline and one with an absent baseline, the set of differing `record` keys is exactly `{"suite_baseline"}` (a record is not a check); and a symmetric test that a `mine` answer has `release is False` both with a completed baseline and with `None`, with the differing key set again exactly `{"suite_baseline"}` (the baseline must not rescue a refusal either).
  - Depends on: E-01
  - Expected outcome: Both tests pass against current code. At authoring the prototype printed `['suite_baseline'] ['suite_baseline']` for not-mine (vs absent, vs contradicting) and `False False mine ['suite_baseline']` for mine.
  - Execution state: pending

### Task group 2: Prove the coverage is load-bearing

- [ ] E-03 Run an in-memory mutation probe with no source edit: write three pytest plugins in an UNTRACKED scratch directory under the gitignored `.aw/state/` (never committed), each rebinding `runner_shared.perform_gate_answer` at import with a wrapper around the original. Mutant A: when the answer is `not-mine` and `baseline` is completed and does not contain every failing id, return a copy of the outcome with `release=False` and `record["refuses"]=True` (the rejected constraint). Mutant B: when `baseline` is completed and the answer is `mine`, return `release=True` (baseline rescue). Mutant C: when the answer is `not-mine` and the baseline is `None` or not `known`, return `release=False` (the most plausible well-meant 'fail closed on an unknown baseline' change, which the maintainer's 2026-09-20 any-run ruling forbids). Run the new module once per plugin with `PYTHONPATH=.aw/state/<scratch>:. python3 -m pytest -o addopts="" -q -p <plugin> tests/test_gate_answer_baseline_indifference.py` (`-o addopts=""` already disables xdist, so the plugin loads in-process; do not add `-n0`) and confirm each mutant makes at least one test fail, then delete the scratch directory. The test module must call `runner_shared.perform_gate_answer` through the module attribute (not a `from ... import` binding) so the rebinding reaches it.
  - Depends on: E-02
  - Expected outcome: All three mutants are killed (nonzero pytest exit with named failing tests); the unmutated module passes. At review a minimal prototype of this exact mechanism (scratch under `.aw/state/`, deleted after) gave: unmutated `2 passed`; A `1 failed, 1 passed` (`test_not_mine`); B `1 failed, 1 passed` (`test_mine`); C `1 failed, 1 passed` (`test_not_mine`).
  - Execution state: pending

### Task group 3: Regression

- [ ] E-04 In `agent_workflows/runner_shared.py`, in the `perform_gate_answer` docstring paragraph beginning "`baseline` IS PASSED STRAIGHT THROUGH", replace the parenthetical "(deleted in `19313eed`; no live guard currently asserts this)" with a pointer to `tests/test_gate_answer_baseline_indifference.py` as the live behavioral guard (restored by `tosnwd`). Change no other text and no code.
  - Depends on: E-03
  - Expected outcome: a docstring-only diff in `runner_shared.py`; the docstring no longer claims the property is unguarded.
  - Execution state: pending

- [ ] E-05 Run the full fast suite bare (`python3 -m pytest`) and confirm no regressions; commit the new module and the docstring edit via `aw commit tosnwd -- tests/test_gate_answer_baseline_indifference.py agent_workflows/runner_shared.py`.
  - Depends on: E-04
  - Expected outcome: Suite green with the new tests included; one path-scoped commit touching exactly those two paths.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Tests must exercise behavior, not code structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16): no `inspect`/`ast`/regex reads of production source. The deleted class's `test_NO_CODE_PATH_compares_the_baseline_to_the_post_work_SET` and `test_the_baseline_reaches_NO_comparison_in_execute_item_core_either` used `inspect.getsource`/`ast.parse` and are NOT restored.
- `runner_shared.perform_gate_answer` signature (keyword-only): `suite_result`, `changed_files`, `ask`, `outcome_path`, ..., `session_id`, `baseline: SuiteBaseline | None`. Its docstring states `not-mine` releases in any run and `mine` refuses with no override.
- `runner_shared.SuiteBaseline` (NamedTuple) and `runner_shared.suite_baseline_absent(reason, *, base_commit="")` construct baselines; `runner_shared.SUITE_BASELINE_COMPLETED` is the completed state.
- Sibling behavioral test `tests/test_gate_answer_record_released.py` drives `perform_gate_answer` with stub `ask`; `tests/test_suite_baseline_direction.py` covers only `_relative_revalidation_verdict`, not baseline indifference (`yuhl6o` E-02 evidence for S-16).
- Mutation-probe pattern (plugin rebinding a `runner_shared` attribute, untracked scratch) follows executed plan `df486j` E-03.
- Suite runs bare: `python3 -m pytest` (pyproject `addopts`).
- Review re-measurement (2026-10-15, HEAD `ba8709ea4`), scratch under gitignored `.aw/state/`, deleted after: four not-mine releases `[True, True, True, True]`; differing record keys `['suite_baseline']` for completed-vs-absent, corroborating-vs-contradicting, and absent-vs-None; mine `False False mine ['suite_baseline']`. Record keys: `answer, ask_reason, asked, awaits_human_decision, failing_tests, integrates, reason, recheck_attempts, recheck_budget, recheck_passed, recheck_summary, refuses, released, session_id, signal, suite_baseline, usable, violation`.
- History: `80db6750c` trimmed `tests/test_suite_baseline.py` (still holding `NothingRefusesOnTheBaseline`, whose three behavioral tests carry no `inspect`/`ast` call); `19313eed7` then deleted the file.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F1 | The deleted coverage lived in `NothingRefusesOnTheBaseline` with three behavioral tests (`test_a_not_mine_verdict_is_IDENTICAL_with_and_without_the_id_in_the_baseline`, `test_the_ONLY_field_that_differs_is_the_RECORDED_baseline_itself`, `test_a_MINE_verdict_is_also_identical_either_way`) plus two AST pins. | `git show 80db6750c^:tests/test_suite_baseline.py`, class `NothingRefusesOnTheBaseline`. |
| F2 | `yuhl6o` dispositioned S-16, S-20, S-21 RETIRE-UNGUARDED: "no live test asserts `perform_gate_answer` baseline indifference". | `.aw/records/plans/executed/20261011-iosmvn-01-yuhl6o-...ipd.md`, E-02 Disposition Table rows S-16/S-20/S-21. |
| F3 | The property still holds on current code: four not-mine releases all True; differing record keys `['suite_baseline']`; mine refuses either way. | Authoring prototype run under gitignored `.aw/state/` (deleted after): output `True True True True` / `['suite_baseline'] ['suite_baseline']` / `False False mine ['suite_baseline']`. |
| F4 | The current record now also carries `released` (added by `nzznlm`); it is included in the equivalence field list. | Prototype printed record keys including `released`. |
| F5 | (review) `runner_shared.perform_gate_answer`'s docstring says "`tests/test_suite_baseline.py` (deleted in `19313eed`; no live guard currently asserts this)". Once this plan lands that sentence is false. | `agent_workflows/runner_shared.py` `perform_gate_answer` docstring, paragraph "`baseline` IS PASSED STRAIGHT THROUGH". |

## Proposed changes (ordered, validatable)

1. New module `tests/test_gate_answer_baseline_indifference.py` with the fixtures and tests in E-01 and E-02.
2. Mutation probe (E-03), untracked, proving the tests fail under all three rejected behaviors.
3. Docstring correction in `runner_shared.perform_gate_answer` (E-04).
4. Full-suite regression and a single path-scoped commit (E-05).

## Deferred / out of scope (with reason)

- AST/`inspect` pins from the deleted class: prohibited by P16 and the backlog item.
  - Carrier-Declined: prohibited work, not outstanding work.
- `fixed` and `needs-human` answers: the backlog item names only baseline non-refusal and not-mine equivalence; `mine` is included because it is the symmetric half of the same deleted class.
  - Carrier-Declined: no lost coverage is known for them; the deleted class covered only `not-mine` and `mine`.
- S-17 (`TheTwoMeasurementsAreComparable`): a RETIRE-PIN site, not in this item.
  - Carrier-Declined: `yuhl6o` dispositioned it RETIRE-PIN (a source pin, not restorable under P16).

## Scope check

- Over-scope: none.
- Under-scope: none after review (F5 docstring added as E-04); all three cited sites (S-16, S-20, S-21) describe the same property, which E-01/E-02 cover.

## Required tests / validation

- The new module passes on current code (E-01, E-02).
- Each of the three mutants is killed by the module (E-03).
- Bare `python3 -m pytest` is green (E-05).

## Spec / documentation sync

No spec or user-facing documentation change: test-only plus one internal docstring correction (E-04); no CHANGELOG line, since no user-visible behavior changes.

## Open questions

### OQ-01: Should the restored module live in a recreated tests/test_suite_baseline.py?

- Blocking: no
- Status: resolved
- Owner: plan author (OpenCode Claude Opus)
- Resolution or deferral rationale: No. A new purpose-named file avoids implying the rest of the deleted module (largely source pins) was restored, matching how `df486j` restored coverage in `tests/test_manifest_entry_selectable.py`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted pytest output of `python3 -m pytest -o addopts="" -q tests/test_gate_answer_baseline_indifference.py -k not_mine` showing the not-mine equivalence test passed, plus the test source excerpt showing all four baselines and the field list; `rg -n "\bimport (inspect|ast)\b|\binspect\.|\bast\.|getsource|read_text\(" tests/test_gate_answer_baseline_indifference.py` returns no hits.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted pytest output showing the differing-keys test and the mine-symmetry test passed, and the excerpt asserting the differing key set equals `{"suite_baseline"}`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted pytest output for the unmutated module and for each of the three mutant plugins, each mutant showing a nonzero exit and at least one named failing test; `git status --porcelain` showing no scratch file tracked or left outside gitignored `.aw/state/`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `git diff agent_workflows/runner_shared.py` showing only the docstring sentence changed (no code line).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted final summary line of bare `python3 -m pytest` with zero failures, and `git show --stat <commit>` for the E-05 commit listing exactly `tests/test_gate_answer_baseline_indifference.py` and `agent_workflows/runner_shared.py`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires `/plan-review` and explicit human approval before execution.

Execution contract: all open questions are resolved. Commit only the files named in `- Scope-Paths:`, through `aw commit tosnwd -- <paths>`, never `git add -A` and never `git push`. Run the suite BARE and paste the actual runner output; never claim a test result that was not produced. Mark an `E-*` item `performed` only after performing it, and a `V-*` item `pass` only after inspecting the evidence in a separate pass. Do not claim done until `aw ipd lint --phase pre-transition` reports conforming and every `V-*` item carries concrete pasted evidence with `Result: pass`. Ownership of the transition is conditional: in a managed runner lane (`AW_EXECUTION_ROLE=worker`) the RUNNER owns `aw ipd begin`/`aw ipd finalize`, so the executor commits its work and leaves the move to the runner; executing BY HAND, run `aw ipd begin` before the first edit and `aw ipd finalize` for the terminal move. Never hand-edit the status or `git mv` the file. SCOPE FENCE: an edit outside `- Scope-Paths:` that proves necessary is made and then justified with `aw ipd finalize --scope-reason`, never silently. The E-03 mutation plugins live only under the gitignored `.aw/state/` and are deleted after the probe; they are never committed.
