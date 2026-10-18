# IPD: Sterilize stdin in CliNeverLeaksTheInteractivityOverrideTests to prevent captured stdin prompting under xdist

- Date: 2026-10-17
- Kind: child
- Concern: In `tests/test_term.py`, `CliNeverLeaksTheInteractivityOverrideTests.test_early_exit_paths_and_nested_invocations` drives `cli.main(["--interactive"])` (case "--interactive with no verb at all") with stdout and stderr redirected but `sys.stdin` left as whatever the process inherited. In an unconfigured test home, `--interactive` forces `_term_mod.is_interactive()` True, so `cli._dispatch` enters `_run_setup(...)`, which calls `input("  root> ")` on the ambient `sys.stdin`. The test was quarantined in commit `f762cafce` with `@pytest.mark.xfail(strict=False, reason="flaky: aenl8o - prompts on captured stdin during concurrent CLI execution")`. Measured at review (2026-10-18, lane HEAD `08fa69666`): the ambient stdin in a pytest worker is `/dev/null` (`tests/__init__.py` reopens fd 0 and `sys.stdin` on `os.devnull`), so `input()` raises `EOFError`, `cli.main` returns 130, and the test currently XPASSes (3 of 3 runs under `-n 4`). The exact mechanism of the recorded flake is therefore NOT reproduced (cause unknown); the test's correctness still depends on an ambient stdin it does not control, which is the defect this plan removes.
- Scope: In `tests/test_term.py`, patch `sys.stdin` to an empty `io.StringIO("")` around every `cli.main` call in `CliNeverLeaksTheInteractivityOverrideTests.test_early_exit_paths_and_nested_invocations`, remove the quarantine `xfail` mark (and the then-unused `import pytest`), and assert the bare `--interactive` invocation's observable outcome (returns 130 at EOF) plus override restoration around it. OUT: changing `_run_setup` or `cli.py` interactive dispatch logic (which correctly prompts when interactivity is forced).
- Scope-Paths: tests/test_term.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: aenl8o
- Set: aenl8o
- Order: 1
- Highest E allocated: 03
- Author: antigravity
- Id: 7g4o5c

## Workflow history
- 2026-10-18 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-006
- 2026-10-17 to-review (antigravity): authored review-ready from backlog aenl8o.
- 2026-10-17 draft (antigravity): created.

## Goal

Make `CliNeverLeaksTheInteractivityOverrideTests` independent of the process's ambient standard input by patching `sys.stdin` to an empty stream during every `cli.main` invocation, so the bare `--interactive` setup prompt deterministically meets EOF, and un-quarantine the test so it runs actively (PASSED, never xfail/xpass) in the suite.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Sterilize stdin and un-quarantine test

- [ ] E-01 In `tests/test_term.py` class `CliNeverLeaksTheInteractivityOverrideTests`, update `test_early_exit_paths_and_nested_invocations` so EVERY `cli.main(...)` call (the loop over `EARLY_EXIT_PATHS` and both subsequent nested-invocation blocks) runs inside `mock.patch("sys.stdin", io.StringIO(""))` (import `from unittest import mock` at module top, or reuse the module's existing local import style) alongside the existing `contextlib.redirect_stdout`/`redirect_stderr`. Do NOT use `contextlib.redirect_stdin`: it does not exist in the standard library (verified on the repo's Python 3.14.6: `hasattr(contextlib, "redirect_stdin")` is `False`). Remove the `@pytest.mark.xfail(strict=False, reason="flaky: aenl8o - ...")` decorator, and remove `import pytest` (line 15) if no other use remains, so ruff F401 does not fire.
  - Depends on: none
  - Expected outcome: The test runs with a sterile, test-owned stdin; the bare `["--interactive"]` case meets immediate EOF in `_run_setup`, `cli.main` catches `EOFError` and returns 130; the test carries no xfail mark and reports PASSED.
  - Execution state: pending

### Task group 2: Bare --interactive outcome and restoration coverage

- [ ] E-02 In the same test (or a sibling method in the same class), with `sys.stdin` patched to `io.StringIO("")`, assert observable outcomes of the bare `--interactive` invocation: (1) from a flagless baseline (`T.set_interactive_override(None)`), `cli.main(["--interactive"])` RETURNS 130 (it must not raise) and leaves `T.get_interactive_override()` as `None`; (2) with an outer override of `False`, and again with an outer override of `True`, an inner `cli.main(["--interactive"])` returns 130 and leaves `T.get_interactive_override()` equal to the outer value (`is False` / `is True`). Do NOT add bare `["--no-interactive"]` (no verb) cases: that path never reads stdin (it prints a status summary) and measured 5.46s and 5.62s per call at review, versus 0.3s for bare `--interactive`.
  - Depends on: E-01
  - Expected outcome: Bare `--interactive` is pinned by its exit code (130 at EOF) and by override restoration across the flagless baseline and both outer-override values, all with sterile stdin.
  - Execution state: pending

