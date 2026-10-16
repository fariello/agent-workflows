# IPD: Restore behavioral coverage of oc_runipd.main interrupt stderr preservation notice

- Date: 2026-10-14
- Kind: child
- Concern: The `KeyboardInterrupt` handler in `agent_workflows.oc_runipd.main` prints the operator-facing exit notice ("Interrupted; durable run state was preserved.", the SIGTERM variant, and the no-cleanup variant) and returns 130/143, but no live test exercises it since `tests/test_interrupt_menu.py` was deleted in `19313eed`.
- Scope: Add one new behavioral test module that drives the real `oc_runipd.main` into its `KeyboardInterrupt` handler and asserts on captured stderr and the exit code; repoint the now-stale "no live guard currently asserts this" comment in `oc_runipd.main` at the new test.
- Scope-Paths: tests/test_oc_runipd_main_interrupt.py, agent_workflows/oc_runipd.py, .aw/records/plans/pending/20261014-zgqs4e-01-5ne0fo-restore-behavioral-coverage-of-oc-runipd-main-interrupt-stde.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: zgqs4e
- Set: zgqs4e
- Order: 1
- Highest E allocated: 02
- Author: opencode
- Id: 5ne0fo

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 5ne0fo verified (set zgqs4e, attempt 1).
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 fixed (review record 20261014-zgqs4e-01-5ne0fo)
- 2026-10-15 draft (opencode): created.
- 2026-10-15 to-review (opencode): authored from backlog `zgqs4e`; prototype of the test approach run against the current tree.

## Goal

Restore behavioral coverage, lost when `tests/test_interrupt_menu.py::RunnerMainOutputOnInterruptTests` was deleted in commit `19313eed`, of the stderr notice and exit code that `oc_runipd.main` produces when the run is interrupted (SIGINT), terminated (SIGTERM), or terminated without cleanup. Plan `9rthek` classified this site S-07 as RETIRE-UNGUARDED; this plan re-guards it with an outcome test only (P16).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Behavioral test of the interrupt exit notice

- [x] E-01 Create `tests/test_oc_runipd_main_interrupt.py` with a `unittest.TestCase` that calls the real `oc_runipd.main(["resume", "run-fake"])` with `run_queue` patched to raise `KeyboardInterrupt(<msg>)` (and `emit_shutdown_report`, `resolve_run_dir`, `load_state`, `locked_run`, `install_stop_triggers` patched exactly as the deleted test did, `resolve_run_dir` returning a nonexistent temp path so the summary-table branch is skipped), capturing `sys.stderr` AND `sys.stdout` (so nothing leaks into pytest output), with the temp path created via `tempfile.TemporaryDirectory()` cleaned up per test. Use `subTest` or three test methods. Three cases: (a) `"clean-up-and-terminate"` asserts exit 130 and stderr contains `"Interrupted; durable run state was preserved."`; (b) `"Terminated by SIGTERM"` asserts exit 143 and stderr contains `"Terminated by SIGTERM; durable run state was preserved."`; (c) `"just-terminate-no-cleanup"` asserts exit 130, stderr contains `"Terminated without clean up; worktree and lanes left in place."` and does NOT contain `"durable run state was preserved"`. Each case also asserts `emit_shutdown_report` was called once with `to_stderr=True`. Assert the notice by `assertIn` on the full sentence only; do NOT pin the following `runner_stop.stop_interrupt_hint` line or the full stderr bytes (that line is owned by `wqq8ua` and would make this test brittle to an unrelated wording change). No `inspect`/`ast`/source reading.
  - Depends on: none
  - Expected outcome: the new module exists, contains only calls into `oc_runipd.main` and assertions on its return value, captured stderr and mock calls, and its three cases pass.
  - Execution state: performed

### Task group 2: Repoint the stale comment

- [x] E-02 In `agent_workflows/oc_runipd.py` `main` (the `except KeyboardInterrupt as exc:` handler), edit only the comment block under "stopdisc (`wqq8ua`) E-03" that reads "which is what `tests/test_interrupt_menu.py::RunnerMainOutputOnInterruptTests` asserted (deleted in `19313eed`; no live guard currently asserts this)" so it names `tests/test_oc_runipd_main_interrupt.py` as the live guard. No executable line changes.
  - Depends on: E-01
  - Expected outcome: `git diff agent_workflows/oc_runipd.py` shows only comment lines changed; the S-07 comment inside the `except KeyboardInterrupt` handler no longer contains "no live guard currently asserts this" (other occurrences of that phrase elsewhere in the file, for unrelated sites, are untouched).
  - Execution state: performed

## Project conventions discovered (Step 0)

