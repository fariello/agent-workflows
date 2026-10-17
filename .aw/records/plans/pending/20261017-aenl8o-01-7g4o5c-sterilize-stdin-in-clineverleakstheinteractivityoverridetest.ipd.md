# IPD: Sterilize stdin in CliNeverLeaksTheInteractivityOverrideTests to prevent captured stdin prompting under xdist

- Date: 2026-10-17
- Kind: child
- Concern: In `tests/test_term.py`, `CliNeverLeaksTheInteractivityOverrideTests.test_early_exit_paths_and_nested_invocations` tests `("--interactive with no verb at all", ["--interactive"])` with stdout and stderr redirected, but unredirected stdin. In an unconfigured environment, `--interactive` forces `_term_mod.is_interactive()` to return `True`, causing `cli.py` to enter `_run_setup(...)`, which calls `input()` on `sys.stdin`. Under pytest and xdist, captured stdin either raises `OSError` (uncaught by `cli.main`) or blocks waiting for input during concurrent execution. As a result, the test was quarantined with `@pytest.mark.xfail(strict=False, reason="flaky: aenl8o - prompts on captured stdin during concurrent CLI execution")`.
- Scope: In `tests/test_term.py`, redirect `sys.stdin` to an empty stream `io.StringIO("")` during `cli.main` invocations in `CliNeverLeaksTheInteractivityOverrideTests`, remove the quarantine `xfail` mark, and ensure clean EOF handling and override restoration for bare flag invocations. OUT: changing `_run_setup` or `cli.py` interactive dispatch logic (which correctly prompts when configured to be interactive).
- Scope-Paths: tests/test_term.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: aenl8o
- Set: aenl8o
- Order: 1
- Highest E allocated: 03
- Author: antigravity
- Id: 7g4o5c

## Workflow history

- 2026-10-17 to-review (antigravity): authored review-ready from backlog aenl8o.
- 2026-10-17 draft (antigravity): created.

## Goal

Sterilize standard input during CLI invocations in `CliNeverLeaksTheInteractivityOverrideTests` by redirecting `sys.stdin` to an empty stream, preventing interactive prompts from blocking or failing on captured stdin under xdist, and un-quarantine the test so it executes actively in the suite.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Sterilize stdin and un-quarantine test

- [ ] E-01 In `tests/test_term.py` class `CliNeverLeaksTheInteractivityOverrideTests`, update `test_early_exit_paths_and_nested_invocations` to wrap all `cli.main(...)` invocations (both the loop over `EARLY_EXIT_PATHS` and the subsequent nested invocation assertions) in `contextlib.redirect_stdin(io.StringIO(""))` alongside `redirect_stdout` and `redirect_stderr`. Remove the `@pytest.mark.xfail(strict=False, reason="flaky: aenl8o - prompts on captured stdin during concurrent CLI execution")` decorator so the test is un-quarantined.
  - Depends on: none
  - Expected outcome: `test_early_exit_paths_and_nested_invocations` runs with sterilized stdin, `["--interactive"]` encounters immediate EOF in `_run_setup`, `cli.main` catches `EOFError` and returns 130 cleanly, and the test runs actively without the xfail decorator.
  - Execution state: pending

### Task group 2: Bare flag interactivity coverage

- [ ] E-02 In `tests/test_term.py` class `CliNeverLeaksTheInteractivityOverrideTests`, expand coverage over bare flag invocations with empty stdin to verify that: (1) `EARLY_EXIT_PATHS` includes `("--no-interactive with no verb at all", ["--no-interactive"])` alongside `("--interactive with no verb at all", ["--interactive"])`; (2) both bare flag invocations leave `T.get_interactive_override()` as `None` when called from a flagless baseline; and (3) an outer override is properly restored after an inner bare `--interactive` or `--no-interactive` call with empty stdin.
  - Depends on: E-01
  - Expected outcome: Both bare flags `--interactive` and `--no-interactive` are validated across flagless reset and nested restoration boundaries with sterile stdin.
  - Execution state: pending

### Task group 3: Test suite validation

- [ ] E-03 Run the test suite: run `python3 -m pytest -o addopts="" -q tests/test_term.py -k CliNeverLeaksTheInteractivityOverrideTests`, run `python3 -m pytest -o addopts="" -q tests/test_term.py` for the full module, and run the routine core gate `python3 -m pytest` with `pytest-randomly` enabled.
  - Depends on: E-01, E-02
  - Expected outcome: All tests in `CliNeverLeaksTheInteractivityOverrideTests` pass actively (reported as PASSED, zero xfail, zero xpass), the full `test_term.py` module passes, and the routine gate passes with exit 0.
  - Execution state: pending

## Project conventions discovered (Step 0)

- AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE": tests assert observable behavior and exit outcomes, never internal source code or line counts.
- `cli.main()` in `agent_workflows/cli.py` (around `except EOFError:`) catches `EOFError` and exits 130 (`Cancelled (end of input).`), and its `finally` block (around `_term_mod.set_interactive_override`) restores `_term_mod.set_interactive_override(_entry_interactive_override)`.
- When `--interactive` is passed with no verb in an unconfigured test environment, `agent_workflows.cli._dispatch` calls `_run_setup()`, which calls `input()` on `sys.stdin`.
- Pytest captures `sys.stdin` (replacing it with `DontReadFromInput`). Calling `input()` on unredirected captured stdin raises `OSError` ("reading from stdin while output is captured") or blocks on stdin, which flaky-quarantined `test_early_exit_paths_and_nested_invocations` in commit `f762cafce`.
- Standard library `contextlib.redirect_stdin(io.StringIO(""))` safely simulates an empty terminal / pipe at EOF without touching physical process streams.
- Routine gate: bare `python3 -m pytest`; narrowed runs: `python3 -m pytest -o addopts="" <path>`. Commits go through `aw commit <plan> -- <paths>`.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F1 | `test_early_exit_paths_and_nested_invocations` was quarantined as flaky with `strict=False` in commit `f762cafce`. | `git show f762cafce -- tests/test_term.py` adds `@pytest.mark.xfail(strict=False, reason="flaky: aenl8o - prompts on captured stdin during concurrent CLI execution")`. |
| F2 | The test iterates over `EARLY_EXIT_PATHS`, which includes `("--interactive with no verb at all", ["--interactive"])`. | `tests/test_term.py` under `EARLY_EXIT_PATHS`. |
| F3 | `cli.main(["--interactive"])` enters interactive setup when unconfigured. | `agent_workflows/cli.py` under `_dispatch`: `if args.command is None: if not config.is_configured(): if _term_mod.is_interactive(): return _run_setup(...)`. |
| F4 | `_run_setup` prompts on standard input. | `agent_workflows/cli.py` in `_run_setup`: `entry = input("  root> ").strip()`. |
| F5 | `test_early_exit_paths_and_nested_invocations` redirects stdout and stderr, but leaves `sys.stdin` untouched. | `tests/test_term.py` in `test_early_exit_paths_and_nested_invocations`: `with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf): cli.main(list(argv))`. |
| F6 | `cli.main()` handles `EOFError` cleanly with exit code 130 and executes its `finally` restoration block. | `agent_workflows/cli.py` in `main()`: `except EOFError: ... return 130` and `finally: _term_mod.set_interactive_override(...)`. |

## Proposed changes (ordered, validatable)

1. E-01: Update `test_early_exit_paths_and_nested_invocations` in `tests/test_term.py` to redirect `sys.stdin` to `io.StringIO("")` during `cli.main` calls and remove the quarantine `xfail` decorator. Validated by V-01.
2. E-02: Expand bare flag coverage in `CliNeverLeaksTheInteractivityOverrideTests` to test both `--interactive` and `--no-interactive` with empty stdin across flagless reset and nested invocation restoration. Validated by V-02.
3. E-03: Run pytest across the targeted test class, the full `tests/test_term.py` module, and the bare `python3 -m pytest` core gate. Validated by V-03.

## Deferred / out of scope (with reason)

- Modifying `cli.py` smart-default dispatch logic or `_run_setup`: when an operator explicitly passes `--interactive` with no verb in an unconfigured environment, interactive setup is intended behavior (decision D7); the issue is solely test isolation of `sys.stdin`.
  - Carrier-Declined: production behavior is intentional; issue is test environment stdin isolation.
- Auditing other CLI tests for unredirected stdin: outside the scope of backlog item `aenl8o`; separate backlog items exist for other quarantined tests (e.g. `q2cgcu`).
  - Carrier-Declined: other tests tracked in separate backlog items.

## Scope check

- Over-scope: none.
- Under-scope: none; resolves the captured stdin prompt and un-quarantines the test.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_term.py -k CliNeverLeaksTheInteractivityOverrideTests` reports all tests passing as PASSED (zero failures, zero xfailed, zero xpassed).
- `python3 -m pytest -o addopts="" -q tests/test_term.py` reports the full module passes.
- Bare `python3 -m pytest` passes cleanly.

## Spec / documentation sync

N/A: test isolation fix and quarantine removal; no user-facing documentation or specification contracts changed.

## Open questions

None. The root cause and fix are verified directly from code inspection in `agent_workflows/cli.py` and `tests/test_term.py` (F1 to F6). No maintainer decision is required.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: `git diff -- tests/test_term.py` showing `contextlib.redirect_stdin(io.StringIO(""))` added to `cli.main` invocations in `test_early_exit_paths_and_nested_invocations` and the removal of `@pytest.mark.xfail`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git diff -- tests/test_term.py` showing bare `--no-interactive` and `--interactive` coverage with empty stdin, and pasted pytest output showing all test cases in `CliNeverLeaksTheInteractivityOverrideTests` pass.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted test runner output for: (1) `python3 -m pytest -o addopts="" -q tests/test_term.py -k CliNeverLeaksTheInteractivityOverrideTests` showing all tests PASSED without xfail/xpass; (2) `python3 -m pytest -o addopts="" -q tests/test_term.py`; and (3) bare `python3 -m pytest` core suite passing with exit 0.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution.

Execution contract:
- All open questions are resolved.
- Scope fence: see Scope check; an out-of-scope edit is made and justified at finalize, not a reason to stop.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Tests assert observable behavior (real outputs, exit codes, files written), never source text or structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Commit only through `aw commit 7g4o5c -- tests/test_term.py`, verify `git diff --cached --name-only` lists only your paths, never `git add -A`, and never push.
- Lifecycle: after every V-item reads `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize` itself.
