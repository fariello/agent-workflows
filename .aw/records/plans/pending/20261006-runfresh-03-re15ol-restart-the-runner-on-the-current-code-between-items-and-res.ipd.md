# IPD: Restart the runner on the current code between items and resume the same run

- Date: 2026-10-06
- Kind: child
- Concern: After Order 02 the runner can tell that an integrated item changed the toolkit code under it, but it keeps running the old code anyway. Spec `25kzda` 5.3b (added by Order 01) requires the driver to restart itself between items on the current code and continue the same run, recorded and bounded, without restarting when the loaded package is not the checkout's own. Both hosts' dispatch loops (`oc_runipd.run_queue` and `agy_runipd.run_queue`) select the next item at the top of a `while True:` loop after reloading state with `load_state(run_dir)`, and both drivers already have a `resume` subcommand that reloads a run from `state.json` and re-enters `run_queue` under `locked_run`, so the restart can reuse that entry point instead of new recovery code.
- Scope: IN: one shared function in `runner_shared`, `restart_on_new_code_if_needed(run_dir, state, *, host_labels, previous_id6, stop_level, replace=None, package_root=None)`, that calls `loaded_code.code_changed(repo, package_root=package_root)` and acts on a pure decision (`none`, `restart`, `unavailable`, `limit-reached`); on `restart` it appends a `driver-restarted` event and a new `state["driver"]["loaded_code"]` entry, increments `state["driver_restarts"]`, saves state, releases the run lock it finds in a process-level registry that `runner_shared.run_lock` maintains, flushes stdio, and replaces the process with the host's `resume` of the same run (POSIX `os.execv`; Windows child-and-exit). Call it from both hosts' `run_queue` loops once per iteration, after `_observe_between_turn_stop` and before `cascade_dependency_blocked`, and nowhere else. Never restart while a stop is requested (the existing stop path runs instead) or when nothing is left to dispatch. Show the restart count in the run summary. At the limit, record a run-level `driver-restart-limit` event and refusal and end the loop with the remainder `queued`. OUT: restarting inside an item; re-dispatching finished items; any change to `resume`'s semantics; detecting the change (Order 02); recording lint findings (Order 04); the full scripted-host end-to-end run (Order 05, `hohlc6`, which asserts the restart through the real driver on both hosts).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/render_stream.py, tests/test_driver_restart.py
- Item-Dependencies: executed:34zv7d
- Status: approved
- Readiness: go-pending-approval
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: runfresh
- Order: 3
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: re15ol
- Approval: 2026-10-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-07 approved (aw set): status set to approved

- 2026-10-07 cross-reference (opencode its_direct/pt3-claude-opus-5.5-1m-us): conventions note on the fresh `tool-identity-verified` assertion now points at `hohlc6` E-05 (added by the `hohlc6` review, finding PR-008); no requirement of this plan changed.
- 2026-10-07 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED
- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008
- 2026-10-06 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 03 of Set `runfresh`. Implements spec `25kzda` 5.3b points 2 to 5 and 7, as amended by Order 01, using the existing `resume` path so no run state is reconstructed by new code.

## Goal

Make every item after a toolkit change run, finalize and retire under the code that change put on disk, by restarting the driver between items into a normal `resume` of the same run.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the restart

- [ ] E-01 Add `runner_shared.restart_decision(change, restart_count, limit=20, *, disabled=False, stop_level=None, has_work=True) -> str` (pure) returning `none` when `disabled` (env `AW_NO_DRIVER_RESTART=1`), when `stop_level` is not None, when `has_work` is False, or when `change.changed` is False; `unavailable` when changed but not `change.restartable`; `limit-reached` when changed, restartable and `restart_count >= limit`; otherwise `restart`. Then add `restart_on_new_code_if_needed` as described in Scope. On `restart` it: appends to `events.jsonl` `{"event": "driver-restarted", "old_fingerprint", "new_fingerprint", "changed_files", "previous_id6", "restart_count"}` (spec `25kzda` 5.3b point 4); APPENDS `{"package_root", "fingerprint": change.new, "recorded_at", "is_target_checkout": True, "restart": n}` to `state["driver"]["loaded_code"]` itself, because Order 02's `loaded_code_record` writes no state and `resume` never calls `initialize_run_core`, so nothing else would (spec A.2); increments `state["driver_restarts"]`; saves state; and calls `replace(argv, env)` (default: `os.execv` on POSIX, `subprocess.call` then `sys.exit` on Windows, mirroring `checkout_pin.check_and_reexec`). `unavailable` does nothing (Order 02 already announced it at run start). `has_work` is True when any item is `queued` or `runner_shared.deferred_integration_items(state)` is non-empty.
  - Depends on: none
  - Expected outcome: the decision returns each of the four values for its inputs, including `none` for `disabled`, for a pending stop level and for no remaining work; with a fake `replace`, a `restart` writes the event with all five fields, appends the loaded-code entry, increments the counter, saves state, releases the lock, and calls `replace` once.
  - Execution state: pending

