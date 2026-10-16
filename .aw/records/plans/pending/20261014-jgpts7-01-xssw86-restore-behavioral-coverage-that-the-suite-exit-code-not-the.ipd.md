# IPD: Restore behavioral coverage that the suite exit code, not the failing-test list, decides integration

- Date: 2026-10-14
- Kind: child
- Concern: The property that the post-merge suite's EXIT CODE (not its parsed failing-test list) is the authority on integration, so a red suite with an EMPTY failing list never integrates (the `32ij2j` inversion), lost its only behavioral guard when `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` was deleted in `19313eed` (yuhl6o sites S-18, S-22, S-23, S-24, all RETIRE-UNGUARDED). Nothing now asserts it for `integration_is_earned`, `new_failures_since_baseline`, or `unattributed_merged_failures`.
- Scope: Add one new behavior-only test module, `tests/test_suite_exit_code_authority.py`, that calls the real `integration_is_earned` (both hosts), `gate_answer_is_warranted`, `SuiteCheckResult.failing_text`/`gate_answer_question`, `new_failures_since_baseline`, and `unattributed_merged_failures` and asserts their returned verdicts; then repoint the four `runner_shared.py` comments that cite the deleted guard as "no live guard currently asserts this" to the new module (comment and docstring text only; no behavior change).
- Scope-Paths: tests/test_suite_exit_code_authority.py, agent_workflows/runner_shared.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: jgpts7
- Set: jgpts7
- Order: 1
- Highest E allocated: 05
- Author: OpenCode Claude Opus
- Id: xssw86
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed

- 2026-10-14 draft (OpenCode Claude Opus): created.
- 2026-10-14 to-review (OpenCode Claude Opus): authored from backlog `jgpts7`; Step 0 evidence gathered (including a throwaway probe of every restored property against current code); ready for `/plan-review`.

## Goal

Restore, as behavior-only tests, the property the deleted `TheExitCodeIsTheAuthorityAndNotTheList` guarded: a non-passing suite never earns integration or a `no-regression` judgement merely because its failing list is empty, a passing exit earns integration regardless of the list, and the agent is always asked (with non-empty evidence) rather than the red tree being silently integrated.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: integration_is_earned (S-18, S-22)

- [x] E-01 Create `tests/test_suite_exit_code_authority.py` with a keyword-only `_suite_result(...)` helper building `runner_shared.SuiteCheckResult` (defaults `passing=False, exit_code=1, summary="1 failed, 1 passed in 0.01s", reason="the driver-run suite did not pass", cwd=".", timeout_seconds=600.0, elapsed_seconds=0.5, failures=()`), and a test class that, for each host module (`oc_runipd`, `agy_runipd`) via `subTest`, calls `module.integration_is_earned(validate=False, verify_disp=None, suite_result=...)` and asserts (both host attributes currently resolve to the one `runner_shared.integration_is_earned` re-exported by `oc_runipd` and `agy_runipd`, so the per-host loop guards against a host re-binding or shadowing the name, not two implementations; do NOT assert identity, which would be a structure pin): (a) exit 1 with `failures=()` gives `earned is False`, `signal == runner_shared.INTEGRATION_REFUSED_SUITE_FAILED`, and `runner_shared.gate_answer_is_warranted(integration_gate_relevant=True, earned=..., integration_signal=..., session_id="s")[0] is True`; (b) the same with `summary=""` also refuses and is warranted; (c) exit codes 124 and 127 with empty list and summary refuse and are warranted; (d) the control: `passing=True, exit_code=0, summary="9 passed", failures=("FAILED stale::leftover",)` gives `earned is True` and `gate_answer_is_warranted(...)[0] is False` (a green suite is never taxed with a question). Assertion messages state that the exit code, not the list, is the authority.
  - Depends on: none
  - Expected outcome: the S-18/S-22 inversion guard runs on both hosts, with a passing control proving the refusal is not vacuous.
  - Execution state: performed

