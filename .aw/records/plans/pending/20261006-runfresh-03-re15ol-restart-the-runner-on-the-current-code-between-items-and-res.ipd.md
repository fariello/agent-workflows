# IPD: Restart the runner on the current code between items and resume the same run

- Date: 2026-10-06
- Kind: child
- Concern: After Order 02 the runner can tell that an integrated item changed the toolkit code under it, but it keeps running the old code anyway. Spec `25kzda` 5.3b (added by Order 01) requires the driver to restart itself between items on the current code and continue the same run, recorded and bounded, without restarting when the loaded package is not the checkout's own. Both hosts' dispatch loops (`oc_runipd.run_queue` and `agy_runipd.run_queue`) select the next item at the top of a `while True:` loop after reloading state with `load_state(run_dir)`, and both drivers already have a `resume` subcommand that reloads a run from `state.json` and re-enters `run_queue` under `locked_run`, so the restart can reuse that entry point instead of new recovery code.
- Scope: IN: one shared function in `runner_shared` (`restart_on_new_code_if_needed(run_dir, state, *, host_labels, resume_argv, release)`) that calls `loaded_code.code_changed`, and when it reports `changed` and `restartable`: checks a per-run restart counter in state against the limit (20), appends a `driver-restarted` event and a new `driver.loaded_code` entry for the next process to complete, saves state, runs the run lock's release, and replaces the process with `os.execv` of the same interpreter running `-m agent_workflows <oc|agy> run resume <run-id> --repo <repo>` plus the in-force output options, with `AW_DRIVER_RESTART=<n>` in the environment; when `changed` but not `restartable`, does nothing (Order 02 already announced it once); when the limit is reached, records a `driver-restart-limit` refusal and stops the run like a deliberate stop, leaving remaining items `queued`. Call it from both hosts' loops at the top of each iteration, after the state reload and before item selection, and nowhere else. On the resumed side, `loaded_code_record` completes the new `driver.loaded_code` entry and the per-process tool-identity cache starts empty, so `assert_child_tool_identity` re-verifies against the new code. Show the restart count in the run summary. On Windows, where `os.execv` does not replace the process, spawn the resume as a child, wait for it, and exit with its code. OUT: restarting inside an item; re-dispatching finished items; any change to `resume`'s semantics; detecting the change (Order 02); recording lint findings (Order 04).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_driver_restart.py
- Item-Dependencies: executed:34zv7d
- Status: to-review
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: runfresh
- Order: 3
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: re15ol

## Workflow history

- 2026-10-06 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 03 of Set `runfresh`. Implements spec `25kzda` 5.3b points 2 to 5 and 7, as amended by Order 01, using the existing `resume` path so no run state is reconstructed by new code.

## Goal

Make every item after a toolkit change run, finalize and retire under the code that change put on disk, by restarting the driver between items into a normal `resume` of the same run.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the restart

- [ ] E-01 Add `runner_shared.restart_on_new_code_if_needed` as described in Scope, with its decision split into a pure function `restart_decision(change, restart_count, limit)` returning `none`, `restart`, `unavailable` or `limit-reached`, so the decision can be tested without replacing a process. The process replacement itself goes through one injected callable (default `os.execv`, or the Windows child-spawn fallback), so tests substitute it.
  - Depends on: none
  - Expected outcome: the decision function returns `none` when unchanged, `restart` when changed and restartable under the limit, `unavailable` when not restartable, and `limit-reached` at the limit; with a fake replacement callable, a `restart` writes the `driver-restarted` event, increments the counter, saves state, calls the release, and calls the replacement with the expected argv and environment.
  - Execution state: pending

- [ ] E-02 Build the resume command and carry the display options. The argv is `[sys.executable, "-m", "agent_workflows", <"oc"|"agy">, "run", "resume", <run-id>, "--repo", <repo>]` plus `--output-mode <mode>` and the verbosity flags currently frozen in `state["options"]`. Confirm by reading each host's `resume` argument parser that every flag passed exists on `resume` and that `resume` re-enters `run_queue` under `locked_run` with `install_stop_triggers` (both do today), and record the quoted parser lines. Set `AW_DRIVER_RESTART` to the new count so the resumed process can log it, and leave `AW_NO_REEXEC` and `AW_REEXEC_FROM` untouched (the restarted process is in the checkout already, so `checkout_pin.check_and_reexec` finds matching roots and does nothing).
  - Depends on: E-01
  - Expected outcome: the argv a fake replacement receives is exactly the resume command for the run, and running that argv against a prepared fixture run (real subprocess, not exec) resumes it.
  - Execution state: pending