- [ ] E-02 Build the resume argv: `[sys.executable, "-m", "agent_workflows", <"oc"|"agy">, "run", "resume", <run-id>, "--repo", state["repo"]]`, the host token derived from `host_labels` (`OC_HOST_LABELS` -> `oc`, `AGY_HOST_LABELS` -> `agy`), plus the display options frozen in `state["options"]`: `--quiet` when `output_mode == "quiet"`, `--raw` when `"raw"`, nothing for `clean`, and `-v` repeated `verbosity` times. THIS MAPPING IS REQUIRED, not cosmetic: there is no `--output-mode` flag (`runner_shared.add_output_mode_flags` registers only `--quiet`/`--raw`/`-v`), and `resume`'s parser defaults `output_mode` to `clean` (`sub_parser.set_defaults(output_mode="clean")`), which `run_queue` then writes into `state["options"]`, so omitting it would silently reset a `--quiet` run to `clean`. Pass no other flag (`refuse_frozen_flags_on_resume` refuses `--retry-budget`; `--verify-with` is refused). The env is `os.environ` plus `AW_DRIVER_RESTART=<n>`; leave `AW_NO_REEXEC`/`AW_REEXEC_FROM`/`PYTHONPATH` and the cwd untouched, so the replaced process resolves `agent_workflows` exactly as this one did (`restartable` already established that root is the checkout). Quote each host's `resume` parser lines for `--repo`, `--quiet`, `--raw`, `-v` in the evidence.
  - Depends on: E-01
  - Expected outcome: for frozen `quiet`/verbosity 2 the argv ends `--quiet -v -v`, for `clean`/0 it carries no display flag; both hosts' `build_parser().parse_args(argv[4:])` accept it (oc and agy `resume`), and a real subprocess of the argv against an all-terminal fixture run exits 0 with `state["options"]["output_mode"]` unchanged.
  - Execution state: pending

- [ ] E-03 Release the run lock before replacing the process. `run_queue` is called INSIDE `with locked_run(run_dir):` in each host's `main` without an `as` binding, so the loop cannot see the handle. Add a module-level registry in `runner_shared` (`_HELD_RUN_LOCKS: dict[str, RunLockHandle]`, keyed by the resolved run dir, the same shape as `_RUN_ATTESTATIONS`), set by `run_lock` after acquisition and popped in its `finally`, with `held_run_lock(run_dir)`; `restart_on_new_code_if_needed` releases it with `RunLockHandle.release()` (idempotent; it also releases the `platform_lock` owner). When no lock is registered (a caller that entered `run_queue` without `locked_run`, as many tests do), it does not restart and appends one `driver-restart-unavailable` event with reason `no-run-lock`. Do not run `clean_shutdown` (between items no child turn is live) and do not unlink the attestation token: `get_run_attestation` in the resumed process reloads it from `DRIVER_ATTEST_FILENAME`. There is no signal-handler teardown to call: `exec` resets handlers and the resumed `main` re-installs them via `install_stop_triggers`.
  - Depends on: E-02
  - Expected outcome: after a fake replacement, `driver.lock` is acquirable by another process; a real exec in E-05 resumes without `Run is already controlled by another process`.
  - Execution state: pending

### Task group 2: wire it

