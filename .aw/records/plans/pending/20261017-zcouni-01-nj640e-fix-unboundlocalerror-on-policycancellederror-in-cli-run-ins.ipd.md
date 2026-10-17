# IPD: Fix UnboundLocalError on PolicyCancelledError in cli._run_install when kept_legacy is True

- Date: 2026-10-17
- Kind: child
- Concern: In `agent_workflows.cli._run_install`, `PolicyCancelledError` is imported lazily inside `if not kept_legacy:` (along with other wizard policy types). When installing into a legacy repository and migration is declined (or `--keep-legacy` is specified), `kept_legacy` is `True` and the `if not kept_legacy:` branch is bypassed. When execution reaches the final confirmation gate (`_confirm_install`), a user cancellation (e.g. `KeyboardInterrupt`, which `_confirm_install` translates into `PolicyCancelledError`) triggers the enclosing `except PolicyCancelledError:` handler in `_run_install`. Because `PolicyCancelledError` was only bound inside the skipped `if not kept_legacy:` block, Python treats `PolicyCancelledError` as an unassigned local variable and raises `UnboundLocalError: cannot access local variable 'PolicyCancelledError' where it is not associated with a value`. Consequently, `Order15CliTests.test_install_legacy_repo_interactive_decline_keeps_legacy` was quarantined under `@pytest.mark.xfail(strict=False, reason="flaky: zcouni - UnboundLocalError on PolicyCancelledError")` due to prompting on captured stdin and crashing on cancellation.
- Scope: In `agent_workflows/cli.py`, import `PolicyCancelledError` unconditionally in `cli._run_install` (at function entry before the repository iteration loop) so the `except PolicyCancelledError:` exception handler is always bound regardless of whether `kept_legacy` is True or False. In `tests/test_cli.py`, remove the `@pytest.mark.xfail` quarantine decorator from `Order15CliTests.test_install_legacy_repo_interactive_decline_keeps_legacy` and provide mocked interactive input (`io.StringIO("\n")`) so it runs cleanly without reading captured stdin. Add a dedicated test verifying that when `kept_legacy` is True and `_confirm_install` raises `PolicyCancelledError`, `_run_install` catches `PolicyCancelledError` cleanly, emits `install cancelled; nothing written.`, and exits with return code 1 without raising `UnboundLocalError`.
- Scope-Paths: agent_workflows/cli.py, tests/test_cli.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: zcouni
- Blocks-Release: next
- Set: zcouni
- Order: 1
- Highest E allocated: 03
- Author: antigravity
- Id: nj640e

## Workflow history

- 2026-10-17 to-review (antigravity): authored from backlog zcouni with findings, checklist, and validation.
- 2026-10-17 draft (antigravity): created.

## Goal

Ensure `cli._run_install` unconditionally binds `PolicyCancelledError` so that cancellation during legacy-mode installation handling catches cleanly rather than crashing with `UnboundLocalError`, unquarantine `Order15CliTests.test_install_legacy_repo_interactive_decline_keeps_legacy`, and add regression coverage for legacy install cancellation.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Unconditional import in _run_install

- [ ] E-01 In `agent_workflows/cli.py` within `_run_install`, import `PolicyCancelledError` from `agent_workflows.install_wizard` at function entry (before the repository iteration loop and before any `_handle_legacy_migration` check) so that `PolicyCancelledError` is unconditionally in scope across all execution branches of `_run_install`, ensuring that the `except PolicyCancelledError:` block wrapping the install confirmation can safely evaluate and handle cancellation when `kept_legacy` is True.
  - Depends on: none
  - Expected outcome: `PolicyCancelledError` is bound at `_run_install` function entry and in scope regardless of whether `kept_legacy` is True.
  - Execution state: pending

### Task group 2: Test unquarantine and regression coverage

- [ ] E-02 In `tests/test_cli.py`, remove the `@pytest.mark.xfail(strict=False, reason="flaky: zcouni - UnboundLocalError on PolicyCancelledError")` decorator from `Order15CliTests.test_install_legacy_repo_interactive_decline_keeps_legacy`, and replace `with mock.patch("sys.stdin.isatty", return_value=True):` with `with mock.patch("sys.stdin", io.StringIO("\n")):` so that all interactive prompts in `_run(["install", str(repo)])` receive predetermined newline answers from the in-memory string stream without prompting on captured stdin.
  - Depends on: E-01
  - Expected outcome: `test_install_legacy_repo_interactive_decline_keeps_legacy` is unquarantined and runs without reading pytest captured stdin.
  - Execution state: pending
- [ ] E-03 In `tests/test_cli.py` within `Order15CliTests`, add `test_install_legacy_repo_interactive_decline_cancellation_handles_policy_cancelled_error` which simulates legacy migration decline (`_ask_policy` returning False, so `kept_legacy` is True) followed by a `PolicyCancelledError` raised during `_confirm_install` (e.g. simulating user cancellation / `KeyboardInterrupt`), verifying that `_run_install` catches `PolicyCancelledError` cleanly without raising `UnboundLocalError`, outputs `install cancelled; nothing written.`, and exits with return code 1.
  - Depends on: E-01
  - Expected outcome: regression test explicitly asserting that legacy install cancellation exits cleanly without `UnboundLocalError`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Tests in `tests/test_installer.py` and `tests/test_migrate_layout_cli.py` mock `sys.stdin` with `io.StringIO(...)` to feed canned responses to interactive CLI commands without relying on captured stdin.