- [ ] E-03 Release the run lock before replacing the process. `locked_run` holds `driver.lock` through a context manager whose `finally` runs `clean_shutdown`; `os.execv` skips `finally` blocks. So `restart_on_new_code_if_needed` must receive the lock handle's release (pass it from the loop, which runs inside `with locked_run(run_dir) as lock:`; add the `as lock` binding where missing) and call it, plus the stop-trigger teardown, before the replacement. The resumed process then acquires the lock afresh. Do not run `clean_shutdown`'s child-reaping: between items there is no live child turn.
  - Depends on: E-02
  - Expected outcome: after a fake replacement, `driver.lock` is acquirable by another process; a real restart in the E-05 integration test resumes without `LockBusy`.
  - Execution state: pending

### Task group 2: wire it

- [ ] E-04 Call `restart_on_new_code_if_needed` from `oc_runipd.run_queue` and `agy_runipd.run_queue` at the top of each `while True:` iteration, immediately after `state = load_state(run_dir)` and before `cascade_dependency_blocked`, passing the host's labels and the lock release. Add the restart count (`state["driver_restarts"]`, default 0) to `render_run_summary_table`'s header line as "Restarts: N" when N > 0. When the decision is `limit-reached`, record the refusal through `record_refusal` on no item (a run-level event `driver-restart-limit`) and exit the loop through the existing deliberate-stop path so remaining items stay `queued`.
  - Depends on: E-03
  - Expected outcome: both hosts call the function once per iteration; the summary shows the count; a run at the limit stops with the event and `queued` remainder.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_driver_restart.py`: unit cases for `restart_decision`; a fake-replacement case per host asserting event, counter, release and argv; a limit case; an unavailable case (no replacement call); and one integration case per host that runs the real driver as a SUBPROCESS over a fixture repository whose package tree is a copy of `agent_workflows` and whose first queued item (driven by a scripted host turn) edits a `.py` file in that copy, asserting the run directory records `driver-restarted` once, the second item runs, and the run finishes with every item's status as before the restart plus the restart record. Prove the tests can fail by making the decision always `none` and pasting the integration failure (no `driver-restarted` event).
  - Depends on: E-04
  - Expected outcome: the new file passes on both hosts; the mutation fails it; existing `tests/test_oc_runipd.py`, `tests/test_runner_shared.py` and the runner run-queue tests pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `resume` IS THE RESTART ENTRY POINT. Both drivers' `main` handle `resume` by resolving the run directory, applying resume-time options, calling `install_stop_triggers`, and entering `run_queue` under `with locked_run(run_dir):`. A restarted driver that runs `resume` therefore gets every recovery the operator path gets (`reconcile_interrupted`, `requeue_interrupted`, `_integrate_stranded_lanes`).
- `resume` REFUSES FROZEN FLAGS. `refuse_frozen_flags_on_resume` refuses `--retry-budget` on resume, and `as <profile>`/`--verify-with` are refused; the restart passes none of those, only display options, which `run_queue` already accepts on resume.
- `checkout_pin.check_and_reexec` RE-EXECS WHEN THE IMPORTED PACKAGE IS NOT THE CHECKOUT'S. A restarted driver launched with `-m agent_workflows` from the repository resolves to the checkout's package, so that check is a no-op there; when the driver is not the checkout's package, Order 02 marks the run `restartable=False` and this plan never restarts.
- THE CHILD-PIN CACHE IS PER PROCESS. `_TOOL_IDENTITY_VERIFIED` is a module-level dict; a new process starts empty and re-verifies, which is the behavior spec `25kzda` 5.3b point 7 requires. No code change is needed for that, only a test asserting the resumed run logs a fresh `tool-identity-verified` event.
- `run_queue` CALL-SITE PINS. `tests/test_rununify_run_queue.py` pins the number of `register_signal_report` sites and `tests/test_runner_shared.py::WrapperTests::test_no_call_site_was_rewritten` pins `save_state` call sites per runner. Add the new call so it does not add a `register_signal_report` or `save_state` site in the host modules (the shared function saves state itself); if a pin must move, name it and update it in this plan with the reason.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The loop reloads state at the top of every iteration, so that is the one point between items where all prior state is on disk. `oc_runipd.run_queue`: `level = runner_stop.poll_stop(run_dir)` then `state = load_state(run_dir)`; `agy_runipd.run_queue` has the same shape. | the first statements of each loop body |
| F-02 | The lock is held by a context manager. `locked_run` is `with run_lock(run_dir) as lock: try: yield lock finally: ... clean_shutdown(...)`. `os.execv` replaces the process without running `finally`, so the lock must be released explicitly first. | `runner_shared.locked_run` |
| F-03 | The process-replacement precedent exists: `checkout_pin.check_and_reexec` calls `os.execve(sys.executable, argv, env)` on POSIX and falls back to `subprocess.call` plus `sys.exit` on Windows. | `checkout_pin.check_and_reexec` |
| F-04 | The 2026-10-06 run had 12 children that changed toolkit code, so with this change it would have restarted up to 12 times; each restart costs one interpreter start plus a state load, measured in seconds, against items measured in tens of minutes. | the run's 13 `ipd-finalized` events and per-item durations in its summary |

## Proposed changes (ordered, validatable)

1. Shared restart function with a pure decision and an injected replacement (E-01).
2. Resume argv and environment, checked against both hosts' parsers (E-02).
3. Explicit lock release before replacement (E-03).
4. One call per loop iteration in both hosts; summary count; limit stop (E-04).
5. Unit, fake-replacement and real-subprocess integration tests with a mutation proof (E-05).

## Deferred / out of scope (with reason)

- RESTART INSIDE AN ITEM. See the orchestrator's Deferred section.
  - Carrier-Declined: between-item restart covers the measured failure
- A FLAG TO DISABLE THE RESTART. Order 05 needs to disable it to reproduce the old failure; it does so with an environment variable read only by this function (`AW_NO_DRIVER_RESTART=1`), documented in the function's docstring, not a public CLI flag.
  - Carrier-Declined: no operator need measured; the test-only switch is enough

## Scope check

- Over-scope: none. The shared module, one call in each host loop, one test file.
- Under-scope: none known. If a run-queue call-site pin must change, that test file is outside Scope-Paths and is justified at finalize with `--scope-reason`.

## Required tests / validation

- Baseline bare `python3 -m pytest` before editing.
- `python3 -m pytest -o addopts="" tests/test_driver_restart.py tests/test_loaded_code.py tests/test_oc_runipd.py tests/test_runner_shared.py -q` pasted.
- The run-queue pin tests named in conventions, pasted passing.
- Mutation run pasted.
- Bare `python3 -m pytest` after, reconciled; `aw ipd lint` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

Implements spec `25kzda` 5.3b points 2 to 5 and 7, as amended by Order 01. No spec edited here. The `AGENTS.md` paragraph "The runners own ordering, isolation, and orchestrators" is not changed: it describes what a run guarantees, and this plan makes the existing guarantees hold across toolkit changes rather than adding a new one.

## Open questions

### OQ-01: Replace the process, or start a child and exit?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: replace the process (`os.execv`) on POSIX, child-and-exit on Windows. Replacing keeps the same process id, terminal and signal handling, so an operator's Ctrl-C and `aw oc run stop` still reach the driver; a child-and-exit on POSIX would leave a parent process waiting and doubling the signal path. This matches `checkout_pin.check_and_reexec`'s existing choice.

### OQ-02: Where exactly in the loop?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: immediately after the state reload, before the dependency cascade and before stop handling. Earlier, nothing has been persisted for this iteration yet; later, the cascade and selection would run on old code, which is the defect. A pending stop request is preserved because stop markers are files the resumed process polls on its first iteration.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the new function and decision function, and the unit test output for the four decision values and the fake-replacement case (event, counter, release call, replacement call).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the built argv for each host, the quoted `resume` parser lines for each flag passed, and the real-subprocess resume of a prepared fixture run using that argv.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the test showing `driver.lock` acquirable by another process after the fake replacement, and the integration run's absence of `LockBusy`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the diffs in both host loops; a run summary showing "Restarts: 1"; the limit case's `driver-restart-limit` event and `queued` remainder.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new test file passing on both hosts with its count; the integration case's `driver-restarted` event, the fresh `tool-identity-verified` event after it, and the final item statuses; the mutation failing and the revert passing; the pin tests passing; a grep for source-structure reads returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only declared paths plus any justified pin update.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Commit only declared paths through `aw commit <plan> -- <paths>`; never push. Paste actual output. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.
