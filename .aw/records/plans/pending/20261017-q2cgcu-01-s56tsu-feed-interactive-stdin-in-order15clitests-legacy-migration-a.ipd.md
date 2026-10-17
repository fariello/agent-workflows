# IPD: Feed interactive stdin in Order15CliTests legacy migration accept test

- Date: 2026-10-17
- Kind: child
- Concern: `Order15CliTests.test_install_legacy_repo_interactive_accept_migrates_to_aw` in `tests/test_cli.py` mocks `sys.stdin.isatty` to return `True` while leaving `sys.stdin` pointed at pytest's captured stream. Because `_run_install` continues through `collect_policy_interactive` and `_confirm_install` after migration, those helpers call `input()`, which attempts to read from captured stdin and causes flakiness or hangs under `pytest-xdist`. The test was consequently quarantined with `@pytest.mark.xfail(strict=False, reason="flaky: q2cgcu - prompts on captured stdin under xdist")`.
- Scope: Update `Order15CliTests.test_install_legacy_repo_interactive_accept_migrates_to_aw` in `tests/test_cli.py` to mock `sys.stdin` with `io.StringIO("\n\n")` (supplying interactive answers to subsequent prompts without reading from captured stdin) instead of patching `sys.stdin.isatty` directly, and remove the `@pytest.mark.xfail` quarantine decorator so the test executes and passes cleanly under pytest-xdist.
- Scope-Paths: tests/test_cli.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: q2cgcu
- Set: q2cgcu
- Order: 1
- Highest E allocated: 02
- Author: antigravity
- Id: s56tsu

## Workflow history

- 2026-10-17 to-review (antigravity): authored from backlog q2cgcu with findings, checklist, and validation.
- 2026-10-17 draft (antigravity): created.

## Goal

Restore clean, unquarantined execution for `Order15CliTests.test_install_legacy_repo_interactive_accept_migrates_to_aw` under `pytest-xdist` by feeding `io.StringIO` to `sys.stdin` during interactive installation testing, eliminating captured-stdin prompts and removing the `@pytest.mark.xfail` quarantine decorator.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Test update and unquarantine

- [ ] E-01 In `tests/test_cli.py` within `Order15CliTests.test_install_legacy_repo_interactive_accept_migrates_to_aw`, remove the `@pytest.mark.xfail(strict=False, reason="flaky: q2cgcu - prompts on captured stdin under xdist")` decorator and replace `with mock.patch("sys.stdin.isatty", return_value=True):` with `with mock.patch("sys.stdin", io.StringIO("\n\n")):` so that all interactive prompts in `_run(["install", str(repo)])` (`collect_policy_interactive` and `_confirm_install`) receive predetermined newline answers from the in-memory string stream without prompting on captured stdin.
  - Depends on: none
  - Expected outcome: the test runs interactively without reading from pytest's captured stdin stream, and the quarantine decorator is removed.
  - Execution state: pending
- [ ] E-02 Run the test suite targeting `Order15CliTests.test_install_legacy_repo_interactive_accept_migrates_to_aw` and the full `Order15CliTests` class under pytest with xdist enabled and `-m "slow or not slow"`, verifying that `test_install_legacy_repo_interactive_accept_migrates_to_aw` passes with a true `PASSED` status (no `XPASS` or `XFAIL`) and no worker hangs or stdin capture errors.
  - Depends on: E-01
  - Expected outcome: `tests/test_cli.py::Order15CliTests::test_install_legacy_repo_interactive_accept_migrates_to_aw` passes cleanly under xdist.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Tests in `tests/test_installer.py` (e.g. `test_prompt_case_p_attended_empty_answer_removes_leftover`, `test_prompt_case_q_attended_n_keeps_leftover_and_reports_defer`) and `tests/test_migrate_layout_cli.py` mock `sys.stdin` with `io.StringIO(...)` to feed canned responses to interactive CLI commands without relying on captured stdin.