- [x] E-02 Add a test that `_suite_result(failures=(), summary="").failing_text` is non-empty after `.strip()`, and that its first line (first 30 chars) appears in `runner_shared.gate_answer_question(failing=text, changed_files=("a.py",))`, so the escalation question never shows an empty evidence section.
  - Depends on: E-01
  - Expected outcome: the deleted `test_the_question_never_shows_an_EMPTY_evidence_section` is restored behaviorally.
  - Execution state: performed

### Task group 2: the relative comparisons (S-23, S-24)

- [x] E-03 Add tests for `runner_shared.new_failures_since_baseline` with a `SuiteBaseline(state="completed", base_commit="abc", failures=("FAILED tests/t.py::a - assert 1 == 2",))`: an EMPTY merged list with `suite_passed=False` returns `judgement == REVALIDATION_UNKNOWN` and `introduced_nothing is False`; the same with `suite_passed` omitted (default) is also `unknown`; and the control with `suite_passed=True` returns `REVALIDATION_NO_REGRESSION`.
  - Depends on: E-01
  - Expected outcome: S-23 guarded: an empty list on a red suite is never read as "nothing new".
  - Execution state: performed

- [x] E-04 Add tests for `runner_shared.unattributed_merged_failures` with `attributed=(normalize_failure_id("FAILED tests/t.py::a - assert 1 == 2"),)`: an EMPTY merged list with `suite_passed=False` returns `unknown`; with `suite_passed` omitted returns `unknown`; controls: merged `("FAILED tests/t.py::a - x",)` returns `no-regression`, and merged `("FAILED tests/t.py::a - x", "FAILED tests/t.py::b - y")` returns `regressed`.
  - Depends on: E-01
  - Expected outcome: S-24 guarded: an empty merged list never vacuously satisfies "every failure was attributed away".
  - Execution state: performed

### Task group 3: honest documentation (F-3)

- [x] E-05 In `agent_workflows/runner_shared.py`, edit ONLY comment/docstring text at the four sites citing `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` ("deleted in `19313eed`; no live guard currently asserts this"): the `(a) AN EMPTY MERGED FAILING LIST ON A NON-PASSING SUITE` comment block (line 28128), the `THE COMPARISON IN HERE IS THE ONE THAT ALREADY INVERTED` comment block (line 28594), the `new_failures_since_baseline` docstring (line 28726), and the `unattributed_merged_failures` docstring (line 28919). Keep the historical note that the original guard was deleted in `19313eed`, and replace "no live guard currently asserts this" with a pointer to `tests/test_suite_exit_code_authority.py`. Do NOT touch the other "no live guard" comments in the file, which concern different properties.
  - Depends on: E-01, E-03, E-04
  - Expected outcome: no `runner_shared.py` comment says this property is unguarded once the guard exists; there is no code change.
  - Execution state: performed

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
| F-3 | Production comments still cite the dead guard and say no live guard asserts it. Once this plan lands they become false, so E-05 repoints them. | `agent_workflows/runner_shared.py` lines 28128, 28594, 28726, and 28919 each cite `TheExitCodeIsTheAuthorityAndNotTheList` with "no live guard currently asserts this". |
| F-4 | No live test calls `new_failures_since_baseline` or `unattributed_merged_failures`. | `grep -rln "new_failures_since_baseline\|unattributed_merged_failures" tests` hits only `integration_is_earned` users, none of these two names. |
| F-5 | Every restored property holds today, so the tests pass against current code. | Throwaway Step 0 probe printed, for both `oc_runipd` and `agy_runipd`: exit 1/`1 failed` -> `False suite-failed True`; exit 1/`''` -> `False suite-failed True`; 124 and 127 -> `False suite-failed True`; exit 0 with stale list -> `True driver-run-suite False`. `failing_text` with empty list and summary -> `'the suite did not pass and produced no parseable summary (ex...'`, present in the question: `True`. `nfsb False unknown`, `nfsb True no-regression`, `nfsb default unknown`; `umf False unknown`, `umf True no-regression`, `umf default unknown`; `umf` single attributed -> `no-regression`, extra unattributed -> `regressed`. |

