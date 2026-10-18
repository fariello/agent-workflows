# IPD: Feed interactive stdin in Order15CliTests legacy migration accept test

- Date: 2026-10-17
- Kind: child
- Concern: `Order15CliTests.test_install_legacy_repo_interactive_accept_migrates_to_aw` in `tests/test_cli.py` mocks `sys.stdin.isatty` to return `True` while leaving `sys.stdin` itself as the ambient process stream. Because `_run_install` continues through `collect_policy_interactive` and `_confirm_install` after migration (and the forced TTY also makes `term.is_interactive()` True, so `engine`'s "Would you like the installer to commit these changes?" prompt is reached too), three `input()` calls read from a stream the test does not own. The test was quarantined in commit `f762cafce` with `@pytest.mark.xfail(strict=False, reason="flaky: q2cgcu - prompts on captured stdin under xdist")`. Measured at review (2026-10-18, lane HEAD `9764d3c1c`): the ambient stdin in a pytest worker is `/dev/null` (`tests/__init__.py` Interactive-prompt guard), so each `input()` raises `EOFError`, every helper takes its default, and the test currently XPASSes (5 of 5 runs at `-n 4`). The exact flake mechanism is therefore NOT reproduced (cause unknown); the defect this plan removes is the test's dependence on an ambient stdin it does not control.
- Scope: Update `Order15CliTests.test_install_legacy_repo_interactive_accept_migrates_to_aw` in `tests/test_cli.py` to mock `sys.stdin` with `io.StringIO("\n\n")` (supplying interactive answers to subsequent prompts without reading from captured stdin) instead of patching `sys.stdin.isatty` directly, assert the install's observable outcome (exit code 0 and the legacy `.agents/workflows` tree removed), and remove the `@pytest.mark.xfail` quarantine decorator so the test executes and passes cleanly under pytest-xdist. OUT: the sibling `test_install_legacy_repo_interactive_decline_keeps_legacy` (backlog `zcouni`) and any production change.
- Scope-Paths: tests/test_cli.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: q2cgcu
- Set: q2cgcu
- Order: 1
- Highest E allocated: 02
- Author: antigravity
- Id: s56tsu
- Approval: 2026-10-18, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-18 approved (aw set): status set to approved
- 2026-10-18 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004

- 2026-10-17 to-review (antigravity): authored from backlog q2cgcu with findings, checklist, and validation.
- 2026-10-17 draft (antigravity): created.

## Goal

Restore clean, unquarantined execution for `Order15CliTests.test_install_legacy_repo_interactive_accept_migrates_to_aw` under `pytest-xdist` by feeding `io.StringIO` to `sys.stdin` during interactive installation testing, eliminating captured-stdin prompts and removing the `@pytest.mark.xfail` quarantine decorator.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Test update and unquarantine

- [ ] E-01 In `tests/test_cli.py` within `Order15CliTests.test_install_legacy_repo_interactive_accept_migrates_to_aw`, remove the `@pytest.mark.xfail(strict=False, reason="flaky: q2cgcu - prompts on captured stdin under xdist")` decorator and replace `with mock.patch("sys.stdin.isatty", return_value=True):` with `with mock.patch("sys.stdin", io.StringIO("\n\n")):` so that all interactive prompts in `_run(["install", str(repo)])` (`collect_policy_interactive` and `_confirm_install`) receive predetermined newline answers from the in-memory string stream without prompting on captured stdin. No new imports are needed (`io` and `mock` are already imported at module top, lines 14 and 22; the local `from unittest import mock` may stay or go). Also add `self.assertEqual(code, 0, out)` after the `_run` call and `self.assertFalse((repo / ".agents" / "workflows").exists())` beside the existing `.aw/system` assertions, keeping the existing `mock_ask` and `.aw/system` assertions unchanged.
  - Depends on: none
  - Expected outcome: the test owns its stdin (the StringIO path makes `_ask_policy`/`collect_policy_interactive`/`_confirm_install` treat the run as attended via their `isinstance(sys.stdin, io.StringIO)` checks, while `term.is_interactive()` stays False so the engine commit prompt is not reached); the install exits 0, `.aw/system/workflows/index.md` and `.aw/system/VERSION` exist, `.agents/workflows` is gone; the quarantine decorator is removed.
  - Execution state: pending
- [ ] E-02 Run: (a) `python3 -m pytest -o addopts="" -rA -m "slow or not slow" tests/test_cli.py -k test_install_legacy_repo_interactive_accept_migrates_to_aw`; (b) five repeated concurrent runs `for i in 1 2 3 4 5; do python3 -m pytest -o addopts="" -n 4 -rxX -m "slow or not slow" tests/test_cli.py -k Order15CliTests; done` (pytest-randomly stays enabled, so seeds vary); (c) the routine gate bare `python3 -m pytest`. Note: `tests/test_cli.py` carries module-level `pytestmark = pytest.mark.slow` (line 29), so (c) never collects this test and is a no-regression gate only; (a) and (b) are the evidence.
  - Depends on: E-01
  - Expected outcome: the target test reports PASSED (never XPASS/XFAIL) in (a) and in every (b) run, no (b) run reports a failure or hang (the sibling `zcouni` test may still report XPASS/XFAIL; it is out of scope), and (c) exits 0.
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
| F-03 | Medium | Review probe (spy on `builtins.input`, `_ask_policy` mocked True): with the current `isatty` mock, three prompts fire (`Keep current policy and proceed? [Y/n/review]`, `Proceed and install into ...? [Y/n]`, `Would you like the installer to commit these changes? [Y/n]`), all reading ambient `/dev/null` and hitting EOF. With `mock.patch("sys.stdin", io.StringIO("\n\n"))` exactly the first two fire and consume the two newlines; code 0, `.aw/system/workflows/index.md` and `.aw/system/VERSION` exist, `.agents/workflows` is gone. The engine commit prompt is skipped because `engine.is_interactive_session` delegates to `term.is_interactive()`, which is False for a non-TTY StringIO stdin. Current test XPASSes 5/5 at `-n 4`. |
| F-04 | Low | The current test discards `code` from `_run(...)` and never asserts the legacy tree was removed, so a failing install that still left `.aw/system` files would pass. `tests/test_cli.py` `test_install_legacy_repo_interactive_accept_migrates_to_aw`. |
| F-02 | Low | In commit `f762cafceda161e1364b6605fc0f7a166bf4b261`, the test was quarantined with `@pytest.mark.xfail(strict=False, reason="flaky: q2cgcu - prompts on captured stdin under xdist")` to allow the testprune suite to pass. Replacing the `sys.stdin.isatty` mock with `mock.patch("sys.stdin", io.StringIO("\n\n"))` eliminates the root cause and allows unquarantining the test. |

## Proposed changes (ordered, validatable)

1. E-01: Remove `@pytest.mark.xfail` and update `test_install_legacy_repo_interactive_accept_migrates_to_aw` in `tests/test_cli.py` to mock `sys.stdin` with `io.StringIO("\n\n")`.
   It also asserts exit code 0 and removal of `.agents/workflows`.
2. E-02: Run the target test once with `-rA`, the class five times under `-n 4 -rxX`, and the bare routine gate as no-regression.

## Deferred / out of scope (with reason)

- Sister test `tests/test_cli.py::Order15CliTests::test_install_legacy_repo_interactive_decline_keeps_legacy`: quarantined under open backlog item `zcouni` due to `UnboundLocalError on PolicyCancelledError in cli._run_install when kept_legacy is True`.
  - Carrier-Declined: tracked under separate open backlog item zcouni with its own bug fix scope

## Scope check

- Over-scope: none. Changes are restricted solely to `tests/test_cli.py`.
- Under-scope: none. The test now owns its stdin and asserts its outcome. If the flake recurs after un-quarantine (cause unknown, see Concern), it turns red visibly; file a new backlog item rather than re-adding `xfail`.

## Required tests / validation

- `python3 -m pytest -o addopts="" -rA -m "slow or not slow" tests/test_cli.py -k test_install_legacy_repo_interactive_accept_migrates_to_aw` shows the test PASSED (not XPASS).
- Five `python3 -m pytest -o addopts="" -n 4 -rxX -m "slow or not slow" tests/test_cli.py -k Order15CliTests` runs each show no failure and no XPASS/XFAIL line for the target test.
- Bare `python3 -m pytest` exits 0 (no-regression only; it does not collect `tests/test_cli.py`).

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
  - Required evidence: paste `git diff tests/test_cli.py` showing removal of the `@pytest.mark.xfail` quarantine decorator, replacement of `mock.patch("sys.stdin.isatty", return_value=True)` with `mock.patch("sys.stdin", io.StringIO("\n\n"))`, and the added `assertEqual(code, 0, out)` and `.agents/workflows` absence assertions; plus pasted `ruff check tests/test_cli.py` output with no findings.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the actual output of (a) the `-rA` target run showing `PASSED tests/test_cli.py::Order15CliTests::test_install_legacy_repo_interactive_accept_migrates_to_aw` and no XPASS; (b) all five `-n 4 -rxX` class runs, each summary showing zero failed and no XPASS/XFAIL line naming the target test; (c) the bare `python3 -m pytest` summary with exit 0.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Tests assert observable behavior (exit codes, files written), never source text or structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"). Commit only files you changed, through `aw commit s56tsu -- tests/test_cli.py`, and verify `git diff --cached --name-only` lists only your paths; never `git add -A`, never push. You MUST paste the ACTUAL runner output into each `V-*`; never claim a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Lifecycle: after every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize` itself.
