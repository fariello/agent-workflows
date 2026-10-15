# IPD: Restore behavioral coverage of oc_runipd.main interrupt stderr preservation notice

- Date: 2026-10-14
- Kind: child
- Concern: The `KeyboardInterrupt` handler in `agent_workflows.oc_runipd.main` prints the operator-facing exit notice ("Interrupted; durable run state was preserved.", the SIGTERM variant, and the no-cleanup variant) and returns 130/143, but no live test exercises it since `tests/test_interrupt_menu.py` was deleted in `19313eed`.
- Scope: Add one new behavioral test module that drives the real `oc_runipd.main` into its `KeyboardInterrupt` handler and asserts on captured stderr and the exit code; repoint the now-stale "no live guard currently asserts this" comment in `oc_runipd.main` at the new test.
- Scope-Paths: tests/test_oc_runipd_main_interrupt.py, agent_workflows/oc_runipd.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: zgqs4e
- Set: zgqs4e
- Order: 1
- Highest E allocated: 02
- Author: opencode
- Id: 5ne0fo

## Workflow history

- 2026-10-15 draft (opencode): created.
- 2026-10-15 to-review (opencode): authored from backlog `zgqs4e`; prototype of the test approach run against the current tree.

## Goal

Restore behavioral coverage, lost when `tests/test_interrupt_menu.py::RunnerMainOutputOnInterruptTests` was deleted in commit `19313eed`, of the stderr notice and exit code that `oc_runipd.main` produces when the run is interrupted (SIGINT), terminated (SIGTERM), or terminated without cleanup. Plan `9rthek` classified this site S-07 as RETIRE-UNGUARDED; this plan re-guards it with an outcome test only (P16).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Behavioral test of the interrupt exit notice

- [ ] E-01 Create `tests/test_oc_runipd_main_interrupt.py` with a `unittest.TestCase` that calls the real `oc_runipd.main(["resume", "run-fake"])` with `run_queue` patched to raise `KeyboardInterrupt(<msg>)` (and `emit_shutdown_report`, `resolve_run_dir`, `load_state`, `locked_run`, `install_stop_triggers` patched exactly as the deleted test did, `resolve_run_dir` returning a nonexistent temp path so the summary-table branch is skipped), capturing `sys.stderr`. Three cases: (a) `"clean-up-and-terminate"` asserts exit 130 and stderr contains `"Interrupted; durable run state was preserved."`; (b) `"Terminated by SIGTERM"` asserts exit 143 and stderr contains `"Terminated by SIGTERM; durable run state was preserved."`; (c) `"just-terminate-no-cleanup"` asserts exit 130, stderr contains `"Terminated without clean up; worktree and lanes left in place."` and does NOT contain `"durable run state was preserved"`. Each case also asserts `emit_shutdown_report` was called once with `to_stderr=True`. No `inspect`/`ast`/source reading.
  - Depends on: none
  - Expected outcome: the new module exists, contains only calls into `oc_runipd.main` and assertions on its return value, captured stderr and mock calls, and passes.
  - Execution state: pending

### Task group 2: Repoint the stale comment

- [ ] E-02 In `agent_workflows/oc_runipd.py` `main`, edit only the comment block under "stopdisc (`wqq8ua`) E-03" that reads "which is what `tests/test_interrupt_menu.py::RunnerMainOutputOnInterruptTests` asserted (deleted in `19313eed`; no live guard currently asserts this)" so it names `tests/test_oc_runipd_main_interrupt.py` as the live guard. No executable line changes.
  - Depends on: E-01
  - Expected outcome: `git diff agent_workflows/oc_runipd.py` shows only comment lines changed; `rg -n "no live guard currently asserts this" agent_workflows/oc_runipd.py` no longer matches the S-07 comment.
  - Execution state: pending

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
| F-02 | The deleted test's mock set still drives the current `main` to the handler. | Prototype run 2026-10-15 in this worktree printed: `clean-up-and-terminate 130 'Interrupted; durable run state was preserved.\n...'`, `Terminated by SIGTERM 143 'Terminated by SIGTERM; durable run state was preserved.\n...'`, `just-terminate-no-cleanup 130 'Terminated without clean up; worktree and lanes left in place.\n...'`. |
| F-03 | The SIGTERM variant (exit 143) was never covered by the deleted test; adding it is within the same property. | Deleted test exercised only the two SIGINT messages. |
| F-04 | `agy_runipd.main` has the twin handler, but backlog `zgqs4e` names only `oc_runipd.main` (S-07). | Backlog body: "property: oc_runipd.main interrupt stderr preservation notice". |

## Proposed changes (ordered, validatable)

1. E-01: new test module `tests/test_oc_runipd_main_interrupt.py` (behavioral, three cases).
2. E-02: comment-only repoint in `agent_workflows/oc_runipd.py` `main`.

## Deferred / out of scope (with reason)

- The `agy_runipd.main` twin handler: not named by backlog `zgqs4e`; adding it would broaden scope. A follow-up backlog item may be filed if desired.
- The `stop_interrupt_hint` sentence: already its own concern (`wqq8ua`); not asserted here beyond not breaking.
- Any change to the handler's behavior: none intended.

## Scope check

- Over-scope: none.
- Under-scope: none; the property is the stderr notice plus exit code, both covered by E-01.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_oc_runipd_main_interrupt.py` passes with 3 tests (V-01).
- Mutation check: temporarily changing the handler's notice string in a scratch copy makes the test fail (V-01), then reverted.
- Full suite `python3 -m pytest` passes (V-02).

## Spec / documentation sync

N/A: no spec governs this test or the comment; no behavior or user-facing documentation changes.

## Open questions

### OQ-01: Should the `agy_runipd.main` twin also be covered?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. Backlog `zgqs4e` scopes the property to `oc_runipd.main` (S-07); the agy twin is out of scope (see Deferred).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" -q tests/test_oc_runipd_main_interrupt.py` showing `3 passed`; pasted output of `rg -n "inspect|import ast|read_text|getsource" tests/test_oc_runipd_main_interrupt.py` showing no source-reading use; pasted failing output of the same pytest run after temporarily altering `"durable run state was preserved."` in `agent_workflows/oc_runipd.py` (then `git diff --stat agent_workflows/oc_runipd.py` showing the mutation reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `git diff agent_workflows/oc_runipd.py` showing only `#` comment lines changed and naming `tests/test_oc_runipd_main_interrupt.py`; pasted bare `python3 -m pytest` summary line showing no failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). Commit through `aw commit 5ne0fo -- tests/test_oc_runipd_main_interrupt.py agent_workflows/oc_runipd.py`; never push. Move to `executed/` only after `aw ipd lint --phase pre-transition` conforms and V-01/V-02 are `pass` with pasted evidence.
