# IPD: Restore behavioral coverage of perform_gate_answer baseline non-refusal and not-mine outcome equivalence

- Date: 2026-10-14
- Kind: child
- Concern: The maintainer's binding ruling (2026-09-08, reaffirmed 2026-09-20) that no programmatic check may refuse a gate-answer verdict on the strength of a suite baseline has had zero behavioral test coverage since commit `19313eed` deleted `tests/test_suite_baseline.py` (class `NothingRefusesOnTheBaseline`); plan `yuhl6o` recorded sites S-16, S-20 and S-21 as RETIRE-UNGUARDED for exactly this property.
- Scope: Add one new behavioral test module that calls `runner_shared.perform_gate_answer` with a stub `ask` and asserts on the returned `GateAnswerOutcome` (`release` and `record`) across corroborating, contradicting, absent and unsupplied baselines, for `not-mine` and `mine` answers. No production code changes; no source-reading assertions.
- Scope-Paths: tests/test_gate_answer_baseline_indifference.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: xhrpeg
- Set: xhrpeg
- Order: 1
- Highest E allocated: 04
- Author: OpenCode Claude Opus
- Id: tosnwd

## Workflow history

- 2026-10-15 draft (OpenCode Claude Opus): created.
- 2026-10-15 to-review (OpenCode Claude Opus): authored review-ready plan graduating backlog xhrpeg.

## Goal

Restore regression coverage so that any change making `perform_gate_answer` refuse (or rescue) a verdict because of what the baseline contains, or letting the baseline alter any outcome field other than the `suite_baseline` audit record, turns the suite red. Only behavioral outcomes are restored; the deleted file's AST/`inspect` pins (for example `test_NO_CODE_PATH_compares_the_baseline_to_the_post_work_SET`) are deliberately NOT restored (P16).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: not-mine equivalence

- [ ] E-01 Create `tests/test_gate_answer_baseline_indifference.py` with fixtures: `_suite_result()` building `oc_runipd.SuiteCheckResult(passing=False, exit_code=1, ..., failures=("FAILED tests/test_pre_existing.py::T::test_already_red - assert 1 == 2",))`; `_completed(failures)` building `runner_shared.SuiteBaseline(state=runner_shared.SUITE_BASELINE_COMPLETED, ...)`; and `_perform(answer, baseline)` that, in a `tempfile.TemporaryDirectory`, passes an `ask` stub writing `{"schema_version": 1, "disposition": "executed", runner_shared.GATE_ANSWER_KEY: answer}` to the outcome path and returning `(0, "ses-1", path, ["stub"])`, then calls `runner_shared.perform_gate_answer(suite_result=..., changed_files=("agent_workflows/term.py",), ask=ask, outcome_path=path, session_id="ses-1", baseline=baseline)`. Add a test that, for `{"answer": "not-mine", ...}`, runs four baselines: corroborating (contains the failing id), contradicting (contains only a different id), `runner_shared.suite_baseline_absent("...")`, and `None`; asserts `release is True` for all four; and asserts (as `subTest`s per field) that `answer`, `reason`, `usable`, `integrates`, `refuses`, `released`, `awaits_human_decision`, `violation`, `recheck_attempts`, `recheck_passed` and `failing_tests` are equal across all four records.
  - Depends on: none
  - Expected outcome: The test passes against current code. At authoring a prototype of exactly this shape printed `True True True True` for the four releases.
  - Execution state: pending

- [ ] E-02 In the same module, add a test asserting that between a `not-mine` outcome with a completed baseline and one with an absent baseline, the set of differing `record` keys is exactly `{"suite_baseline"}` (a record is not a check); and a symmetric test that a `mine` answer has `release is False` both with a completed baseline and with `None`, with the differing key set again exactly `{"suite_baseline"}` (the baseline must not rescue a refusal either).
  - Depends on: E-01
  - Expected outcome: Both tests pass against current code. At authoring the prototype printed `['suite_baseline'] ['suite_baseline']` for not-mine (vs absent, vs contradicting) and `False False mine ['suite_baseline']` for mine.
  - Execution state: pending

### Task group 2: Prove the coverage is load-bearing

- [ ] E-03 Run an in-memory mutation probe with no source edit: write two pytest plugins in an UNTRACKED scratch directory under the gitignored `.aw/state/` (never committed), each rebinding `runner_shared.perform_gate_answer` at import with a wrapper around the original. Mutant A: when the answer is `not-mine` and `baseline` is completed and does not contain every failing id, return a copy of the outcome with `release=False` and `record["refuses"]=True` (the rejected constraint). Mutant B: when `baseline` is completed and the answer is `mine`, return `release=True` (baseline rescue). Run the new module once per plugin with `PYTHONPATH=.aw/state/<scratch>:. python3 -m pytest -o addopts="" -q -n0 -p <plugin> tests/test_gate_answer_baseline_indifference.py` and confirm each mutant makes at least one test fail, then delete the scratch directory. The test module must call `runner_shared.perform_gate_answer` through the module attribute (not a `from ... import` binding) so the rebinding reaches it.
  - Depends on: E-02
  - Expected outcome: Both mutants are killed (nonzero pytest exit with named failing tests); the unmutated module passes.
  - Execution state: pending

### Task group 3: Regression

