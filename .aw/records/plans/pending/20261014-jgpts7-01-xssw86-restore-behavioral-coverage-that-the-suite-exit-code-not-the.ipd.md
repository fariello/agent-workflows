# IPD: Restore behavioral coverage that the suite exit code, not the failing-test list, decides integration

- Date: 2026-10-14
- Kind: child
- Concern: The property that the post-merge suite's EXIT CODE (not its parsed failing-test list) is the authority on integration, so a red suite with an EMPTY failing list never integrates (the `32ij2j` inversion), lost its only behavioral guard when `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` was deleted in `19313eed` (yuhl6o sites S-18, S-22, S-23, S-24, all RETIRE-UNGUARDED). Nothing now asserts it for `integration_is_earned`, `new_failures_since_baseline`, or `unattributed_merged_failures`.
- Scope: Add one new behavior-only test module, `tests/test_suite_exit_code_authority.py`, that calls the real `integration_is_earned` (both hosts), `gate_answer_is_warranted`, `SuiteCheckResult.failing_text`/`gate_answer_question`, `new_failures_since_baseline`, and `unattributed_merged_failures` and asserts their returned verdicts. Test-only; no production change.
- Scope-Paths: tests/test_suite_exit_code_authority.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: jgpts7
- Set: jgpts7
- Order: 1
- Highest E allocated: 04
- Author: OpenCode Claude Opus
- Id: xssw86

## Workflow history

- 2026-10-14 draft (OpenCode Claude Opus): created.
- 2026-10-14 to-review (OpenCode Claude Opus): authored from backlog `jgpts7`; Step 0 evidence gathered (including a throwaway probe of every restored property against current code); ready for `/plan-review`.

## Goal

Restore, as behavior-only tests, the property the deleted `TheExitCodeIsTheAuthorityAndNotTheList` guarded: a non-passing suite never earns integration or a `no-regression` judgement merely because its failing list is empty, a passing exit earns integration regardless of the list, and the agent is always asked (with non-empty evidence) rather than the red tree being silently integrated.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: integration_is_earned (S-18, S-22)

- [ ] E-01 Create `tests/test_suite_exit_code_authority.py` with a keyword-only `_suite_result(...)` helper building `runner_shared.SuiteCheckResult` (defaults `passing=False, exit_code=1, summary="1 failed, 1 passed in 0.01s", reason="the driver-run suite did not pass", cwd=".", timeout_seconds=600.0, elapsed_seconds=0.5, failures=()`), and a test class that, for each host module (`oc_runipd`, `agy_runipd`) via `subTest`, calls `module.integration_is_earned(validate=False, verify_disp=None, suite_result=...)` and asserts: (a) exit 1 with `failures=()` gives `earned is False`, `signal == runner_shared.INTEGRATION_REFUSED_SUITE_FAILED`, and `runner_shared.gate_answer_is_warranted(integration_gate_relevant=True, earned=..., integration_signal=..., session_id="s")[0] is True`; (b) the same with `summary=""` also refuses and is warranted; (c) exit codes 124 and 127 with empty list and summary refuse and are warranted; (d) the control: `passing=True, exit_code=0, summary="9 passed", failures=("FAILED stale::leftover",)` gives `earned is True`. Assertion messages state that the exit code, not the list, is the authority.
  - Depends on: none
  - Expected outcome: the S-18/S-22 inversion guard runs on both hosts, with a passing control proving the refusal is not vacuous.
  - Execution state: pending

- [ ] E-02 Add a test that `_suite_result(failures=(), summary="").failing_text` is non-empty after `.strip()`, and that its first line (first 30 chars) appears in `runner_shared.gate_answer_question(failing=text, changed_files=("a.py",))`, so the escalation question never shows an empty evidence section.
  - Depends on: E-01
  - Expected outcome: the deleted `test_the_question_never_shows_an_EMPTY_evidence_section` is restored behaviorally.
  - Execution state: pending

### Task group 2: the relative comparisons (S-23, S-24)

- [ ] E-03 Add tests for `runner_shared.new_failures_since_baseline` with a `SuiteBaseline(state="completed", base_commit="abc", failures=("FAILED tests/t.py::a - assert 1 == 2",))`: an EMPTY merged list with `suite_passed=False` returns `judgement == REVALIDATION_UNKNOWN` and `introduced_nothing is False`; the same with `suite_passed` omitted (default) is also `unknown`; and the control with `suite_passed=True` returns `REVALIDATION_NO_REGRESSION`.
  - Depends on: E-01
  - Expected outcome: S-23 guarded: an empty list on a red suite is never read as "nothing new".
  - Execution state: pending

- [ ] E-04 Add tests for `runner_shared.unattributed_merged_failures` with `attributed=(normalize_failure_id("FAILED tests/t.py::a - assert 1 == 2"),)`: an EMPTY merged list with `suite_passed=False` returns `unknown`; with `suite_passed` omitted returns `unknown`; controls: merged `("FAILED tests/t.py::a - x",)` returns `no-regression`, and merged `("FAILED tests/t.py::a - x", "FAILED tests/t.py::b - y")` returns `regressed`.
  - Depends on: E-01
  - Expected outcome: S-24 guarded: an empty merged list never vacuously satisfies "every failure was attributed away".
  - Execution state: pending

## Project conventions discovered (Step 0)