- P16 / AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE": restored coverage must call the code and assert real outputs, exit codes and side effects; never read source.
- Suite runs bare as `python3 -m pytest` (addopts supplies `-q -n auto`); narrowed runs use `-o addopts=""`.
- Deleted predecessor: `git show 19313eed^:tests/test_interrupt_menu.py`, class `RunnerMainOutputOnInterruptTests.test_main_messages_match`, which patched `run_queue`, `emit_shutdown_report`, `resolve_run_dir`, `load_state`, `locked_run`, `install_stop_triggers` and `sys.stderr`, then called `module.main(["resume", "run-fake"])`.
- Handler under test: `agent_workflows.oc_runipd.main`, the `except KeyboardInterrupt as exc:` branch containing `"durable run state was preserved."` and `return 143 if is_sigterm else 130`.
- Site classification: executed plan `9rthek` (`.aw/records/plans/executed/20261011-iosmvn-02-9rthek-retire-or-repoint-the-dangling-test-citations-in-the-host-dr.ipd.md`), row S-07 RETIRE-UNGUARDED.
- Commits go through `aw commit <plan> -- <paths>`.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | No live test asserts the preservation notice. | `rg -n "durable run state was preserved" tests/` returns nothing (also recorded in `9rthek` V-02 for S-07). |
| F-02 | The deleted test's mock set still drives the current `main` to the handler. | Re-run at review 2026-10-15 with a nonexistent temp `resolve_run_dir` path: all three cases reproduced the exit codes and sentences below, `emit_shutdown_report` was called exactly once with `to_stderr=True`, stdout stayed empty, and each stderr ended with the `stop_interrupt_hint` line. Author's prototype printed: `clean-up-and-terminate 130 'Interrupted; durable run state was preserved.\n...'`, `Terminated by SIGTERM 143 'Terminated by SIGTERM; durable run state was preserved.\n...'`, `just-terminate-no-cleanup 130 'Terminated without clean up; worktree and lanes left in place.\n...'`. |
| F-03 | The SIGTERM variant (exit 143) was never covered by the deleted test; adding it is within the same property. | Deleted test exercised only the two SIGINT messages. |
| F-04 | `agy_runipd.main` has the twin handler, but backlog `zgqs4e` names only `oc_runipd.main` (S-07). | Backlog body: "property: oc_runipd.main interrupt stderr preservation notice". |

## Proposed changes (ordered, validatable)

1. E-01: new test module `tests/test_oc_runipd_main_interrupt.py` (behavioral, three cases).
2. E-02: comment-only repoint in `agent_workflows/oc_runipd.py` `main`.

## Deferred / out of scope (with reason)

- The `agy_runipd.main` twin handler: not named by backlog `zgqs4e`; adding it would broaden scope.
  - Carrier-Declined: backlog `zgqs4e` scopes the property to `oc_runipd.main` (site S-07); no defect is known in the agy twin, which is a coverage question the maintainer can file separately if wanted.
- The `stop_interrupt_hint` sentence: already its own concern (`wqq8ua`); not asserted here beyond not breaking.
  - Carrier-Declined: owned by the executed `wqq8ua` work; asserting it here would couple this test to a different property.
- Any change to the handler's behavior: none intended.
  - Carrier-Declined: deliberate non-goal (coverage restoration only), not an outstanding obligation.

## Scope check