- [ ] E-04 Run the full fast suite bare (`python3 -m pytest`) and confirm no regressions; commit only the new module via `aw commit <plan> -- tests/test_gate_answer_baseline_indifference.py`.
  - Depends on: E-03
  - Expected outcome: Suite green with the new tests included; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Tests must exercise behavior, not code structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16): no `inspect`/`ast`/regex reads of production source. The deleted class's `test_NO_CODE_PATH_compares_the_baseline_to_the_post_work_SET` and `test_the_baseline_reaches_NO_comparison_in_execute_item_core_either` used `inspect.getsource`/`ast.parse` and are NOT restored.
- `runner_shared.perform_gate_answer` signature (keyword-only): `suite_result`, `changed_files`, `ask`, `outcome_path`, ..., `session_id`, `baseline: SuiteBaseline | None`. Its docstring states `not-mine` releases in any run and `mine` refuses with no override.
- `runner_shared.SuiteBaseline` (NamedTuple) and `runner_shared.suite_baseline_absent(reason, *, base_commit="")` construct baselines; `runner_shared.SUITE_BASELINE_COMPLETED` is the completed state.
- Sibling behavioral test `tests/test_gate_answer_record_released.py` drives `perform_gate_answer` with stub `ask`; `tests/test_suite_baseline_direction.py` covers only `_relative_revalidation_verdict`, not baseline indifference (`yuhl6o` E-02 evidence for S-16).
- Mutation-probe pattern (plugin rebinding a `runner_shared` attribute, untracked scratch) follows executed plan `df486j` E-03.
- Suite runs bare: `python3 -m pytest` (pyproject `addopts`).

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F1 | The deleted coverage lived in `NothingRefusesOnTheBaseline` with three behavioral tests (`test_a_not_mine_verdict_is_IDENTICAL_with_and_without_the_id_in_the_baseline`, `test_the_ONLY_field_that_differs_is_the_RECORDED_baseline_itself`, `test_a_MINE_verdict_is_also_identical_either_way`) plus two AST pins. | `git show 80db6750c^:tests/test_suite_baseline.py`, class `NothingRefusesOnTheBaseline`. |
| F2 | `yuhl6o` dispositioned S-16, S-20, S-21 RETIRE-UNGUARDED: "no live test asserts `perform_gate_answer` baseline indifference". | `.aw/records/plans/executed/20261011-iosmvn-01-yuhl6o-...ipd.md`, E-02 Disposition Table rows S-16/S-20/S-21. |
| F3 | The property still holds on current code: four not-mine releases all True; differing record keys `['suite_baseline']`; mine refuses either way. | Authoring prototype run under gitignored `.aw/state/` (deleted after): output `True True True True` / `['suite_baseline'] ['suite_baseline']` / `False False mine ['suite_baseline']`. |
| F4 | The current record now also carries `released` (added by `nzznlm`); it is included in the equivalence field list. | Prototype printed record keys including `released`. |

## Proposed changes (ordered, validatable)

1. New module `tests/test_gate_answer_baseline_indifference.py` with the fixtures and tests in E-01 and E-02.
2. Mutation probe (E-03), untracked, proving the tests fail under both rejected behaviors.
3. Full-suite regression and a single path-scoped commit (E-04).

## Deferred / out of scope (with reason)

- AST/`inspect` pins from the deleted class: prohibited by P16 and the backlog item.
- `fixed` and `needs-human` answers: the backlog item names only baseline non-refusal and not-mine equivalence; `mine` is included because it is the symmetric half of the same deleted class.
- S-17 (`TheTwoMeasurementsAreComparable`): a RETIRE-PIN site, not in this item.

## Scope check

- Over-scope: none.
- Under-scope: none; all three cited sites (S-16, S-20, S-21) describe the same property, which E-01/E-02 cover.

## Required tests / validation

- The new module passes on current code (E-01, E-02).
- Each of the two mutants is killed by the module (E-03).
- Bare `python3 -m pytest` is green (E-04).

## Spec / documentation sync

N/A: test-only change; no spec or user-facing documentation describes these test files.

## Open questions

### OQ-01: Should the restored module live in a recreated tests/test_suite_baseline.py?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. A new purpose-named file avoids implying the rest of the deleted module (largely source pins) was restored, matching how `df486j` restored coverage in `tests/test_manifest_entry_selectable.py`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted pytest output of `python3 -m pytest -o addopts="" -q tests/test_gate_answer_baseline_indifference.py -k not_mine` showing the not-mine equivalence test passed, plus the test source excerpt showing all four baselines and the field list; `rg -n "inspect|ast\\." tests/test_gate_answer_baseline_indifference.py` returns no hits.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted pytest output showing the differing-keys test and the mine-symmetry test passed, and the excerpt asserting the differing key set equals `{"suite_baseline"}`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted pytest output for each mutant plugin showing a nonzero exit and at least one named failing test; `git status --porcelain` showing no scratch file tracked or left outside gitignored `.aw/state/`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted final summary line of bare `python3 -m pytest` with zero failures, and `git show --stat HEAD` listing only `tests/test_gate_answer_baseline_indifference.py`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval. Follow the agent execution contract: commit only the declared Scope-Paths via `aw commit`, never push, paste actual runner output. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` is `pass` with observed evidence.