### Task group 3: Test suite validation

- [ ] E-03 Run: (a) `python3 -m pytest -o addopts="" -rA -p no:cacheprovider tests/test_term.py -k CliNeverLeaksTheInteractivityOverrideTests`; (b) five repeated concurrent runs `for i in 1 2 3 4 5; do python3 -m pytest -o addopts="" -n 6 -rxX tests/test_term.py -k CliNeverLeaksTheInteractivityOverrideTests; done` (pytest-randomly stays enabled, so each run uses a different seed); (c) `python3 -m pytest -o addopts="" -n 6 tests/test_term.py` for the full module; (d) the routine core gate bare `python3 -m pytest`. Note: `tests/test_term.py` carries no `core` marker (bare `python3 -m pytest --collect-only -q` collected 0 of its tests at review), so (d) is a no-regression gate for the suite, not evidence about this test; (a) to (c) are the evidence for this test.
  - Depends on: E-01, E-02
  - Expected outcome: Every test in `CliNeverLeaksTheInteractivityOverrideTests` reports PASSED in (a) and in each of the five (b) runs, with zero xfailed and zero xpassed; (c) reports no failures; (d) exits 0.
  - Execution state: pending

## Project conventions discovered (Step 0)

- AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE": tests assert observable behavior and exit outcomes, never internal source code or line counts.
- `cli.main()` in `agent_workflows/cli.py` (`def main`, the `except EOFError:` branch printing `Cancelled (end of input).`) returns 130, and its `finally` block calls `_term_mod.set_interactive_override(_entry_interactive_override)`, restoring the override the call inherited.
- When `--interactive` is passed with no verb in an unconfigured home, `agent_workflows.cli._dispatch` (`if args.command is None:` / `if not config.is_configured():` / `if _term_mod.is_interactive():`) calls `_run_setup()`, which calls `input("  root> ")` on `sys.stdin`.
- The suite already sterilizes the process stdin: `tests/__init__.py` (the "Interactive-prompt guard" block) `os.dup2`s `/dev/null` onto fd 0 and sets `sys.stdin = open(os.devnull, "r")`, so an unguarded `input()` raises `EOFError`. A test that depends on that ambient guard is still fragile; owning stdin per test is the convention used elsewhere.
- Existing convention for a sterile stdin in CLI tests: `mock.patch("sys.stdin", io.StringIO(""))` (for example `tests/test_installer.py`, `test_prompt_case_r_yes_flag_never_prompts_and_removes`). `contextlib` has no `redirect_stdin`.
- Routine gate: bare `python3 -m pytest` selects only `core`-marked tests (`conftest.py` `pytest_collection_modifyitems`); narrowed runs: `python3 -m pytest -o addopts="" <path>`. Commits go through `aw commit <plan> -- <paths>`. `ruff` runs as a pre-commit hook (`.pre-commit-config.yaml`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F1 | `test_early_exit_paths_and_nested_invocations` was quarantined as flaky with `strict=False` in commit `f762cafce`. | `git show f762cafce -- tests/test_term.py` adds `import pytest` and `@pytest.mark.xfail(strict=False, reason="flaky: aenl8o - prompts on captured stdin during concurrent CLI execution")`. |
| F2 | The test iterates over `EARLY_EXIT_PATHS`, which includes `("--interactive with no verb at all", ["--interactive"])`. | `tests/test_term.py` `CliNeverLeaksTheInteractivityOverrideTests.EARLY_EXIT_PATHS`. |
| F3 | `cli.main(["--interactive"])` enters interactive setup when unconfigured. | `agent_workflows/cli.py` `_dispatch`: `if args.command is None: if not config.is_configured(): if _term_mod.is_interactive(): return _run_setup(...)`. |
| F4 | `_run_setup` prompts on standard input. | `agent_workflows/cli.py` `_run_setup`: `entry = input("  root> ").strip()  # KeyboardInterrupt/EOF handled in main()`. |
| F5 | The test redirects stdout and stderr, but leaves `sys.stdin` untouched. | `tests/test_term.py` `test_early_exit_paths_and_nested_invocations`: `with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf): cli.main(list(argv))`. |
| F6 | `cli.main()` handles `EOFError` with exit code 130 and executes its `finally` restoration block. | `agent_workflows/cli.py` `main()`: `except EOFError: print("\nCancelled (end of input).", ...); return 130` and `finally: ... _term_mod.set_interactive_override(_entry_interactive_override)`. |
| F7 | The recorded flake mechanism did not reproduce at review: the ambient stdin is `/dev/null`, so the prompt meets EOF and the test XPASSes. | Review probe: `stdin type: TextIOWrapper fd0: /dev/null`, `input raised EOFError` (serial and `-n 2`); unpatched `cli.main(["--interactive"])` -> `rc 130`, override `None`; current test `1 xpassed` in 3 of 3 runs at `-n 4`. `tests/__init__.py` Interactive-prompt guard. |
| F8 | With `mock.patch("sys.stdin", io.StringIO(""))`, bare `--interactive` returns 130 in 0.3s and restores outer `None`/`False`; bare `--no-interactive` returns 0 but takes about 5.5s. | Review probe: `None ['--interactive'] rc 130 after None`, `False ['--interactive'] rc 130 after False`, `True ['--no-interactive'] rc 0 after True`; timings `['--interactive'] 0.3`, `['--no-interactive'] 5.46`, `5.62`. |

## Proposed changes (ordered, validatable)

1. E-01: Patch `sys.stdin` to `io.StringIO("")` around every `cli.main` call in `test_early_exit_paths_and_nested_invocations`, remove the quarantine `xfail` decorator and the unused `import pytest`. Validated by V-01.
2. E-02: Assert bare `--interactive` returns 130 at EOF and restores the override from a flagless baseline and from outer `False` and `True`. Validated by V-02.
3. E-03: Run the targeted class (once plus five concurrent repeats), the full `tests/test_term.py` module, and the bare `python3 -m pytest` core gate. Validated by V-03.

## Deferred / out of scope (with reason)

- Modifying `cli.py` smart-default dispatch logic or `_run_setup`: when an operator explicitly passes `--interactive` with no verb in an unconfigured environment, interactive setup is intended behavior (decision D7); the issue is solely test isolation of `sys.stdin`.
  - Carrier-Declined: production behavior is intentional; issue is test environment stdin isolation.
- Auditing other CLI tests for unredirected stdin: outside the scope of backlog item `aenl8o`; separate backlog items exist for other quarantined tests (e.g. `q2cgcu`).
  - Carrier-Declined: other tests tracked in separate backlog items.
- Bare `--no-interactive` (no verb) coverage: it never reads stdin, so it does not exercise this concern, and it costs about 5.5s per call (F8).
  - Carrier-Declined: not part of the stdin-isolation concern; covered in spirit by the existing `--no-interactive` early-exit cases.

## Scope check

- Over-scope: none (bare `--no-interactive` cases removed at review, PR-004).
- Under-scope: none; the test owns its stdin, its bare `--interactive` outcome is asserted, and the quarantine is removed. If the flake recurs after un-quarantine (F7: cause unknown), it turns red visibly; file it as a new backlog item rather than re-adding `xfail`.

## Required tests / validation

- `python3 -m pytest -o addopts="" -rA -p no:cacheprovider tests/test_term.py -k CliNeverLeaksTheInteractivityOverrideTests` reports every test PASSED (zero failures, zero xfailed, zero xpassed).
- Five repeated `python3 -m pytest -o addopts="" -n 6 -rxX tests/test_term.py -k CliNeverLeaksTheInteractivityOverrideTests` runs each report all passed with no xfail/xpass lines.
- `python3 -m pytest -o addopts="" -n 6 tests/test_term.py` reports no failures.
- Bare `python3 -m pytest` exits 0 (suite no-regression gate; it does not collect `tests/test_term.py`).

## Spec / documentation sync

N/A: test isolation fix and quarantine removal; no user-facing documentation or specification contracts changed.

## Open questions

None. The fix mechanism is demonstrated (F8 probe), and the flake's original cause is recorded as unknown (F7) with an explicit recurrence path in the Scope check. No maintainer decision is required.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: `git diff -- tests/test_term.py` showing `mock.patch("sys.stdin", io.StringIO(""))` wrapping every `cli.main` call in `test_early_exit_paths_and_nested_invocations`, the removal of `@pytest.mark.xfail(...)`, and (if no other use remains) the removal of `import pytest`; plus pasted `ruff check tests/test_term.py` output showing no findings.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git diff -- tests/test_term.py` showing assertions that bare `cli.main(["--interactive"])` returns 130 under empty stdin and that the override equals `None`, `False`, and `True` respectively after the flagless and the two outer-override invocations; plus pasted pytest output showing the test(s) in `CliNeverLeaksTheInteractivityOverrideTests` PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted runner output for: (1) the `-rA` targeted run showing every class test PASSED with no XFAIL/XPASS; (2) all five `-n 6 -rxX` repeated runs, each ending in `N passed` with no xfailed/xpassed; (3) the full `tests/test_term.py` module run with no failures; (4) bare `python3 -m pytest` ending in exit 0.
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