- The interactive CLI helpers in `agent_workflows/cli.py` (`_ask_policy`, `_confirm_install`, `_install_leftover_disposition`) and `agent_workflows/install_wizard.py` (`collect_policy_interactive`) explicitly inspect `isinstance(sys.stdin, io.StringIO)` alongside TTY checks to detect interactive test streams.
- Tests must exercise observable outcomes and side effects rather than pinning code structure (AGENTS.md rule "TEST OUTCOMES, NOT CODE STRUCTURE").
- `tests/test_cli.py::Order15CliTests::test_install_legacy_repo_interactive_accept_migrates_to_aw` is listed in `tests/slow_allowlist.txt` under `Full repo install/uninstall filesystem fixture tree lifecycle`, requiring `-m "slow or not slow"` when running pytest specifically on it.

## Findings

| Finding | Severity | Description |
|---|---|---|
| F-01 | Medium | `Order15CliTests.test_install_legacy_repo_interactive_accept_migrates_to_aw` patched `sys.stdin.isatty` to return `True` but did not provide an input stream. When `_ask_policy` returned `True`, the legacy migration succeeded and `cli._run_install` continued to `collect_policy_interactive` and `_confirm_install`. Both called `input()`, reading from pytest's captured stdin and causing flaky hangs or capture errors under `pytest-xdist`. |
| F-02 | Low | In commit `f762cafceda161e1364b6605fc0f7a166bf4b261`, the test was quarantined with `@pytest.mark.xfail(strict=False, reason="flaky: q2cgcu - prompts on captured stdin under xdist")` to allow the testprune suite to pass. Replacing the `sys.stdin.isatty` mock with `mock.patch("sys.stdin", io.StringIO("\n\n"))` eliminates the root cause and allows unquarantining the test. |

## Proposed changes (ordered, validatable)

1. E-01: Remove `@pytest.mark.xfail` and update `test_install_legacy_repo_interactive_accept_migrates_to_aw` in `tests/test_cli.py` to mock `sys.stdin` with `io.StringIO("\n\n")`.
2. E-02: Run pytest across the targeted test and class under xdist to verify green execution.

## Deferred / out of scope (with reason)

- Sister test `tests/test_cli.py::Order15CliTests::test_install_legacy_repo_interactive_decline_keeps_legacy`: quarantined under open backlog item `zcouni` due to `UnboundLocalError on PolicyCancelledError in cli._run_install when kept_legacy is True`.
  - Carrier-Declined: tracked under separate open backlog item zcouni with its own bug fix scope

## Scope check

- Over-scope: none. Changes are restricted solely to `tests/test_cli.py`.
- Under-scope: none. The change directly resolves the captured stdin prompt mechanism identified in backlog item `q2cgcu`.

## Required tests / validation

- `python3 -m pytest tests/test_cli.py -k "test_install_legacy_repo_interactive_accept_migrates_to_aw" -m "slow or not slow" -v` reports `1 passed` (not xpassed).
- `python3 -m pytest tests/test_cli.py -k "Order15CliTests" -m "slow or not slow" -v` reports all runnable tests in `Order15CliTests` passing with no stdin capture hangs or errors.
- Core test suite run via `python3 -m pytest` passes.

## Spec / documentation sync

N/A: no specification or documentation changes are required; this change adjusts test harness input stream mocking for an existing CLI test.

## Open questions

### OQ-01: Should sys.stdin be mocked with io.StringIO instead of patching builtins.input?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes. Mocking `sys.stdin` with `io.StringIO` is the established pattern in `tests/test_installer.py` and `tests/test_migrate_layout_cli.py`. Furthermore, `agent_workflows/cli.py` and `agent_workflows/install_wizard.py` explicitly check `isinstance(sys.stdin, io.StringIO)` to determine interactivity. Mocking `sys.stdin` tests the actual input stream handling without intercepting `builtins.input`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff tests/test_cli.py` showing removal of the `@pytest.mark.xfail` quarantine decorator and replacement of `mock.patch("sys.stdin.isatty", return_value=True)` with `mock.patch("sys.stdin", io.StringIO("\n\n"))`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the summary line of `python3 -m pytest tests/test_cli.py -k "test_install_legacy_repo_interactive_accept_migrates_to_aw" -m "slow or not slow" -v` showing `1 passed`, and paste the summary line of `python3 -m pytest tests/test_cli.py -k "Order15CliTests" -m "slow or not slow" -v` showing zero failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Commit only files you changed, through `aw commit s56tsu -- tests/test_cli.py`; never `git add -A`, never push. You MUST paste the ACTUAL runner output into each `V-*`; never claim a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Lifecycle: after every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize` itself.