- P16 / AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE": the deleted file also contained `BothHostsShareEveryAdjudicationSymbol.test_the_adjudication_logic_lives_in_the_SHARED_module`, which imported `ast`; that is a source pin and is NOT restored. Host parity is exercised here by calling both hosts' `integration_is_earned` and asserting equal behavior, not by identity or AST.
- Recreating `tests/test_suite_adjudication.py` would revive a file the suite trim (`19313eed`) deliberately removed; the sibling plan `eg6r2t` (backlog `bzjclz`) set the same precedent by not reviving its deleted file. A new, narrowly named module is used instead.
- Existing live tests of `integration_is_earned` (`tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`, `tests/test_verifier_evidence.py`) cover validate-ON verifier paths only, never the empty-failing-list red-suite case.
- Suite runs bare: `python3 -m pytest`; narrowed runs use `python3 -m pytest -o addopts="" <file>` (repo-local development contract).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The guard was deleted in `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"). | `git show 19313eed7^:tests/test_suite_adjudication.py` contains `class TheExitCodeIsTheAuthorityAndNotTheList` with `test_a_RED_exit_with_an_EMPTY_failing_list_still_ESCALATES`, `..._EMPTY_summary_still_escalates`, `test_the_question_never_shows_an_EMPTY_evidence_section`, `test_a_PASSING_exit_earns_integration_regardless_of_the_list`, `test_a_TIMEOUT_and_an_UNRUNNABLE_suite_both_refuse_fail_closed`. |
| F-2 | yuhl6o recorded S-18, S-22, S-23, S-24 as RETIRE-UNGUARDED, Removed-by `19313eed`. | `.aw/records/plans/executed/20261011-iosmvn-01-yuhl6o-...ipd.md`, E-02 disposition rows S-18, S-22, S-23, S-24. |
| F-3 | Production comments still cite the dead guard and say no live guard asserts it. | `runner_shared.py` text "(deleted in `19313eed`; no live guard currently asserts this)" near `new_failures_since_baseline` and `unattributed_merged_failures` docstrings. |
| F-4 | No live test calls `new_failures_since_baseline` or `unattributed_merged_failures`. | `grep -rln "new_failures_since_baseline\|unattributed_merged_failures" tests` hits only `integration_is_earned` users, none of these two names. |
| F-5 | Every restored property holds today, so the tests pass against current code. | Throwaway Step 0 probe printed, for both `oc_runipd` and `agy_runipd`: exit 1/`1 failed` -> `False suite-failed True`; exit 1/`''` -> `False suite-failed True`; 124 and 127 -> `False suite-failed True`; exit 0 with stale list -> `True driver-run-suite False`. `failing_text` with empty list and summary -> `'the suite did not pass and produced no parseable summary (ex...'`, present in the question: `True`. `nfsb False unknown`, `nfsb True no-regression`, `nfsb default unknown`; `umf False unknown`, `umf True no-regression`, `umf default unknown`; `umf` single attributed -> `no-regression`, extra unattributed -> `regressed`. |

## Proposed changes (ordered, validatable)

1. E-01: dual-host `integration_is_earned` refusal and escalation for red-with-empty-list, plus the passing control.
2. E-02: non-empty evidence in the escalation question.
3. E-03: `new_failures_since_baseline` empty-red is `unknown`.
4. E-04: `unattributed_merged_failures` empty-red is `unknown`, with regressed/no-regression controls.

## Deferred / out of scope (with reason)

- Updating the `runner_shared.py` comments that say "no live guard currently asserts this": a production-file edit outside this test-only scope; a follow-up may repoint them to the new module.
- The deleted file's other classes (real-pytest capture, verdict actions, merged-tree location, host symbol identity): not part of the property this backlog item names.
- Pinning the exact `detail`/`reason` prose: text pins are prohibited by P16.

## Scope check

- Over-scope: none.
- Under-scope: none; S-18/S-22 are covered by E-01/E-02, S-23 by E-03, S-24 by E-04.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_suite_exit_code_authority.py -v` shows each new test passing.
- Mutation check (temporary, not committed): monkeypatch the empty-list guard by wrapping `runner_shared.new_failures_since_baseline` / `unattributed_merged_failures` so they are called with `suite_passed=True`, and patch `integration_is_earned`'s suite input to `passing=True` when `failures == ()`, confirming E-01, E-03, E-04 fail; revert.
- Full suite bare: `python3 -m pytest` passes with no new failures.

## Spec / documentation sync

N/A: test-only change restoring coverage; no spec or user-facing behavior changes.

## Open questions

### OQ-01: Which test file should host the restored coverage?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: a new module `tests/test_suite_exit_code_authority.py`; no live file owns these three predicates' red-suite behavior, and reviving `tests/test_suite_adjudication.py` would undo the deliberate `19313eed` trim (precedent: plan `eg6r2t`).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_suite_exit_code_authority.py -v` output showing the E-01 tests PASSED for both host subtests; plus pasted mutation-check output (a `SuiteCheckResult` with `failures=()` forced to `passing=True` before `integration_is_earned`) showing the red-with-empty-list test FAILED, then passing after revert.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output showing the evidence-section test PASSED, and the test source excerpt showing it calls the real `SuiteCheckResult.failing_text` and `runner_shared.gate_answer_question`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output showing the `new_failures_since_baseline` tests PASSED; plus pasted mutation-check output (wrapper forcing `suite_passed=True`) showing the empty-red `unknown` assertion FAILED, then passing after revert.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted pytest output showing the `unattributed_merged_failures` tests PASSED; plus pasted bare `python3 -m pytest` output with the `N passed` summary and no new failures; plus pasted `git diff` of the new file showing no `inspect`/`ast` import, no read of any `agent_workflows/*.py` source, and no assertion on docstring or reason prose (P16).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only `tests/test_suite_exit_code_authority.py` via `aw commit <this plan> -- tests/test_suite_exit_code_authority.py`; never push. Move the plan to `executed/` through the tooled lifecycle only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
