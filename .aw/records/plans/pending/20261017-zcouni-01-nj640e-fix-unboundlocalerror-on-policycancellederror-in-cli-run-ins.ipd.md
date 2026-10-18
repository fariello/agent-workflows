# IPD: Fix UnboundLocalError on PolicyCancelledError in cli._run_install when kept_legacy is True

- Date: 2026-10-17
- Kind: child
- Concern: In `agent_workflows.cli._run_install`, `PolicyCancelledError` is imported lazily inside `if not kept_legacy:` (along with other wizard policy types). When installing into a legacy repository and migration is declined (or `--keep-legacy` is specified), `kept_legacy` is `True` and the `if not kept_legacy:` branch is bypassed. When execution reaches the final confirmation gate (`_confirm_install`), a user cancellation (e.g. `KeyboardInterrupt`, which `_confirm_install` translates into `PolicyCancelledError`) triggers the enclosing `except PolicyCancelledError:` handler in `_run_install`. Because `PolicyCancelledError` was only bound inside the skipped `if not kept_legacy:` block, Python treats `PolicyCancelledError` as an unassigned local variable and raises `UnboundLocalError: cannot access local variable 'PolicyCancelledError' where it is not associated with a value`. The same masking happens for ANY exception that propagates out of that `try` (Python evaluates the `except` expression to match it): measured at review, an `OSError` from `input()` on pytest's captured-stdin object surfaced as `UnboundLocalError` with the `OSError` only as `__context__`. `Order15CliTests.test_install_legacy_repo_interactive_decline_keeps_legacy` was quarantined in commit `f762cafce` under `@pytest.mark.xfail(strict=False, reason="flaky: zcouni - UnboundLocalError on PolicyCancelledError")`. Measured at review (lane HEAD `08fa69666`): in a normal pytest worker the ambient stdin is the `/dev/null` stream installed by the `tests/__init__.py` interactive-prompt guard, so `input()` raises `EOFError`, `_confirm_install` returns its default, and the test currently XPASSes (3 of 3 runs at `-n 4`, `3 passed, 2 xpassed`). The exact flake trigger is therefore NOT reproduced (cause unknown); the defect is the unbound handler name, which turns any cancellation or stdin error on the legacy path into a crash, plus the test's dependence on an ambient stdin it does not own.
- Scope: In `agent_workflows/cli.py`, import `PolicyCancelledError` unconditionally in `cli._run_install` (at function entry before the repository iteration loop) so the `except PolicyCancelledError:` exception handler is always bound regardless of whether `kept_legacy` is True or False. In `tests/test_cli.py`, remove the `@pytest.mark.xfail` quarantine decorator from `Order15CliTests.test_install_legacy_repo_interactive_decline_keeps_legacy` and provide mocked interactive input (`io.StringIO("\n")`) so it runs cleanly without reading captured stdin. Add a dedicated test verifying that when `kept_legacy` is True and the user presses CTRL-C at the final install confirmation (which the real `_confirm_install` translates into `PolicyCancelledError`), `_run_install` reports `install cancelled; nothing written.`, writes nothing, and exits 1 without raising `UnboundLocalError`.
- Scope-Paths: agent_workflows/cli.py, tests/test_cli.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: zcouni
- Blocks-Release: next
- Set: zcouni
- Order: 1
- Highest E allocated: 04
- Author: antigravity
- Id: nj640e
- Approval: 2026-10-18, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-18 approved (aw set): status set to approved
- 2026-10-18 reviewed (plan-review opencode model=its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006

- 2026-10-17 to-review (antigravity): authored from backlog zcouni with findings, checklist, and validation.
- 2026-10-17 draft (antigravity): created.

## Goal

Ensure `cli._run_install` unconditionally binds `PolicyCancelledError` so that cancellation during legacy-mode installation handling catches cleanly rather than crashing with `UnboundLocalError`, unquarantine `Order15CliTests.test_install_legacy_repo_interactive_decline_keeps_legacy`, and add regression coverage for legacy install cancellation.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Unconditional import in _run_install

- [ ] E-01 In `agent_workflows/cli.py` within `_run_install`, add `from agent_workflows.install_wizard import PolicyCancelledError` as the first statement of the function body (before the `targets = ...` line, so before the repository iteration loop and before `_handle_legacy_migration`), and REMOVE `PolicyCancelledError,` from the inner `from agent_workflows.install_wizard import (...)` list inside `if not kept_legacy:` so the name has exactly one binding. Leave both `except PolicyCancelledError:` handlers (the policy-wizard one and the final-confirmation one) unchanged.
  - Depends on: none
  - Expected outcome: `PolicyCancelledError` is bound on every path through `_run_install`. A cancellation at the final confirmation on the legacy path reports `install cancelled; nothing written.` and returns 1; any OTHER exception from that `try` now propagates as itself instead of as `UnboundLocalError` (demonstrated at review on a scratch copy: KeyboardInterrupt case `EXIT 1` with the cancelled line and no `.agents/workflows/index.md` written; OSError case raises `OSError`; a non-legacy cancellation still exits 1 with the cancelled line).
  - Execution state: pending

### Task group 2: Test unquarantine and regression coverage

- [ ] E-02 In `tests/test_cli.py`, remove the `@pytest.mark.xfail(strict=False, reason="flaky: zcouni - UnboundLocalError on PolicyCancelledError")` decorator from `Order15CliTests.test_install_legacy_repo_interactive_decline_keeps_legacy`, and replace `with mock.patch("sys.stdin.isatty", return_value=True):` with `with mock.patch("sys.stdin", io.StringIO("\n")):` (module-level `io` and `mock` are already imported) so the one remaining prompt (`_confirm_install`'s "Proceed and install into ...? [Y/n]") reads the in-memory newline instead of an ambient stream. Add `self.assertEqual(code, 0, out)` after the `_run` call and `self.assertFalse((repo / ".aw" / "system").exists())` beside the existing assertions, keeping the existing `mock_ask` and VERSION assertions. Do NOT touch the sibling `test_install_legacy_repo_interactive_accept_migrates_to_aw` (owned by plan `s56tsu`).
  - Depends on: E-01
  - Expected outcome: the test owns its stdin and asserts its outcome: exit 0, the deprecation warning printed, `.agents/workflows/VERSION` kept, no `.aw/system` created (demonstrated at review on the same inputs: `EXIT 0`, deprecation line present, VERSION kept, `.aw/system` absent); the quarantine decorator is gone.
  - Execution state: pending
- [ ] E-03 In `tests/test_cli.py` within `Order15CliTests`, add `test_install_legacy_repo_interactive_decline_cancellation_handles_policy_cancelled_error`. Build the same legacy fixture as E-02 (`.agents/workflows/VERSION`), then run `_run(["install", str(repo)])` under `mock.patch("agent_workflows.cli._ask_policy", return_value=False)` (so `kept_legacy` is True), `mock.patch("sys.stdin", io.StringIO(""))`, and `mock.patch("builtins.input", side_effect=KeyboardInterrupt)`. This drives the REAL `_confirm_install`, whose `except KeyboardInterrupt:` raises `PolicyCancelledError`; it follows the existing precedent `InstallAtomicWizardTests.test_install_ctrl_c_preset_prompt_writes_zero_files_and_skips_cleanly`. Assert: the call returns normally (an `UnboundLocalError` would propagate out of `_run` and fail the test), `code == 1`, `"install cancelled; nothing written."` is in the output, `"FAIL"` is not, `.agents/workflows/VERSION` still exists, and `.agents/workflows/index.md` was NOT written (nothing installed).
  - Depends on: E-01
  - Expected outcome: the test passes after E-01 and FAILS with `UnboundLocalError` against the pre-change `cli.py` (demonstrated at review: pre-change `RAISED UnboundLocalError: cannot access local variable 'PolicyCancelledError' ...`; post-change `EXIT 1`, cancelled line present, `index.md` absent).
  - Execution state: pending
- [ ] E-04 Run the regression set. `tests/test_cli.py` carries module-level `pytestmark = pytest.mark.slow`, so every targeted run needs `-m "slow or not slow"` and the bare core gate never collects these tests (it is a no-regression gate only). Run: (a) `python3 -m pytest -o addopts="" -rA -m "slow or not slow" tests/test_cli.py -k "Order15CliTests or InstallAtomicWizardTests"`; (b) three repeated concurrent runs `for i in 1 2 3; do python3 -m pytest -o addopts="" -n 4 -rxX -m "slow or not slow" tests/test_cli.py -k Order15CliTests; done`; (c) the bare core gate `python3 -m pytest`.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: (a) zero failures, and the two zcouni tests report PASSED (not XPASS/XFAIL); (b) every run reports zero failures, with at most the one `s56tsu`-owned test still XPASS if that plan has not landed; (c) zero failures.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Tests in `tests/test_installer.py` and `tests/test_migrate_layout_cli.py` mock `sys.stdin` with `io.StringIO(...)` to feed canned responses to interactive CLI commands without relying on captured stdin.
- The interactive CLI helpers in `agent_workflows/cli.py` (`_ask_policy`, `_confirm_install`, `_install_leftover_disposition`) and `agent_workflows/install_wizard.py` (`collect_policy_interactive`) explicitly inspect `isinstance(sys.stdin, io.StringIO)` alongside TTY checks to detect interactive test streams.
- `agent_workflows/cli.py` defers imports into function bodies to maintain fast CLI startup times; importing `PolicyCancelledError` at `cli._run_install` function entry maintains this lazy-loading pattern while guaranteeing scope availability for the entire install routine.
- Tests must exercise observable outcomes and side effects rather than pinning code structure (AGENTS.md rule "TEST OUTCOMES, NOT CODE STRUCTURE").
- `tests/test_cli.py` has module-level `pytestmark = pytest.mark.slow`, and `addopts` deselects `slow`, so every targeted run needs `-m "slow or not slow"`. `tests/slow_allowlist.txt` separately lists `Order15CliTests::test_install_legacy_repo_interactive_decline_keeps_legacy` as a known long-duration test; it is a duration report, not a selector. If the conftest duration report names the new E-03 test as unlisted, add it to `tests/slow_allowlist.txt` and justify that out-of-scope path at finalize.
- Cancellation-test precedent: `tests/test_cli.py` `InstallAtomicWizardTests.test_install_ctrl_c_preset_prompt_writes_zero_files_and_skips_cleanly` patches `sys.stdin` to `io.StringIO("")` and `builtins.input` to raise `KeyboardInterrupt`, then asserts `install cancelled; nothing written.`, no `FAIL`, and zero files written.
- `tests/__init__.py` reopens the process stdin on `/dev/null` ("Interactive-prompt guard"), so an unmocked `input()` in a test raises `EOFError` rather than blocking.

## Findings

| Finding | Severity | Description | Evidence |
|---|---|---|---|
| F-01 | High | `agent_workflows.cli._run_install` imports `PolicyCancelledError` inside `if not kept_legacy:`. When `kept_legacy` is True, that block is skipped. Later in `_run_install`, the final confirmation gate is wrapped in `try: ... except PolicyCancelledError:`. Because Python assigns local scope to `PolicyCancelledError` at compile time, the skipped branch leaves the variable unassigned, causing `UnboundLocalError` when any exception propagating out of that `try` makes Python evaluate the `except` clause. Reproduced at review: CTRL-C at the confirmation on a declined legacy repo raised `UnboundLocalError: cannot access local variable 'PolicyCancelledError' where it is not associated with a value`. | `agent_workflows/cli.py` `_run_install` `if not kept_legacy:` ... `from agent_workflows.install_wizard import (` ... `PolicyCancelledError,`; final gate `confirmed = _confirm_install(` ... `except PolicyCancelledError:` |
| F-02 | Medium | `Order15CliTests.test_install_legacy_repo_interactive_decline_keeps_legacy` patched `sys.stdin.isatty` to return True without providing an input stream, so `_confirm_install` calls `input()` on whatever ambient stdin the process has. Quarantined in commit `f762cafce` with `@pytest.mark.xfail(strict=False, ...)`. It currently XPASSes because the ambient stdin is the `/dev/null` guard (EOF -> default). Exact flake trigger not reproduced (cause unknown). | `tests/test_cli.py` `Order15CliTests.test_install_legacy_repo_interactive_decline_keeps_legacy` `mock.patch("sys.stdin.isatty", return_value=True)`; `tests/__init__.py` "Interactive-prompt guard" `sys.stdin = open(os.devnull, "r")`; review run `3 passed, 2 xpassed` x3 at `-n 4` |
| F-03 | Low | There was no dedicated regression test verifying that cancelling during the install confirmation of a legacy repository (`kept_legacy` is True) gracefully catches `PolicyCancelledError` and terminates with a skip status instead of crashing. | `tests/test_cli.py` `InstallAtomicWizardTests.test_install_ctrl_c_preset_prompt_writes_zero_files_and_skips_cleanly` covers only the non-legacy path |
| F-04 | Medium | The unbound name also MASKS unrelated errors: any non-`PolicyCancelledError` exception raised inside the final-gate `try` on the legacy path is reported as `UnboundLocalError`. Reproduced at review with pytest's captured-stdin object: `UnboundLocalError` whose `__context__` was `OSError: pytest: reading from stdin while output is captured!`. After the fix that `OSError` propagates as itself. | scratch reproduction at lane HEAD `08fa69666` |

## Proposed changes (ordered, validatable)

1. E-01: In `agent_workflows/cli.py`, add `from agent_workflows.install_wizard import PolicyCancelledError` at `_run_install` function entry and drop it from the inner import list.
2. E-02: In `tests/test_cli.py`, unquarantine `test_install_legacy_repo_interactive_decline_keeps_legacy` by removing `@pytest.mark.xfail`, mocking `sys.stdin` with `io.StringIO("\n")`, and asserting exit 0 and no `.aw/system`.
3. E-03: In `tests/test_cli.py`, add `test_install_legacy_repo_interactive_decline_cancellation_handles_policy_cancelled_error`, driving the real `_confirm_install` with a `KeyboardInterrupt` from `input()`.
4. E-04: run the Order15 and install-wizard classes, repeated concurrent runs, and the bare core gate.

## Deferred / out of scope (with reason)

- Sister test `tests/test_cli.py::Order15CliTests::test_install_legacy_repo_interactive_accept_migrates_to_aw`: quarantined under backlog item `q2cgcu` and addressed in plan `s56tsu`.
  - Carrier: s56tsu

## Scope check

- Over-scope: none. Changes are restricted solely to `agent_workflows/cli.py` and `tests/test_cli.py`.
- Under-scope: none. Directly resolves the `UnboundLocalError` root cause, unquarantines the affected test, and adds regression coverage. Verified at review that `PolicyCancelledError` is referenced nowhere else in `agent_workflows/` outside `install_wizard.py` except `cli._confirm_install` and `cli._confirm_relocation` (each imports it locally right before raising) and the two handlers in `_run_install`, and that `_install_all` and the setup path call `_handle_legacy_migration` without a `PolicyCancelledError` handler, so no sibling site has the same unbound-name defect. If the flake recurs after un-quarantine (cause unknown, see Concern), it turns red visibly; file a new backlog item rather than re-adding `xfail`.

Invariants and the test that pins each:
- I-1 A cancellation at the final install confirmation on the legacy path exits 1 with `install cancelled; nothing written.` and writes nothing: E-03.
- I-2 Declining migration still installs in compatibility mode (exit 0, legacy tree kept, no `.aw/system`): E-02.
- I-3 Cancellation on the non-legacy path is unchanged: `InstallAtomicWizardTests` in E-04 (a).

## Required tests / validation

- `python3 -m pytest -o addopts="" -rA -m "slow or not slow" tests/test_cli.py -k test_install_legacy_repo_interactive_decline_keeps_legacy` reports `PASSED` (not XPASS or XFAIL) (V-02).
- `python3 -m pytest -o addopts="" -rA -m "slow or not slow" tests/test_cli.py -k test_install_legacy_repo_interactive_decline_cancellation_handles_policy_cancelled_error` reports `PASSED`, and the same command against the pre-change `cli.py` FAILS with `UnboundLocalError` (V-03).
- E-04 (a), (b), (c) report zero failures (V-04).

## Spec / documentation sync

N/A: no specification or documentation changes are required. The documented behavior (CTRL-C at an install prompt reports `install cancelled; nothing written.` and writes nothing, as `cli.main`'s D-CLI-UX docstring and `InstallAtomicWizardTests` describe) is unchanged; this fix makes the legacy path honor it instead of crashing.

## Open questions

### OQ-01: Should PolicyCancelledError be imported at module scope or within cli._run_install?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Importing at the top of `cli._run_install` preserves the lazy-import convention established throughout `agent_workflows/cli.py` (for example `_confirm_install` and `_confirm_relocation` each import `PolicyCancelledError` locally) to maintain quick CLI startup, while unconditionally ensuring the symbol is in scope throughout `_run_install` before any branching on `kept_legacy`. Demonstrated at review on a scratch copy of `_run_install` with exactly this edit (see E-01 Expected outcome).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff agent_workflows/cli.py` showing `from agent_workflows.install_wizard import PolicyCancelledError` as the first statement of `cli._run_install` and `PolicyCancelledError,` removed from the inner import list, with both `except PolicyCancelledError:` handlers unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `git diff tests/test_cli.py` showing removal of the zcouni `@pytest.mark.xfail` from `test_install_legacy_repo_interactive_decline_keeps_legacy`, the `mock.patch("sys.stdin", io.StringIO("\n"))` replacement, and the added exit-code and `.aw/system` assertions; and paste the output of `python3 -m pytest -o addopts="" -rA -m "slow or not slow" tests/test_cli.py -k test_install_legacy_repo_interactive_decline_keeps_legacy` showing the test `PASSED` (not XPASS).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `git diff tests/test_cli.py` showing the new `test_install_legacy_repo_interactive_decline_cancellation_handles_policy_cancelled_error`; paste the output of `python3 -m pytest -o addopts="" -rA -m "slow or not slow" tests/test_cli.py -k test_install_legacy_repo_interactive_decline_cancellation_handles_policy_cancelled_error` showing `PASSED`; AND paste the same command's output with ONLY `agent_workflows/cli.py` reverted to the pre-change version (e.g. `git stash push -- agent_workflows/cli.py`, run, `git stash pop`) showing the test FAILING with `UnboundLocalError`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the summary line of E-04 (a), the summary line of each of the three E-04 (b) runs, and the summary line of the bare `python3 -m pytest` run (c), each showing zero failures and errors.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Commit only files you changed, through `aw commit nj640e -- agent_workflows/cli.py tests/test_cli.py`; never `git add -A`, never push. You MUST paste the ACTUAL runner output into each `V-*`; never claim a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Lifecycle: after every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize` itself.