- The interactive CLI helpers in `agent_workflows/cli.py` (`_ask_policy`, `_confirm_install`, `_install_leftover_disposition`) and `agent_workflows/install_wizard.py` (`collect_policy_interactive`) explicitly inspect `isinstance(sys.stdin, io.StringIO)` alongside TTY checks to detect interactive test streams.
- `agent_workflows/cli.py` defers imports into function bodies to maintain fast CLI startup times; importing `PolicyCancelledError` at `cli._run_install` function entry maintains this lazy-loading pattern while guaranteeing scope availability for the entire install routine.
- Tests must exercise observable outcomes and side effects rather than pinning code structure (AGENTS.md rule "TEST OUTCOMES, NOT CODE STRUCTURE").
- `tests/test_cli.py::Order15CliTests::test_install_legacy_repo_interactive_decline_keeps_legacy` is listed in `tests/slow_allowlist.txt` under `Full repo install/uninstall filesystem fixture tree lifecycle`, requiring `-m "slow or not slow"` when running pytest specifically on it.

## Findings

| Finding | Severity | Description |
|---|---|---|
| F-01 | High | `agent_workflows.cli._run_install` imports `PolicyCancelledError` inside `if not kept_legacy:`. When `kept_legacy` is True, that block is skipped. Later in `_run_install`, the final confirmation gate is wrapped in `try: ... except PolicyCancelledError:`. Because Python assigns local scope to `PolicyCancelledError` at compile time, the skipped branch leaves the variable unassigned, causing `UnboundLocalError` when any cancellation or exception handling evaluates the `except` clause. |
| F-02 | Medium | `Order15CliTests.test_install_legacy_repo_interactive_decline_keeps_legacy` patched `sys.stdin.isatty` to return True without providing an input stream. When `_ask_policy` declined migration, execution continued to `_confirm_install`, calling `input()` on captured stdin. In commit `f762cafceda161e1364b6605fc0f7a166bf4b261`, the test was quarantined with `@pytest.mark.xfail(strict=False, reason="flaky: zcouni - UnboundLocalError on PolicyCancelledError")`. |
| F-03 | Low | There was no dedicated regression test verifying that cancelling during the install confirmation of a legacy repository (`kept_legacy` is True) gracefully catches `PolicyCancelledError` and terminates with a skip status instead of crashing. |

## Proposed changes (ordered, validatable)

1. E-01: In `agent_workflows/cli.py`, add `from agent_workflows.install_wizard import PolicyCancelledError` at `_run_install` function entry.
2. E-02: In `tests/test_cli.py`, unquarantine `test_install_legacy_repo_interactive_decline_keeps_legacy` by removing `@pytest.mark.xfail` and mock `sys.stdin` with `io.StringIO("\n")`.
3. E-03: In `tests/test_cli.py`, add `test_install_legacy_repo_interactive_decline_cancellation_handles_policy_cancelled_error` to assert graceful cancellation without `UnboundLocalError` when `kept_legacy` is True.

## Deferred / out of scope (with reason)

- Sister test `tests/test_cli.py::Order15CliTests::test_install_legacy_repo_interactive_accept_migrates_to_aw`: quarantined under backlog item `q2cgcu` and addressed in plan `s56tsu`.
  - Carrier-Declined: tracked under separate open backlog item q2cgcu and plan s56tsu

## Scope check

- Over-scope: none. Changes are restricted solely to `agent_workflows/cli.py` and `tests/test_cli.py`.
- Under-scope: none. Directly resolves the `UnboundLocalError` root cause, unquarantines the affected test, and adds regression coverage.

## Required tests / validation

- `python3 -m pytest tests/test_cli.py -k "test_install_legacy_repo_interactive_decline_keeps_legacy" -m "slow or not slow" -v` reports `1 passed` (not xfail or xpass).
- `python3 -m pytest tests/test_cli.py -k "test_install_legacy_repo_interactive_decline_cancellation_handles_policy_cancelled_error" -m "slow or not slow" -v` reports `1 passed`.
- `python3 -m pytest tests/test_cli.py -k "Order15CliTests" -m "slow or not slow" -v` reports all runnable tests in `Order15CliTests` passing cleanly with zero failures.
- Core test suite run via `python3 -m pytest` passes.

## Spec / documentation sync

N/A: no specification or documentation changes are required; this change fixes an unhandled variable binding bug in an internal CLI command handler and updates test coverage.

## Open questions

### OQ-01: Should PolicyCancelledError be imported at module scope or within cli._run_install?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Importing at the top of `cli._run_install` preserves the lazy-import convention established throughout `agent_workflows/cli.py` to maintain quick CLI startup, while unconditionally ensuring the symbol is in scope throughout `_run_install` before any branching on `kept_legacy`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff agent_workflows/cli.py` showing `from agent_workflows.install_wizard import PolicyCancelledError` at `cli._run_install` function entry before the repository iteration loop.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `git diff tests/test_cli.py` showing removal of `@pytest.mark.xfail` from `test_install_legacy_repo_interactive_decline_keeps_legacy` and replacement with `mock.patch("sys.stdin", io.StringIO("\n"))`, and paste the runner output of `python3 -m pytest tests/test_cli.py -k "test_install_legacy_repo_interactive_decline_keeps_legacy" -m "slow or not slow" -v` showing `1 passed`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `git diff tests/test_cli.py` showing the new regression test `test_install_legacy_repo_interactive_decline_cancellation_handles_policy_cancelled_error`, and paste the runner output of `python3 -m pytest tests/test_cli.py -k "test_install_legacy_repo_interactive_decline_cancellation_handles_policy_cancelled_error" -m "slow or not slow" -v` showing `1 passed`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Commit only files you changed, through `aw commit nj640e -- agent_workflows/cli.py tests/test_cli.py`; never `git add -A`, never push. You MUST paste the ACTUAL runner output into each `V-*`; never claim a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Lifecycle: after every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize` itself.