- Over-scope: none.
- Under-scope: none; the property is the stderr notice plus exit code, both covered by E-01.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_oc_runipd_main_interrupt.py` passes with 3 tests (V-01).
- Mutation check: temporarily change `"durable run state was preserved."` in `agent_workflows/oc_runipd.py` itself (a scratch copy would not be imported), confirm the test FAILS, then revert with `git checkout -- agent_workflows/oc_runipd.py` BEFORE E-02 edits that file (V-01).
- `aw ipd lint --phase pre-transition` conforms (the Deferred rows carry `Carrier-Declined`).
- Full suite `python3 -m pytest` passes (V-02).

## Spec / documentation sync

N/A: no spec governs this test or the comment; no behavior or user-facing documentation changes.

## Open questions

### OQ-01: Should the `agy_runipd.main` twin also be covered?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. Backlog `zgqs4e` scopes the property to `oc_runipd.main` (S-07); the agy twin is out of scope (see Deferred).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" -q tests/test_oc_runipd_main_interrupt.py` showing `3 passed`; pasted output of `rg -n "inspect|import ast|read_text|getsource" tests/test_oc_runipd_main_interrupt.py` showing no source-reading use; pasted failing output of the same pytest run after temporarily altering `"durable run state was preserved."` in `agent_workflows/oc_runipd.py` (then an empty `git diff --stat agent_workflows/oc_runipd.py`, run BEFORE E-02, showing the mutation reverted).
  - Observed evidence:
    `python3 -m pytest -o addopts="" -q tests/test_oc_runipd_main_interrupt.py`:
    ```
    ...                                                                      [100%]
    3 passed in 0.34s
    ```
    `rg -n "inspect|import ast|read_text|getsource" tests/test_oc_runipd_main_interrupt.py`:
    Exited with returncode 1 (no occurrences found).
    Failing pytest output under temporary mutation of `"durable run state was preserved."` to `"MUTATED durable run state was preserved."`:
    ```
    .FF                                                                      [100%]
    =================================== FAILURES ===================================
    _ OcRunipdMainInterruptTests.test_clean_up_and_terminate_notice_and_exit_code __

    self = <tests.test_oc_runipd_main_interrupt.OcRunipdMainInterruptTests testMethod=test_clean_up_and_terminate_notice_and_exit_code>

        def test_clean_up_and_terminate_notice_and_exit_code(self):
            """Interrupted run with clean-up exits 130 and notices durable state preserved."""
            code, stderr, stdout, mock_emit = self._run_main_with_interrupt(
                "clean-up-and-terminate"
            )
            self.assertEqual(code, 130)
    >       self.assertIn("Interrupted; durable run state was preserved.", stderr)
    E       AssertionError: 'Interrupted; durable run state was preserved.' not found in 'Interrupted; MUTATED durable run state was preserved.\nNext time, `aw oc run stop <run-id> --after-call` requests a graceful stop from another terminal (see `aw oc run stop --help` for the levels).\n'

    tests/test_oc_runipd_main_interrupt.py:61: AssertionError
    __ OcRunipdMainInterruptTests.test_terminated_by_sigterm_notice_and_exit_code __

    self = <tests.test_oc_runipd_main_interrupt.OcRunipdMainInterruptTests testMethod=test_terminated_by_sigterm_notice_and_exit_code>

        def test_terminated_by_sigterm_notice_and_exit_code(self):
            """SIGTERM interrupt exits 143 and notices durable state preserved."""
            code, stderr, stdout, mock_emit = self._run_main_with_interrupt(
                "Terminated by SIGTERM"
            )
            self.assertEqual(code, 143)
    >       self.assertIn(
                "Terminated by SIGTERM; durable run state was preserved.", stderr
            )
    E       AssertionError: 'Terminated by SIGTERM; durable run state was preserved.' not found in 'Terminated by SIGTERM; MUTATED durable run state was preserved.\nNext time, `aw oc run stop <run-id> --after-call` requests a graceful stop from another terminal (see `aw oc run stop --help` for the levels).\n'

    tests/test_oc_runipd_main_interrupt.py:70: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_oc_runipd_main_interrupt.py::OcRunipdMainInterruptTests::test_clean_up_and_terminate_notice_and_exit_code
    FAILED tests/test_oc_runipd_main_interrupt.py::OcRunipdMainInterruptTests::test_terminated_by_sigterm_notice_and_exit_code
    2 failed, 1 passed in 1.47s
    ```
    `git diff --stat agent_workflows/oc_runipd.py` run before E-02:
    Exited 0 with empty output (mutation reverted clean).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `git diff agent_workflows/oc_runipd.py` showing only `#` comment lines changed and naming `tests/test_oc_runipd_main_interrupt.py`; pasted bare `python3 -m pytest` summary line showing no failures.
  - Observed evidence:
    `git diff agent_workflows/oc_runipd.py`:
    ```diff
    diff --git a/agent_workflows/oc_runipd.py b/agent_workflows/oc_runipd.py
    index 7f9bd5845..8a04a7d5f 100755
    --- a/agent_workflows/oc_runipd.py
    +++ b/agent_workflows/oc_runipd.py
    @@ -5737,8 +5737,7 @@ def main(argv: list[str] | None = None) -> int:
             #
             # AFTER THE BRANCH, NOT INSIDE EITHER, for two reasons. It is true on BOTH exits, and keeping
             # it out of the branch bodies leaves each existing sentence byte-identical and contiguous,
    -        # which is what `tests/test_interrupt_menu.py::RunnerMainOutputOnInterruptTests` asserted
    -        # (deleted in `19313eed`; no live guard currently asserts this).
    +        # which is what `tests/test_oc_runipd_main_interrupt.py` asserts.
             #
             # PHRASED AS WHAT IS AVAILABLE NEXT TIME, because this handler cannot know which R12 path or
             # which ladder rung produced the exit, so naming a level would risk describing the wrong one.
    ```
    Bare `python3 -m pytest` summary:
    ```
    NOTE: 5 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    695 passed in 39.51s
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved 5ne0fo --by-human`); OQ-01 is resolved and no question blocks. Begin with `aw ipd begin 5ne0fo`.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition; an edit outside it is made and justified at finalize with `--scope-reason <path>=<why>`. STOP only for a genuinely unsafe condition: a concurrent edit to `agent_workflows/oc_runipd.py` that cannot be safely combined, or the `except KeyboardInterrupt as exc:` handler in `oc_runipd.main` no longer containing the cited sentences.

Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*`; never claim a result you did not run. The mutation is temporary and MUST be reverted before E-02; it is never committed.

Commits: commit only the Scope-Paths files you changed through `aw commit 5ne0fo -- <paths>`; never `git add -A`, never push, never tag. Verify the staged set with `git diff --cached --name-only` before committing.

Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize; when executed by hand, run `aw ipd finalize 5ne0fo` only after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms. Never hand-edit `- Status:` or hand-roll a `git mv` into `executed/`.