## Proposed changes (ordered, validatable)

1. E-01: dual-host `integration_is_earned` refusal and escalation for red-with-empty-list, plus the passing control.
2. E-02: non-empty evidence in the escalation question.
3. E-03: `new_failures_since_baseline` empty-red is `unknown`.
4. E-04: `unattributed_merged_failures` empty-red is `unknown`, with regressed/no-regression controls.
5. E-05: repoint the four stale `runner_shared.py` comments (text only).

## Deferred / out of scope (with reason)

- The deleted file's other classes (real-pytest capture, verdict actions, merged-tree location, host symbol identity): not part of the property this backlog item names.
  - Carrier-Declined: outside backlog `jgpts7`'s named property (S-18, S-22, S-23, S-24); host symbol identity is a P16 source pin and is never restored.
- Pinning the exact `detail`/`reason` prose: text pins are prohibited by P16.
  - Carrier-Declined: permanent non-goal under P16; nothing to carry.

## Scope check

- Over-scope: none.
- Under-scope: none; S-18/S-22 are covered by E-01/E-02, S-23 by E-03, S-24 by E-04, and the F-3 doc honesty by E-05.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_suite_exit_code_authority.py -v` shows each new test passing.
- Mutation check (temporary, never committed, no production edit): a throwaway pytest plugin under the gitignored `.aw/state/` loaded with `python3 -m pytest -o addopts="" -p <plugin> tests/test_suite_exit_code_authority.py`. Mutant A rebinds `integration_is_earned` on `runner_shared`, `oc_runipd`, and `agy_runipd` to a wrapper forcing `passing=True` when `failures == ()`; mutant B rebinds `runner_shared.new_failures_since_baseline` and `runner_shared.unattributed_merged_failures` to wrappers forcing `suite_passed=True`. MEASURED at review with a prototype of exactly these tests: unmutated `6 passed`; mutant A `1 failed, 5 passed` (the red-empty-list test); mutant B `2 failed, 4 passed` (the E-03 and E-04 empty-red tests). Delete the plugin afterwards.
- Full suite bare: `python3 -m pytest` passes with no new failures, run LAST, after E-05.

## Spec / documentation sync

N/A for specs and CHANGELOG: this restores test coverage and corrects internal comments (E-05); there is no spec or user-facing behavior change.

## Open questions

### OQ-01: Which test file should host the restored coverage?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: a new module `tests/test_suite_exit_code_authority.py`; no live file owns these three predicates' red-suite behavior, and reviving `tests/test_suite_adjudication.py` would undo the deliberate `19313eed` trim (precedent: plan `eg6r2t`).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_suite_exit_code_authority.py -v` output showing the E-01 tests PASSED, plus the test source excerpt showing the `for ... in (("oc", oc_runipd), ("agy", agy_runipd))` / `subTest(host=...)` loop (this repository has no `pytest-subtests` plugin, so `-v` prints one line per test method, never per subtest); plus pasted mutant-A output (see Required tests) showing the red-with-empty-list test FAILED, then the unmutated run passing.
  - Observed evidence:
    Pasted `python3 -m pytest -o addopts="" tests/test_suite_exit_code_authority.py -v` output:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=70513952
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 6 items

    tests/test_suite_exit_code_authority.py::SuiteExitCodeAuthorityTests::test_unattributed_merged_failures_empty_red_and_controls PASSED [ 16%]
    tests/test_suite_exit_code_authority.py::SuiteExitCodeAuthorityTests::test_new_failures_since_baseline_passing_control PASSED [ 33%]
    tests/test_suite_exit_code_authority.py::SuiteExitCodeAuthorityTests::test_passing_exit_earns_integration_regardless_of_the_list PASSED [ 50%]
    tests/test_suite_exit_code_authority.py::SuiteExitCodeAuthorityTests::test_the_question_never_shows_an_empty_evidence_section PASSED [ 66%]
    tests/test_suite_exit_code_authority.py::SuiteExitCodeAuthorityTests::test_red_exit_with_empty_failing_list_still_escalates PASSED [ 83%]
    tests/test_suite_exit_code_authority.py::SuiteExitCodeAuthorityTests::test_new_failures_since_baseline_empty_red_is_unknown PASSED [100%]

    ============================== 6 passed in 0.35s ===============================
    ```
    Test source excerpt showing the `for ... in (("oc", oc_runipd), ("agy", agy_runipd))` / `subTest(host=...)` loop:
    ```python
        for host_name, host_module in (("oc", oc_runipd), ("agy", agy_runipd)):
            with self.subTest(host=host_name, case="exit 1 empty failures"):
                res = _suite_result(passing=False, exit_code=1, failures=())
                verdict = host_module.integration_is_earned(
                    validate=False,
                    verify_disp=None,
                    suite_result=res,
                )
                self.assertFalse(
                    verdict.earned,
                    "The exit code, not the list, is the authority: exit 1 with empty failures must refuse integration",
                )
                self.assertEqual(
                    verdict.signal,
                    runner_shared.INTEGRATION_REFUSED_SUITE_FAILED,
                    "The exit code, not the list, is the authority: refusal signal must be suite-failed",
                )
                warranted, _ = runner_shared.gate_answer_is_warranted(
                    integration_gate_relevant=True,
                    earned=verdict.earned,
                    integration_signal=verdict.signal,
                    session_id="s",
                )
                self.assertTrue(
                    warranted,
                    "The exit code, not the list, is the authority: unparseable red suite must escalate to agent",
                )
    ```
    Mutant A output showing red-with-empty-list test FAILED:
    ```
    $ PYTHONPATH=.aw/state/scratch_mutants_xssw86:. python3 -m pytest -o addopts="" -v -p mutant_a tests/test_suite_exit_code_authority.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=3719526008
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 6 items

    tests/test_suite_exit_code_authority.py::SuiteExitCodeAuthorityTests::test_new_failures_since_baseline_passing_control PASSED [ 16%]
    tests/test_suite_exit_code_authority.py::SuiteExitCodeAuthorityTests::test_the_question_never_shows_an_empty_evidence_section PASSED [ 33%]
    tests/test_suite_exit_code_authority.py::SuiteExitCodeAuthorityTests::test_passing_exit_earns_integration_regardless_of_the_list PASSED [ 50%]
    tests/test_suite_exit_code_authority.py::SuiteExitCodeAuthorityTests::test_unattributed_merged_failures_empty_red_and_controls PASSED [ 66%]
    tests/test_suite_exit_code_authority.py::SuiteExitCodeAuthorityTests::test_red_exit_with_empty_failing_list_still_escalates FAILED [ 83%]
    tests/test_suite_exit_code_authority.py::SuiteExitCodeAuthorityTests::test_new_failures_since_baseline_empty_red_is_unknown PASSED [100%]

    =================================== FAILURES ===================================
    _ SuiteExitCodeAuthorityTests.test_red_exit_with_empty_failing_list_still_escalates _

    self = <tests.test_suite_exit_code_authority.SuiteExitCodeAuthorityTests testMethod=test_red_exit_with_empty_failing_list_still_escalates>

        def test_red_exit_with_empty_failing_list_still_escalates(self) -> None:
            """The exit code, not the list, is the authority: a red suite with an empty list refuses and escalates."""
            for host_name, host_module in (("oc", oc_runipd), ("agy", agy_runipd)):
                with self.subTest(host=host_name, case="exit 1 empty failures"):
                    res = _suite_result(passing=False, exit_code=1, failures=())
                    verdict = host_module.integration_is_earned(
                        validate=False,
                        verify_disp=None,
                        suite_result=res,
                    )
    >               self.assertFalse(
                        verdict.earned,
                        "The exit code, not the list, is the authority: exit 1 with empty failures must refuse integration",
                    )
    E               AssertionError: True is not false : The exit code, not the list, is the authority: exit 1 with empty failures must refuse integration

    tests/test_suite_exit_code_authority.py:61: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_suite_exit_code_authority.py::SuiteExitCodeAuthorityTests::test_red_exit_with_empty_failing_list_still_escalates
    ========================= 1 failed, 5 passed in 0.23s ==========================
    ```
    Unmutated run passing:
    ```
    $ python3 -m pytest -o addopts="" tests/test_suite_exit_code_authority.py -v
    ============================== 6 passed in 0.35s ===============================
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted pytest output showing the evidence-section test PASSED, and the test source excerpt showing it calls the real `SuiteCheckResult.failing_text` and `runner_shared.gate_answer_question`.
  - Observed evidence:
    Pasted pytest output:
    ```
    $ python3 -m pytest -o addopts="" tests/test_suite_exit_code_authority.py -k "test_the_question_never_shows_an_empty_evidence_section" -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 6 items / 5 deselected / 1 selected

    tests/test_suite_exit_code_authority.py::SuiteExitCodeAuthorityTests::test_the_question_never_shows_an_empty_evidence_section PASSED [100%]

    ======================= 1 passed, 5 deselected in 0.22s ========================
    ```
    Test source excerpt:
    ```python
        def test_the_question_never_shows_an_empty_evidence_section(self) -> None:
            """An empty section reads as 'no failures'; question must show non-empty evidence."""
            text = _suite_result(failures=(), summary="").failing_text
            self.assertTrue(text.strip())
            prompt = runner_shared.gate_answer_question(failing=text, changed_files=("a.py",))
            self.assertIn(text.splitlines()[0][:30], prompt)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted pytest output showing the `new_failures_since_baseline` tests PASSED; plus pasted mutant-B output (see Required tests) showing the empty-red `unknown` assertion FAILED, then the unmutated run passing.
  - Observed evidence:
    Pasted pytest output:
    ```
    $ python3 -m pytest -o addopts="" tests/test_suite_exit_code_authority.py -k "test_new_failures_since_baseline" -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 6 items / 4 deselected / 2 selected

    tests/test_suite_exit_code_authority.py::SuiteExitCodeAuthorityTests::test_new_failures_since_baseline_empty_red_is_unknown PASSED [ 50%]
    tests/test_suite_exit_code_authority.py::SuiteExitCodeAuthorityTests::test_new_failures_since_baseline_passing_control PASSED [100%]

    ======================= 2 passed, 4 deselected in 0.23s ========================
    ```
    Mutant B output showing empty-red unknown assertion FAILED:
    ```
    $ PYTHONPATH=.aw/state/scratch_mutants_xssw86:. python3 -m pytest -o addopts="" -v -p mutant_b tests/test_suite_exit_code_authority.py
    =================================== FAILURES ===================================
    _ SuiteExitCodeAuthorityTests.test_new_failures_since_baseline_empty_red_is_unknown _

    self = <tests.test_suite_exit_code_authority.SuiteExitCodeAuthorityTests testMethod=test_new_failures_since_baseline_empty_red_is_unknown>

        def test_new_failures_since_baseline_empty_red_is_unknown(self) -> None:
            """An empty merged list on a non-passing suite is unknown, never no-regression."""
            baseline = runner_shared.SuiteBaseline(
                state="completed",
                base_commit="abc",
                failures=("FAILED tests/t.py::a - assert 1 == 2",),
            )
            res_explicit = runner_shared.new_failures_since_baseline(
                merged_failures=(),
                baseline=baseline,
                suite_passed=False,
            )
    >       self.assertEqual(res_explicit.judgement, runner_shared.REVALIDATION_UNKNOWN)
    E       AssertionError: 'no-regression' != 'unknown'
    E       - no-regression
    E       + unknown

    tests/test_suite_exit_code_authority.py:185: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_suite_exit_code_authority.py::SuiteExitCodeAuthorityTests::test_new_failures_since_baseline_empty_red_is_unknown
    ========================= 2 failed, 4 passed in 0.25s ==========================
    ```
    Unmutated run passing:
    ```
    $ python3 -m pytest -o addopts="" tests/test_suite_exit_code_authority.py -v
    ============================== 6 passed in 0.35s ===============================
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted pytest output showing the `unattributed_merged_failures` tests PASSED; plus pasted bare `python3 -m pytest` output with the `N passed` summary and no new failures; plus pasted mutant-B output showing the E-04 empty-red test FAILED; plus pasted `git diff` of the new file showing no `inspect`/`ast` import, no read of any `agent_workflows/*.py` source, and no assertion on docstring or reason prose (P16).
  - Observed evidence:
    Pasted pytest output:
    ```
    $ python3 -m pytest -o addopts="" tests/test_suite_exit_code_authority.py -k "test_unattributed_merged_failures" -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 6 items / 5 deselected / 1 selected

    tests/test_suite_exit_code_authority.py::SuiteExitCodeAuthorityTests::test_unattributed_merged_failures_empty_red_and_controls PASSED [100%]

    ======================= 1 passed, 5 deselected in 0.22s ========================
    ```
    Bare `python3 -m pytest` output showing 707 passed with zero failures:
    ```
    $ python3 -m pytest
    bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...
    ........................................................................ [ 10%]
    ......................................................................... [ 20%]
    ........................................................................ [ 30%]
    ........................................................................ [ 40%]
    ........................................................................ [ 51%]
    ........................................................................ [ 61%]
    ........................................................................ [ 71%]
    ........................................................................ [ 81%]
    ........................................................................ [ 91%]
    ..........................................................               [100%]
    NOTE: 5 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    707 passed in 23.09s
    ```
    Mutant B output showing E-04 empty-red test FAILED:
    ```
    $ PYTHONPATH=.aw/state/scratch_mutants_xssw86:. python3 -m pytest -o addopts="" -v -p mutant_b tests/test_suite_exit_code_authority.py
    =================================== FAILURES ===================================
    _ SuiteExitCodeAuthorityTests.test_unattributed_merged_failures_empty_red_and_controls _

    self = <tests.test_suite_exit_code_authority.SuiteExitCodeAuthorityTests testMethod=test_unattributed_merged_failures_empty_red_and_controls>

        def test_unattributed_merged_failures_empty_red_and_controls(self) -> None:
            """An empty merged list on a non-passing suite is unknown; controls verify non-empty behavior."""
            attributed = (
                runner_shared.normalize_failure_id("FAILED tests/t.py::a - assert 1 == 2"),
            )
            res_explicit = runner_shared.unattributed_merged_failures(
                merged_failures=(),
                attributed=attributed,
                suite_passed=False,
            )
    >       self.assertEqual(res_explicit.judgement, runner_shared.REVALIDATION_UNKNOWN)
    E       AssertionError: 'no-regression' != 'unknown'
    E       - no-regression
    E       + unknown

    tests/test_suite_exit_code_authority.py:220: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_suite_exit_code_authority.py::SuiteExitCodeAuthorityTests::test_unattributed_merged_failures_empty_red_and_controls
    ========================= 2 failed, 4 passed in 0.25s ==========================
    ```
    P16 compliance check showing no inspect/ast/source-reading or code pins:
    ```
    $ python3 -c "
    import re
    text = open('tests/test_suite_exit_code_authority.py').read()
    assert not re.search(r'\b(inspect|ast)\b', text), 'found inspect/ast'
    assert 'read_text' not in text, 'found read_text'
    assert 'getsource' not in text, 'found getsource'
    print('P16 check passed clean')
    "
    P16 check passed clean
    ```
    `git show e61af7cfb36d98cb957fd3ef44423e185e2efa20 -- tests/test_suite_exit_code_authority.py` excerpt:
    ```diff
    +++ b/tests/test_suite_exit_code_authority.py
    @@ -0,0 +1,252 @@
    +#!/usr/bin/env python3
    +"""Behavioral tests for the suite exit code authority (IPD xssw86, backlog jgpts7).
    +
    +Restores behavioral coverage that the post-merge suite's exit code, not its parsed
    +failing-test list, is the authority on integration:
    +- A non-passing suite never earns integration merely because its failing list is empty (the 32ij2j inversion).
    +- A passing exit earns integration regardless of the list.
    +- A non-passing suite always escalates to the agent with non-empty evidence rather than silently integrating.
    +- Empty lists on non-passing suites in relative comparisons (new_failures_since_baseline,
    +  unattributed_merged_failures) yield unknown judgements rather than vacuous passes.
    +
    +Behavior-only tests: observable behavior and outcomes only (P16).
    +"""
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted `git diff -- agent_workflows/runner_shared.py` showing only comment/docstring lines changed at the four `TheExitCodeIsTheAuthorityAndNotTheList` sites, each now naming `tests/test_suite_exit_code_authority.py`; plus pasted `grep -n "TheExitCodeIsTheAuthorityAndNotTheList" agent_workflows/runner_shared.py` output showing no remaining hit beside "no live guard currently asserts this"; plus the bare `python3 -m pytest` output for V-04, which MUST be taken after this edit (run the full suite last).
  - Observed evidence:
    Pasted `git show e61af7cfb36d98cb957fd3ef44423e185e2efa20 -- agent_workflows/runner_shared.py`:
    ```diff
    diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
    index 42db940da..078919253 100644
    --- a/agent_workflows/runner_shared.py
    +++ b/agent_workflows/runner_shared.py
    @@ -28149,7 +28149,7 @@ evidence block. Claim `{GATE_ANSWER_NOT_MINE}` only if you believe it.
     #
     #   (a) AN EMPTY MERGED FAILING LIST ON A NON-PASSING SUITE IS NOT "NOTHING NEW". This is the `32ij2j`
     #       inversion, guarded by `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList`
    -#       (deleted in `19313eed`; no live guard currently asserts this), whose own docstring records
    +#       (deleted in `19313eed`; guarded live by `tests/test_suite_exit_code_authority.py`), whose own docstring records
     #       that plan comparing failing sets as a subset over an ALWAYS-EMPTY
     #       string so that "every lane passed including one that broke everything" (the always-empty read
     #       was SHIPPED in `run_suite_check` until `h5pyqa`). Measured while authoring this: with a merged
    @@ -28615,7 +28615,7 @@ REVALIDATION_CACHE_KEY: str = "post_merge_revalidation"
     # it is written to REFUSE TO BE THE AUTHORITY. Plan `32ij2j` compared failing SETS as a subset and
     # derived them from an always-empty string, so every lane passed INCLUDING one that broke everything;
     # `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` (deleted in `19313eed`;
    -# no live guard currently asserts this) existed for that case and called it the most important in its
    +# guarded live by `tests/test_suite_exit_code_authority.py`) existed for that case and called it the most important in its
     # file. Three rules below close the ways the subtraction can lie,
     # and each is a MEASURED hazard rather than a hypothetical one. A list may make a refusal SPECIFIC;
     # it may NEVER manufacture a pass.
    @@ -28747,7 +28747,7 @@ def new_failures_since_baseline(
         evaluated, because "empty because green" and "empty because nothing parsed" look identical from
         the list alone - and the EXIT CODE, not the list, is this repository's authority on which one it
         is (`tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` was deleted in
    -    `19313eed`; no live guard currently asserts this). It DEFAULTS False, the conservative reading, so
    +    `19313eed`; guarded live by `tests/test_suite_exit_code_authority.py`). It DEFAULTS False, the conservative reading, so
         a caller that forgets it gets `unknown` rather than a pass.
         """

    @@ -28940,7 +28940,7 @@ def unattributed_merged_failures(

           1. AN EMPTY MERGED FAILING LIST ON A NON-PASSING SUITE IS UNKNOWN. This is the `32ij2j` inversion
              (`tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList`, deleted in
    -         `19313eed`; no live guard currently asserts this): with a merged
    +         `19313eed`; guarded live by `tests/test_suite_exit_code_authority.py`): with a merged
              list of `()` the predicate "every failing id was attributed away" is VACUOUSLY TRUE, so a tree
              that broke everything integrates. The EXIT CODE, never the list, is this repository's authority
              on whether an empty list means "green" or "nothing parsed", which is why ``suite_passed`` is
    ```
    Grep output showing no remaining hit beside "no live guard currently asserts this":
    ```
    $ grep -n -C 1 "TheExitCodeIsTheAuthorityAndNotTheList" agent_workflows/runner_shared.py
    28150-#   (a) AN EMPTY MERGED FAILING LIST ON A NON-PASSING SUITE IS NOT "NOTHING NEW". This is the `32ij2j`
    28151:#       inversion, guarded by `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList`
    28152-#       (deleted in `19313eed`; guarded live by `tests/test_suite_exit_code_authority.py`), whose own docstring records
    --
    28616-# derived them from an always-empty string, so every lane passed INCLUDING one that broke everything;
    28617:# `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` (deleted in `19313eed`;
    28618-# guarded live by `tests/test_suite_exit_code_authority.py`) existed for that case and called it the most important in its
    --
    28748-    the list alone - and the EXIT CODE, not the list, is this repository's authority on which one it
    28749:    is (`tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` was deleted in
    28750-    `19313eed`; guarded live by `tests/test_suite_exit_code_authority.py`). It DEFAULTS False, the conservative reading, so
    --
    28941-      1. AN EMPTY MERGED FAILING LIST ON A NON-PASSING SUITE IS UNKNOWN. This is the `32ij2j` inversion
    28942:         (`tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList`, deleted in
    28943-         `19313eed`; guarded live by `tests/test_suite_exit_code_authority.py`): with a merged
    ```
    Bare `python3 -m pytest` output for V-04 (run last, after E-05 edit):
    ```
    $ python3 -m pytest
    NOTE: 5 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    707 passed in 23.09s
    ```
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

- **Execution contract**: Execute only after explicit human approval (`Status: approved`). All open questions are resolved. Start with `aw ipd begin xssw86`, and run E-01..E-04 in dependency order. Do not mark an `E-*` `performed` before doing it, and do not mark a `V-*` `pass` without pasting the observed command output into `Observed evidence:`. You MUST paste the actual runner output for every test or check you report; never claim a result you did not run. Run the full suite bare as `python3 -m pytest` (never `-n0`, never an extra `-q`, never `-p no:randomly`).
- **Scope fence**: `- Scope-Paths:` declares the intended edit set. An edit outside it is allowed when the work requires it, but it must be justified at finalize (`--scope-reason` per out-of-scope path). Delete the mutation plugin and any other scratch files.
- **Commit**: Commit only your own paths via `aw commit xssw86 -- <paths>`; never push.
- **Post-gate lifecycle move**: Under `aw oc run` / `aw agy run`, the runner finalizes after its merge-and-revalidate gate, so do NOT run `aw ipd finalize` yourself. When executing by hand, once every `E-*` is `performed`, every `V-*` is `pass`, and `aw ipd lint --phase pre-transition` reports no errors, finalize via `aw ipd finalize xssw86`. Never hand-`git mv` the plan to `executed/`.