- [ ] E-04 Call `restart_on_new_code_if_needed` from `oc_runipd.run_queue` and `agy_runipd.run_queue` once per `while True:` iteration, immediately after `wind_down = _observe_between_turn_stop(...)` and before `cascade_dependency_blocked`, passing the host's labels, `stop_level=level`, and `previous_id6` (a new local set to `runnable["id6"]` where `current_setid` is set before `execute_item`; None before the first dispatch). On `limit-reached`, the function appends a run-level `driver-restart-limit` event, stores `state["driver_restart_refusal"] = {"code": "driver-restart-limit", "reason", "remedy"}` (remedy: resume the run once the toolkit code has settled), prints it to stderr, saves state and returns the decision; the loop then `break`s, so the remainder stays `queued` and the existing post-loop report, summary and `run_exit_code(..., stopped=False)` run (exit 1, measured at review: `run_exit_code([executed, queued], stopped=False) == 1`). `record_refusal` is not used here because it requires an item. In `render_stream.render_run_summary_table`, show `Restarts: N` beside the existing outcome line when `state.get("driver_restarts", 0) > 0`, and the `driver_restart_refusal` reason and remedy in the diagnostics block when present.
  - Depends on: E-03
  - Expected outcome: both hosts call the function once per iteration at that point; the summary shows `Restarts: 1` for a state carrying it; a limit-reached run ends with the event, the refusal in the summary, `queued` remainder and exit 1.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_driver_restart.py`: unit cases for every `restart_decision` branch; a fake-replacement case per host (call each host's `run_queue` over a fixture run whose first iteration sees a changed fixture `package_root`, entered under `locked_run`) asserting the event fields, the appended loaded-code entry, the counter, the lock acquirable from another process, and the argv including the frozen display flags; a limit case; an unavailable case and a no-lock case (no replacement call); a pending-stop case (no replacement call; the existing stop path records the deliberate stop); and ONE real-exec case: a subprocess that holds `locked_run` on an all-terminal fixture run, calls `restart_on_new_code_if_needed` with a fixture `package_root` it has just edited (so `restartable` holds because fixture repo and root are the same directory) and the default `replace`, with the subprocess's cwd at this repository's root and `AW_NO_REEXEC=1` (so the replaced `python -m agent_workflows` imports the same package and `checkout_pin` does not re-exec into the fixture), and the fixture tree containing a small `agent_workflows/<x>.py` for the fingerprint to cover; asserting the subprocess exits 0, the run dir records `driver-restarted` once, and stderr carries no `already controlled by another process`. The full scripted-host run (a child changes the linter and the orchestrator then retires) is Order 05's (`hohlc6` E-02) and is not duplicated here. Prove the tests can fail by making `restart_decision` always return `none` and pasting the failing fake-replacement and real-exec cases.
  - Depends on: E-04
  - Expected outcome: the new file passes; the mutation fails it; the existing runner tests listed under Required tests pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `resume` IS THE RESTART ENTRY POINT. Both drivers' `main` handle `resume` by resolving the run directory, applying resume-time options, calling `install_stop_triggers`, and entering `run_queue` under `with locked_run(run_dir):`. A restarted driver that runs `resume` therefore gets every recovery the operator path gets (`reconcile_interrupted`, `requeue_interrupted`, `_integrate_stranded_lanes`).
- `resume` REFUSES FROZEN FLAGS. `refuse_frozen_flags_on_resume` refuses `--retry-budget` on resume, and `as <profile>`/`--verify-with` are refused; the restart passes none of those, only display options, which `run_queue` already accepts on resume.
- `checkout_pin.check_and_reexec` RE-EXECS WHEN THE IMPORTED PACKAGE IS NOT THE CHECKOUT'S. A restarted driver launched with `-m agent_workflows` from the repository resolves to the checkout's package, so that check is a no-op there; when the driver is not the checkout's package, Order 02 marks the run `restartable=False` and this plan never restarts.
- THE CHILD-PIN CACHE IS PER PROCESS. `_TOOL_IDENTITY_VERIFIED` is a module-level dict; a new process starts empty and re-verifies, which is the behavior spec `25kzda` 5.3b point 7 requires. No code change is needed for that. The fresh `tool-identity-verified` event after a restart is asserted by Order 05 (`hohlc6` E-05, a direct exec case; its E-02 run uses `--no-self-finalize` and never calls the check); this plan's real-exec case resumes an all-terminal run that never calls `assert_child_tool_identity`.
- THE CALL-SITE PIN TESTS ARE GONE. `tests/test_rununify_run_queue.py` and `test_no_call_site_was_rewritten` were removed (`git log -S test_no_call_site_was_rewritten -- tests/` lists `19313eed7` and `d4dd6b880`); comments in `run_queue` still mention them. No pin constrains the new call; the shared function saving state itself is still the cleaner shape.
- `resume` DEFAULTS `output_mode` TO `clean`. `runner_shared.add_output_mode_flags` calls `sub_parser.set_defaults(output_mode="clean")` for `resume` too, and `run_queue` writes a non-None `output_mode` into `state["options"]`; measured at review, `build_parser().parse_args(["resume","run-x"])` gives `output_mode='clean'` on both hosts. The restart must therefore pass the frozen mode explicitly.
- THE STOP REQUEST IS A FILE THAT NOTHING CLEARS, but the WIND-DOWN IS IN MEMORY. `stop-request.json` persists, so a resumed process would see a level again; but `wind_down` and its captured `current_setid` (level 2's boundary) live only in the loop, so a restart under a pending stop would lose the set boundary and stop early. Hence no restart while `level` is not None.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The loop reloads state at the top of every iteration, so that is the one point between items where all prior state is on disk. `oc_runipd.run_queue`: `level = runner_stop.poll_stop(run_dir)` then `state = load_state(run_dir)`; `agy_runipd.run_queue` has the same shape. | the first statements of each loop body |
| F-02 | The lock is held by a context manager. `locked_run` is `with run_lock(run_dir) as lock: try: yield lock finally: ... clean_shutdown(...)`. `os.execv` replaces the process without running `finally`, so the lock must be released explicitly first. | `runner_shared.locked_run` |
| F-03 | The process-replacement precedent exists: `checkout_pin.check_and_reexec` calls `os.execve(sys.executable, argv, env)` on POSIX and falls back to `subprocess.call` plus `sys.exit` on Windows. | `checkout_pin.check_and_reexec` |
| F-05 | The run lock is unreachable from the loop. Both hosts' `main` enter `with locked_run(run_dir):` with no `as` binding and call `run_queue(run_dir, ...)`, whose signature carries no lock. | `oc_runipd.main` / `agy_runipd.main` `resume` and `start` branches; `oc_runipd.run_queue` signature |
| F-06 | Order 02's loaded-code record is written only by `initialize_run_core`; `loaded_code_record` writes no state, so a restart that does not append its own entry leaves `state["driver"]["loaded_code"]` with only the start entry, against spec A.2. | Order 02 (`34zv7d`) E-01 and E-03 |
| F-04 | The 2026-10-06 run had 12 children that changed toolkit code, so with this change it would have restarted up to 12 times; each restart costs one interpreter start plus a state load, measured in seconds, against items measured in tens of minutes. | the run's 13 `ipd-finalized` events and per-item durations in its summary |

## Proposed changes (ordered, validatable)

1. Shared restart function with a pure decision (stop- and work-aware) and an injected replacement; it appends the loaded-code entry itself (E-01).
2. Resume argv carrying the frozen display mode as `--quiet`/`--raw`/`-v` (E-02).
3. A run-lock registry so the loop can release the lock before replacement (E-03).
4. One call per loop iteration in both hosts after the stop observation; summary count; run-level limit refusal (E-04).
5. Unit, fake-replacement and one real-exec test with a mutation proof; the scripted-host end-to-end stays in Order 05 (E-05).

## Deferred / out of scope (with reason)

- RESTART INSIDE AN ITEM. See the orchestrator's Deferred section.
  - Carrier-Declined: between-item restart covers the measured failure
- A FLAG TO DISABLE THE RESTART. Order 05 needs to disable it to reproduce the old failure; it does so with an environment variable read only by this function (`AW_NO_DRIVER_RESTART=1`), documented in the function's docstring, not a public CLI flag.
  - Carrier-Declined: no operator need measured; the test-only switch is enough

## Scope check

- Over-scope: none. The shared module, one call in each host loop, the summary line in `render_stream`, one test file. The scripted-host end-to-end run was moved out to Order 05, which already owns it (review PR-007).
- Under-scope: none known.

## Required tests / validation

- Baseline bare `python3 -m pytest` before editing.
- `python3 -m pytest -o addopts="" tests/test_driver_restart.py tests/test_loaded_code.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_runner_shared.py tests/test_runner_stop_triggers_e2e.py -q` pasted.
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
- Resolution or deferral rationale: RESOLVED (amended at review, PR-001): after the state reload AND after `_observe_between_turn_stop`, before the dependency cascade. Later, the cascade and selection would run on old code, which is the defect. A restart is skipped whenever a stop level is pending, because the wind-down and its captured set boundary are in-memory loop state that a replaced process would lose; the existing stop path then ends the run on the current process, and the operator's later `resume` starts on the new code anyway.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the decision and restart functions, and test output for every decision branch (including `disabled`, pending stop and no work) and the fake-replacement case showing the event's five fields, the appended `loaded_code` entry, the counter, and one replacement call.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the built argv for each host for frozen `quiet`/2 and `clean`/0, the quoted `resume` parser lines for `--repo`, `--quiet`, `--raw`, `-v`, and the real-subprocess resume of an all-terminal fixture run exiting 0 with `options.output_mode` unchanged before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `run_lock` registry diff, the test showing `driver.lock` acquirable by another process after the fake replacement, the no-lock case's `driver-restart-unavailable` event, and the real-exec case's stderr with no `already controlled by another process`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the diffs in both host loops and in `render_run_summary_table`; a rendered summary showing `Restarts: 1`; the limit case's `driver-restart-limit` event, the summary's refusal line, the `queued` remainder and the exit code 1.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new test file passing with its count; the real-exec case's `driver-restarted` event; the pending-stop and no-lock cases showing no replacement call; the mutation failing (fake-replacement and real-exec cases) and the revert passing; the Required-tests run passing; a grep of the new file for `inspect`, `ast.`, or `read_text` on `agent_workflows/` sources returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only declared paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Open questions: all resolved. Scope fence: `- Scope-Paths:` declares the change; an out-of-scope edit is made and then justified with `--scope-reason` at finalize. Commit only declared paths through `aw commit <plan> -- <paths>`; never push. You MUST paste the actual runner output for every test claim. Lifecycle: under a runner, the runner owns begin/finalize; by hand, finish with `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms; never `git mv` the plan by hand.
