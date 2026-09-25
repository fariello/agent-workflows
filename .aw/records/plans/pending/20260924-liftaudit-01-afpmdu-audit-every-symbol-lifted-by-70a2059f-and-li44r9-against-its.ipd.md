# IPD: Audit every symbol lifted by 70a2059f and li44r9 against its pre-lift host body and fix each transcription divergence

- Date: 2026-09-24
- Kind: child
- Concern: THE AUDIT THE BACKLOG ITEM ASKS FOR HAS BEEN PERFORMED AT AUTHORING (read-only, HEAD `877545fc`), AND ITS HEADLINE PREMISE IS FALSE: `ccu3k7` says all five `execute_item_core` deliberate-stop defects "are fixed by `13xo5k`". FOUR ARE. DEFECT 5 IS STILL LIVE ON BOTH HOSTS. The two SPAWN-PATH handlers in `runner_shared.execute_item_core` (`except runner_stop.StopNowForce` and `except runner_stop.StopAtCheckpoint` around `spawn_executor(...)`) still end in `return` and still assign `item["status"] = runner_stop.FORCED_DISPOSITION` / `STOPPED_DISPOSITION` directly, where the pre-lift host bodies (`git show 70a2059f^:agent_workflows/oc_runipd.py`, `execute_item`, the handlers after `run_opencode(...)`) routed status through `reconcile_disposition(repo, item, run_dir, 1)` and `raise`d. Plan `13xo5k` fixed the `stop.exit_code` crash and the missing `git_status_fn`, but its own V-03 evidence PINNED the `return` as correct ("Spawn path: `mod.execute_item(...)` returns cleanly (no exception escapes)"), and the tests it added (`tests/test_runner_stop_level3.py`, `tests/test_runner_stop_level4.py`) were later DELETED by the suite trim `19313eed`. So nothing in `tests/` now drives a deliberate stop through `execute_item_core` at all (`grep -ln 'StopNowForce\|StopAtCheckpoint' tests/*.py` -> no file).
  MEASURED BEHAVIORALLY, NOT FROM READING. A throwaway probe drove each host's REAL `run_queue` over two queued, approved items, with the launcher (`run_opencode` / `run_agy_turn`) replaced by a fake that records which id6 it was called for and raises a deliberate stop. Pre-lift, `run_queue`'s `except runner_stop.StopNowForce:` / `except runner_stop.StopAtCheckpoint:` arms set `stopped_at_checkpoint = True` and `break`, so the second item is never dispatched. At HEAD:

      RESULT oc_runipd level 3: dispatched=['qa0001', 'qa0002'] rc=1 exc=None statuses=[('qa0001', 'interrupted'), ('qa0002', 'interrupted')]
      RESULT oc_runipd level 4: dispatched=['qa0001', 'qa0002'] rc=1 exc=None statuses=[('qa0001', 'unknown_outcome'), ('qa0002', 'unknown_outcome')]
      RESULT agy_runipd level 3: dispatched=['qa0001', 'qa0002'] rc=1 exc=None statuses=[('qa0001', 'interrupted'), ('qa0002', 'interrupted')]
      RESULT agy_runipd level 4: dispatched=['qa0001', 'qa0002'] rc=1 exc=None statuses=[('qa0001', 'unknown_outcome'), ('qa0002', 'unknown_outcome')]

  An operator's level-3 or level-4 stop does NOT stop the run: the NEXT IPD is dispatched (a real run pays for a new agent turn), `run_queue`'s `stopped_at_checkpoint` flag is never set so the run is not reported as deliberately stopped, and level 4 leaves `unknown_outcome` as the ITEM STATUS where the original set `interrupted` via `reconcile_disposition` (whose deliberate-stop branch returns `runner_stop.STOPPED_DISPOSITION` for BOTH levels, carrying indeterminacy on the record's `certainty` flag). `unknown_outcome` is not `interrupted`, so `requeue_interrupted` skips it outright rather than applying its R19 indeterminate gate. This is exactly `ccu3k7`'s defect 5 ("an operator who requested a stop got a run that kept spending money on the next IPD"), still shipping. NOTE, CORRECTING `ccu3k7`: the RUN EXIT CODE is not a discriminator here. `runner_stop.deliberate_stop_exit_code(['interrupted', 'queued'], success_states={EXIT_SUCCESS_TOKEN}, stopped=True)` is `1` (measured), because `interrupted` is not a success state, so the fixed run also exits 1 for this queue; the harm is the extra dispatch and the lost stop, not the number.
  THE REST OF THE AUDIT FOUND ONE MORE LATENT DEFECT AND OTHERWISE CONFIRMS THE LIFTS. Every other symbol either matches its pre-lift body after normalization, or differs only by an intentional, commit-attributable change (lazy `from agent_workflows import X` added in the body, annotations loosened to `Any`, host-varying values moved to explicit `labels=`/`*_fn=`/`*_builder=` injection). The latent defect: `runner_shared._record_forced_stop` still has a fallback branch `git_status(repo)` that calls the SHARED `runner_shared.git_status`, whose `run_checked` is keyword-only with no default. That is byte-for-byte the transcription class `ccu3k7` describes (identical call text, different resolved signature). Measured: `_record_forced_stop(Path(t), {"repo": t}, {"id6": "x"}, runner_stop.StopNowForce(level=4, events_seen=1))` returns `git_state` = `<unobserved: git_status() missing 1 required keyword-only argument: 'run_checked'>`. Both in-tree call sites pass `git_status_fn=git_status` (13xo5k), so no shipped path reaches the fallback today; `_record_checkpoint_stop` already made the same parameter REQUIRED for this reason, and `_record_forced_stop` did not.
- Scope: Fix `ccu3k7`'s still-live defect 5 in `runner_shared.execute_item_core`'s two SPAWN-PATH deliberate-stop handlers so they match the pre-lift host bodies (status via `reconcile_disposition`, then `raise`), remove the dead-and-broken `git_status(repo)` fallback in `runner_shared._record_forced_stop`, and add BEHAVIORAL tests that drive the real `run_queue` on BOTH hosts and would have caught defect 5. Also commit the drift scan as a reproducible tool. OUT: the four symbols other plans own (`classify_recovery_disposition`, `build_verify_and_continue_notice`, `reconcile_disposition` -> `recovone`/`zt2b16`; `reconcile_item_on_interrupt` -> `intrecon`/`2415x6`); the `record_item_spec_edits` key/shape divergence (`tm5vnx`); `route_recovery_turn`'s shared copy (not reached; `zt2b16` records why it cannot be consolidated yet); any change to `runner_stop`'s exception classes or to the verify/reconcile handler pair, which already matches the original.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_liftaudit_stop_halts_run.py, tools/lift_drift_scan.py, tests/test_lift_drift_scan.py
- Item-Dependencies: none
- Status: to-review
- Set: liftaudit
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: afpmdu
- From-Backlog: ccu3k7
- Blocks-Release: next
- Priority: high
- Work-Kind: bug

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog ccu3k7; ran the full lift audit read-only at HEAD 877545fc over all 27 symbols moved by 70a2059f and 12a5c05b plus execute_item_core against each pre-lift host execute_item, and found ccu3k7's claim that 13xo5k fixed all five defects is FALSE: defect 5 (spawn-path stop handlers return instead of raise) is still live on both hosts, measured by driving the real run_queue, plus one latent arity defect in _record_forced_stop's fallback.

## Goal

Make a deliberate level-3/level-4 stop on an execute turn STOP THE RUN again on both hosts, as it did before `70a2059f`, with a behavioral test on each host's real `run_queue` that fails on today's code; remove the one remaining latent resolved-signature defect the audit found; and leave the audit itself re-runnable as a committed tool so the next lift can be checked the same way.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: commit the audit so its numbers reproduce

- [ ] E-01 ADD `tools/lift_drift_scan.py`, the lift-drift scanner, REUSING `tools/runner_fork_scan.py` rather than re-implementing it. `runner_fork_scan` compares the two host modules AT ONE REVISION; it does not compare a pre-lift host body at `<commit>^` against the shared body, so the new tool is needed, but it must import `runner_fork_scan.normalize`, `runner_fork_scan.top_level_defs`, `runner_fork_scan.free_names` and `runner_fork_scan.is_pure_delegation` instead of copying them (import by path: `sys.path.insert(0, <tools dir>)`, the way the authoring probe did).
  THE LOGIC, which the authoring probes under `/tmp/opencode/probe-liftaudit/` performed and which this tool must reproduce exactly: (1) for a lift commit `C`, the LIFTED set is every top-level def/class NEW in `C:agent_workflows/runner_shared.py` versus `C^`, plus `execute_item_core` paired with each host's `execute_item`; (2) BODY DIFF: for each lifted symbol and each host defining it at `C^`, compare `normalize()` of the pre-lift host body against the HEAD shared body after erasing `oc_runipd`/`agy_runipd`/`runner_shared` module qualifiers, and print a unified diff; (3) RESOLVED-SIGNATURE CHECK, the class that let defects 3 and 4 through a line-by-line review: for every `ast.Call` whose `func` is a bare `ast.Name` inside a HEAD `runner_shared` top-level def, when the name is a `runner_shared` top-level function (and is not shadowed by a local binding or parameter of the enclosing def), report any required positional or keyword-only parameter the call does not supply (skip calls using `*args`/`**kwargs`); (4) HANDLER-VERB CHECK, the class of defect 5: for `execute_item_core` versus each pre-lift `execute_item`, key every `except` handler by (caught type, first call in the `try` body, mapping `run_opencode`/`run_agy_turn` -> `spawn_executor`) and report where the handler's LAST statement differs (`raise` / `return` / fall-through) or where `item["status"]` is assigned directly in one and from a call in the other. Output is plain text with one summary line per check (`arity violations: N`, `handler verb diffs: N`); exit 0 always (a measuring instrument, like `runner_fork_scan`). An `--exclude` option takes symbol names to skip (the executor passes the four excluded names).
  - Depends on: none
  - Expected outcome: `python3 tools/lift_drift_scan.py 70a2059f 12a5c05b` runs at HEAD and, BEFORE E-02/E-03, reports the two spawn-path handler verb diffs (`StopAtCheckpoint`, `StopNowForce` at `spawn_executor`: pre `raise`/via-call, head `return`/direct) on each host and the arity violation `_record_forced_stop -> git_status(...) missing ['run_checked']`, matching the Findings table; the tool imports its helpers from `runner_fork_scan`.
  - Execution state: pending

### Task group 2: fix the defects

- [ ] E-02 RESTORE THE PRE-LIFT CONTROL FLOW IN `runner_shared.execute_item_core`'S TWO SPAWN-PATH DELIBERATE-STOP HANDLERS (the `except runner_stop.StopNowForce as stop:` and `except runner_stop.StopAtCheckpoint as stop:` immediately after `exit_code, session_id, log_path, argv = spawn_executor(`). In each: replace `item["status"] = runner_stop.FORCED_DISPOSITION` / `item["status"] = runner_stop.STOPPED_DISPOSITION` with `item["status"], _ = reconcile_disposition(repo, item, run_dir, 1)` (the verify/reconcile pair in the same function already does exactly this; `repo` is bound well before this point), keep `save_state(run_dir, state)` and the stderr line, and replace the final `return` with `raise`. Leave `attempt["disposition"]` as it is (the pre-lift bodies set it to the runner_stop constant too). Do NOT touch the `except StallTimeout:` handler beside them: its `return` matches the pre-lift body.
  WHY `raise` IS SAFE: the `try:`/`finally:` that wraps this region (the `integearn-05` (`9lyg5h`) cleanup construct, whose comment names `StopNowForce` and `StopAtCheckpoint` as paths it must cover) still runs on a raise, so the suite-baseline checkout is still cleaned up; and both hosts' `run_queue` already have the `except runner_stop.StopNowForce:` / `except runner_stop.StopAtCheckpoint:` arms that `load_state` and `break`, which is where the stop was always meant to land. Correct the in-code comment on that `finally:` if it still describes these handlers as `except ... return`.
  NOTE THE CONFLICT WITH `13xo5k`, AND WHY THIS PLAN WINS IT: executed plan `13xo5k`'s V-03 records "Spawn path: ... returns cleanly (no exception escapes)" as the EXPECTED behavior. That was the transcription defect being certified, not a decision: `13xo5k`'s own Findings say the originals re-raised (F-5, "Do not convert either to a swallow") and its conventions state "THE VERIFY/RECONCILE HANDLERS RE-RAISE ON PURPOSE ... so the driver's outer `except BaseException` routes to the shared reaper". The pre-lift spawn-path handlers did the same. Do not edit `13xo5k`'s executed record; cite it in the commit message.
  - Depends on: E-01
  - Expected outcome: both spawn-path handlers end in `raise` and set `item["status"]` via `reconcile_disposition`; `python3 tools/lift_drift_scan.py 70a2059f 12a5c05b` reports `handler verb diffs: 0` for the two stop types (the `StallTimeout` and `DriverError` key-count differences it may list are the benign ones recorded in Findings F-5/F-6).
  - Execution state: pending

- [ ] E-03 REMOVE THE BROKEN FALLBACK IN `runner_shared._record_forced_stop`: make `git_status_fn` a REQUIRED keyword-only parameter (`git_status_fn: Callable[[Path], str]`, no default) and call it unconditionally, exactly as `runner_shared._record_checkpoint_stop` already does. The fallback `git_status(repo)` resolves to `runner_shared.git_status`, whose `run_checked` is required, so it can only ever produce `<unobserved: ... missing 1 required keyword-only argument: 'run_checked'>`. Check every caller first (`grep -n "_record_forced_stop(" agent_workflows/*.py`): at authoring the only callers were the two in `execute_item_core` (both pass `git_status_fn=git_status`) and the hosts' `_record_forced_stop` wrappers; if a host wrapper calls the shared one WITHOUT `git_status_fn`, pass its own `git_status` there, and if a caller cannot supply it, STOP and report rather than restoring a default.
  - Depends on: E-01
  - Expected outcome: `_record_forced_stop` has no `git_status(repo)` fallback and a required `git_status_fn`; `python3 tools/lift_drift_scan.py 70a2059f 12a5c05b` no longer lists the `_record_forced_stop -> git_status` arity violation.
  - Execution state: pending

### Task group 3: prove it behaviorally

- [ ] E-04 ADD `tests/test_liftaudit_stop_halts_run.py`: a behavioral test, per host (`oc_runipd` with launcher `run_opencode`, `agy_runipd` with launcher `run_agy_turn`) and per level (3 via `runner_stop.StopAtCheckpoint(runner_stop.CheckpointObserver(detector=lambda: 3, requested_level=3, stop_at_checkpoint=True))`, 4 via `runner_stop.StopNowForce(level=4, events_seen=2)`), that drives the host's REAL `run_queue` over TWO queued, approved, lint-conforming plans (reuse `tests.test_oc_runipd._CONFORMING_PLAN` and the state shape of `SelfFinalizeWiringTests._state_and_item`, with `self_finalize: False`, `no_audit: True`, `isolate_worktree: False`), patching `driver_begin` to succeed and the launcher to record the dispatched id6 and raise the stop. Declare the execution role in `setUp` with `support.declare_execution_role(self)` as the neighbouring runner tests do. Assert: (a) the launcher was called for the FIRST id6 ONLY; (b) the second item's persisted status is still `queued`; (c) the first item's persisted status is `interrupted` (`runner_stop.STOPPED_DISPOSITION`) at BOTH levels and its `stopped` record carries `certainty` `known` (level 3) / `indeterminate` (level 4); (d) the `run_queue` return value equals `runner_stop.deliberate_stop_exit_code(runner_shared.exit_code_statuses(<persisted queue>), success_states={runner_shared.EXIT_SUCCESS_TOKEN}, stopped=True)` (measured at authoring as `1` for `['interrupted', 'queued']`, so this is a consistency check, NOT the assertion that proves the fix; (a) and (b) are). Also add one direct unit test that `runner_shared._record_forced_stop` writes the INJECTED `git_status_fn`'s return value as the record's `git_state`, and that omitting `git_status_fn` raises `TypeError` at the call.
  THE TESTS MUST BE SEEN TO FAIL: with E-02 reverted locally, the four `run_queue` tests must fail on (a) (both ids dispatched, as the authoring probe measured); restore E-02 before committing.
  - Depends on: E-02, E-03
  - Expected outcome: 6 new tests (4 `run_queue` tests: 2 hosts x 2 levels; 2 `_record_forced_stop` unit tests) passing with the fix, and the 4 `run_queue` tests failing on assertion (a) with E-02 reverted.
  - Execution state: pending

- [ ] E-05 ADD `tests/test_lift_drift_scan.py`, a FAST guard that runs `tools/lift_drift_scan.py`'s check functions IN-PROCESS against HEAD and asserts `arity violations: 0` for every `runner_shared` top-level def (the resolved-signature class, repo-wide in that module rather than only the lifted symbols), and that `execute_item_core`'s spawn-path `StopNowForce`/`StopAtCheckpoint` handlers end in `raise`. Keep it free of `git show` so it does not depend on history being present (shallow clones in CI): the history-comparing half of the tool stays a manual instrument. This is the "guard for that class" `ccu3k7`'s What-to-do section asks for; its limit (a static arity check cannot see a wrong-but-complete argument) goes in its docstring.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: guard passes at the fixed HEAD and FAILS when either E-02's `raise` is reverted to `return` or E-03's default is restored with its fallback call.
  - Execution state: pending

- [ ] E-06 RUN THE BARE SUITE `python3 -m pytest` (no extra flags) and record the summary line.
  - Depends on: E-04, E-05
  - Expected outcome: the suite's summary line pasted, with no failure attributable to this change; any pre-existing failure named with evidence that it fails identically without this change.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A LIFT CAN CHANGE BEHAVIOR WHILE CHANGING NO CHARACTERS: a bare name inside a moved body re-resolves in `runner_shared`'s namespace. `execute_item_core` counters this by rebinding 23 names off `driver_module` with `getattr(driver_module, "<name>", globals().get("<name>"))`; a name NOT rebound resolves to the shared definition. Any audit must check what each bare name RESOLVES to, not only the text.
- `tools/runner_fork_scan.py` IS THE COMMITTED CENSUS INSTRUMENT for host duplication, measures at ONE revision, and exits 0 always; its `normalize` (docstring-stripped `ast.unparse`) and `free_names` are the reusable primitives. New drift tooling reuses them rather than forking a third normalizer.
- DELIBERATE-STOP SEMANTICS (spec `c4gd2h` R18/R21/R22): a turn-interrupting stop (levels 3/4) is recorded on the item, the item status is decided in ONE place (`reconcile_disposition`'s deliberate-stop branch, returning `runner_stop.STOPPED_DISPOSITION` for both levels), and the exception propagates so `run_queue` breaks and remaining items stay `queued`. Indeterminacy is the record's `certainty` flag, never a separate item status.
- THE SUITE WAS TRIMMED (`19313eed`, `d3d800d4`): tests a plan's validation relied on may no longer exist. Re-check a cited test file exists before relying on it.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `877545fc` (`git rev-parse --short HEAD`), read-only, with throwaway probes under `/tmp/opencode/probe-liftaudit/` (`lift_enum.py`, `drift.py`, `resolve.py`, `callcheck.py`, `verbs.py`, `lifthead.py`, `values.py`, `queueprobe.py`). Symbol enumeration (`lift_enum.py`: top-level defs new in `C:runner_shared.py` vs `C^`):

    70a2059f NEW in runner_shared: ['RecoveryDisposition', 'ToolIdentityError', '_lane_commit_subjects', '_record_checkpoint_stop', '_record_forced_stop', 'assert_child_tool_identity', 'build_isolation_notice', 'build_verify_and_continue_notice', 'classify_recovery_disposition', 'evaluate_clean_base_for_launch', 'execute_item_core', 'pinned_child_env', 'pinned_module_argv', 'reconcile_disposition', 'record_item_spec_edits', 'route_recovery_turn', 'runner_package_root']
    12a5c05b NEW in runner_shared: ['StallWatchdog', '_budget_breach_recorder', '_default_stall_reaper', '_escalation_recorder', '_observe_between_turn_stop', '_record_deliberate_stop', 'driver_finalize', 'handle_stop_command', 'install_stop_triggers', 'locked_run', 'requeue_interrupted', 'run_lock', 'set_plan_approved', 'terminate_process']
    12a5c05b CHANGED in runner_shared: ['HostLabels', '_record_checkpoint_stop']

(`12a5c05b`'s "16 symbols" = these 14 new plus `build_isolation_notice` and `evaluate_clean_base_for_launch`, which already existed unused in `runner_shared` from `70a2059f` and whose host copies became wrappers.) `agy_runipd` at `70a2059f^` did not define `ToolIdentityError`, `assert_child_tool_identity`, `pinned_child_env`, `pinned_module_argv`, `record_item_spec_edits`, `RecoveryDisposition`, `_lane_commit_subjects`, `runner_package_root` (it imported them from `oc_runipd`), so those compare against the `oc_runipd` body only.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | BLOCKER | `runner_shared.execute_item_core`, the `except runner_stop.StopNowForce` and `except runner_stop.StopAtCheckpoint` handlers after `spawn_executor(` | DEFECT (still live; `ccu3k7` defect 5, wrongly reported fixed). Pre-lift both hosts set `item["status"], _ = reconcile_disposition(repo, item, run_dir, 1)` and `raise`; HEAD assigns `item["status"] = runner_stop.FORCED_DISPOSITION`/`STOPPED_DISPOSITION` and `return`s. `run_queue` therefore never sees the stop and dispatches the next IPD, and never sets `stopped_at_checkpoint`; level 4 leaves item status `unknown_outcome` instead of `interrupted`. Introduced by `70a2059f` (`git log -S"stopped cleanly at checkpoint"` -> only `70a2059f`); not changed by `13xo5k` (`ec116ce7`), whose V-03 certified the `return`. | `verbs.py`: `DIFF runner_stop.StopAtCheckpoint @ run_opencode: pre=[('raise', 'via-call'), ('raise', 'via-call')] head=[('return', 'direct')]` (same for `StopNowForce`, same on `agy_runipd`); `queueprobe.py` output quoted in Concern: `dispatched=['qa0001', 'qa0002'] rc=1` on both hosts, both levels |
| F-2 | HIGH | `runner_shared._record_forced_stop` fallback `git_status(repo)` | DEFECT (latent). Same resolved-signature class as `ccu3k7` defects 3/4: the call text is identical to the pre-lift host body but resolves to `runner_shared.git_status(repo, *, run_checked)`. Unreachable from shipped call sites (both pass `git_status_fn=git_status` since `ec116ce7`), but any new caller that omits the optional parameter silently records a TypeError string as the observed tree. | `callcheck.py`: `MISSING _record_forced_stop -> git_status(...) line 25056: missing ['run_checked']`; direct call returned `fallback git_state: <unobserved: git_status() missing 1 required keyword-only argument: 'run_checked'>` |
| F-3 | INFO (deferred) | `runner_shared.record_item_spec_edits` | DEFECT, OWNED ELSEWHERE. Shared body writes `item["spec_edits_reconciliation"]` with a different shape; `spec_edit_summary` reads `item["spec_edits"]`, so every item reports `not_finalized`. Introduced by `70a2059f` (`git log -S"spec_edits_reconciliation"` -> only `70a2059f`). Already filed as `tm5vnx` (open, `Blocks-Release: next`). | `drift.py` diff: `-    item['spec_edits'] = record` / `+    item['spec_edits_reconciliation'] = record`; probe: `keys written: ['id6', 'spec_edits_reconciliation']`, `summary: {... 'not_finalized': ['abc123']}` |
| F-4 | INFO (deferred) | `runner_shared.route_recovery_turn` | Shared copy calls `save_state(run_dir, state)` without the required `write_report` and resolves `classify_recovery_disposition` to the dead shared copy. NOT REACHED: `execute_item_core` rebinds `route_recovery_turn` off `driver_module`, and `AGY_IMPORTS_FROM_OC_RUNIPD` records why consolidation was tried and reverted. Its fix is entangled with `zt2b16`'s classifier, so it stays with that carrier. | `callcheck.py`: `MISSING route_recovery_turn -> save_state(...) line 24926: missing ['write_report']`; `resolution.py`: `rebound off driver_module: 23`, `route_recovery_turn` among them |
| F-5 | benign | `execute_item_core` `except StallTimeout` | Verb table shows pre `[('return','direct'), ('fall','-')]` vs head `[('return','direct')]` under key `@ run_opencode`: the pre-lift verifier-turn `StallTimeout` handler maps to key `@ spawn_verifier` at HEAD, where it falls through as before (now with an explicit `unknown_outcome` verdict added by `runverdict-06` `fzxfph`, an intentional later change). Not a divergence. | `verbs.py` HEAD table: `('StallTimeout', 'spawn_executor') [('return', 'direct')]`, `('StallTimeout', 'spawn_verifier') [('fall', '-')]` |
| F-6 | benign | `execute_item_core` `except DriverError` around `resolve_plan_path` | 6 handlers at HEAD vs 4 per pre-lift host: the self-finalize branch was split into lane and main-tree arms at the lift (each arm carries its own `current_plan_for_finalize = plan_path` and `pass` fallback), both identical to the pre-lift single arm; one more (`verify_absence_text(VERIFY_ABSENCE_PLAN_UNRESOLVABLE, ...)`) is intentional, added by `a0618dbe` "fix(runner): distinguish the reasons a verifier verdict is absent". | `70a2059f` already had 6 (`DriverError@resolve_plan_path at 70a2059f: 6`); handler first-statements listed by probe |
| F-7 | intentional | `_record_checkpoint_stop` | `git_status(repo)` -> required `git_status_fn(repo)`: `12a5c05b` (li44r9 commit message: "runner_shared._record_checkpoint_stop was an unreachable copy that called git_status() without its required run_checked"). Correct. | `drift.py` `[12a5c05b] _record_checkpoint_stop` diff |
| F-8 | intentional | `StallWatchdog`, `terminate_process`, `_escalation_recorder`, `handle_stop_command`, `install_stop_triggers`, `set_plan_approved`, `driver_finalize` | Host-varying reads became explicit injection: `reaper=` (`_default_stall_reaper` fallback), `sigint_grace=`/`sigterm_grace=`, `labels=` for `_detect_driver_command()` and `FULL_AUTO_ACTOR` (`labels.full_auto_actor`), `resolve_run_dir_fn=`, `argv_builder=`/`env_builder=`/`run_checked=`. All by `12a5c05b` per its message; host wrappers pass their own values (`hostcalls.py`: no host call to `runner_shared.X` is missing a required argument). `driver_finalize` additionally ends in `finalize_outcome(...)`, added by `98f82ed9` "fix(finidem)". | `drift.py` diffs; `hostcalls.py` -> `done` with no findings; `lifthead.py`: `driver_finalize: LIFT!=HEAD` only |
| F-9 | benign | `_record_forced_stop`, `_record_checkpoint_stop`, `build_isolation_notice`, `evaluate_clean_base_for_launch`, `_budget_breach_recorder`, `_observe_between_turn_stop`, `_record_deliberate_stop`, `locked_run`, `requeue_interrupted`, `run_lock` | Only a lazy in-body `from agent_workflows import runner_stop` (or `lane_containment`, `runner_shutdown`, `platform_lock`) and annotations loosened to `Any`. No behavior change. | `drift.py` diffs, each 1 to 2 lines |
| F-10 | none | `RecoveryDisposition`, `ToolIdentityError`, `_lane_commit_subjects`, `assert_child_tool_identity`, `pinned_child_env`, `pinned_module_argv`, `runner_package_root`, `route_recovery_turn` (oc) | Normalized body identical to the pre-lift host body at the lift commit AND at HEAD. | `drift.py`: `LIFT==PRE HEAD==PRE` for each |
| F-11 | none | module-level VALUE drift (the `FULL_AUTO_ACTOR` class) | No module-level constant read by any lifted body holds a different literal in `runner_shared` at HEAD than in the pre-lift host. | `values.py` -> `done` with no findings |
| F-12 | HIGH | `tests/` | No test in the tree drives a deliberate stop through `execute_item_core` or `run_queue`: `13xo5k`'s `tests/test_runner_stop_level3.py`/`level4.py` were deleted by `19313eed` "test: trim test suite". This is why F-1 is invisible to a green suite. `ccu3k7`'s cited guards `tests/test_hostdedup_identical_lift.py` and `tests/test_rununify_execute_item.py` no longer exist either. | `grep -ln "StopNowForce\|StopAtCheckpoint" tests/*.py` -> none; `git log --diff-filter=D -- tests/test_runner_stop_level3.py` -> `19313eed` |

## Proposed changes (ordered, validatable)

1. E-01 commits `tools/lift_drift_scan.py` (reusing `runner_fork_scan` primitives) and shows it reproduces F-1 and F-2 before any fix.
2. E-02 restores `reconcile_disposition` + `raise` in the two spawn-path stop handlers (F-1).
3. E-03 makes `_record_forced_stop`'s `git_status_fn` required and removes the broken fallback (F-2).
4. E-04 adds per-host, per-level `run_queue` tests that fail on today's code (F-1, F-12) plus the `_record_forced_stop` unit test (F-2).
5. E-05 adds a fast static guard for the resolved-signature and stop-handler-verb classes.
6. E-06 runs the bare suite.

## Deferred / out of scope (with reason)

- `classify_recovery_disposition` and `build_verify_and_continue_notice`: diverged, dead shared copies; owned by plan `recovone` (being authored concurrently).
  - Carrier: zt2b16
- `reconcile_disposition`: owned by plan `recovone` together with the two above.
  - Carrier: zt2b16
- `reconcile_item_on_interrupt`: owned by plan `intrecon` (`87jnym`).
  - Carrier: 2415x6
- `record_item_spec_edits` writes `spec_edits_reconciliation` while the reader reads `spec_edits` (F-3): already filed, `Blocks-Release: next`, and its fix is a record-shape decision, not a transcription revert.
  - Carrier: tm5vnx
- `runner_shared.route_recovery_turn`'s missing `write_report` (F-4): unreachable today, and fixing it without `zt2b16`'s classifier would produce a working wrapper around a classifier that raises `AttributeError`.
  - Carrier: zt2b16
- `ccu3k7`'s behavioral guard for every lifted body: E-04/E-05 cover the two classes that actually shipped defects (resolved signature, stop-handler verb); a general behavioral-equivalence harness per symbol is not proposed because F-10/F-11 show no further divergence to guard.
  - Carrier-Declined: the audit found no remaining divergence outside the carried items, and E-05's static guard covers the two defect classes observed.

## Scope check

- Over-scope: `agent_workflows/runner_shared.py` is touched ONLY in the two spawn-path stop handlers of `execute_item_core` (and the adjacent `finally:` comment if it describes them as returning) and in `_record_forced_stop`'s signature/body. Do NOT edit the verify/reconcile stop handlers, the `StallTimeout` handler, `record_item_spec_edits`, `route_recovery_turn`, or any of the four excluded symbols. No host module is in scope; if E-03's caller check finds a host wrapper that must pass `git_status_fn`, declare that host file in `- Scope-Paths:` before editing it.
- Under-scope: `tm5vnx` (F-3) is a live release blocker found by this same audit class and is NOT fixed here; it has its own carrier.

## Required tests / validation

- `python3 -m pytest tests/test_liftaudit_stop_halts_run.py tests/test_lift_drift_scan.py -o addopts="" -q` passing, and the `run_queue` tests shown FAILING with E-02 reverted.
- `python3 tools/lift_drift_scan.py 70a2059f 12a5c05b --exclude classify_recovery_disposition build_verify_and_continue_notice reconcile_disposition reconcile_item_on_interrupt` output pasted before and after the fix.
- Bare `python3 -m pytest`, summary line pasted.

## Spec / documentation sync

- N/A: E-02 restores behavior spec `c4gd2h` (R18/R21/R22) already requires; no spec text changes. If the executor finds `c4gd2h` describes the spawn-path handler as returning, STOP and report rather than editing the spec.

## Open questions

### OQ-01: Does restoring `raise` in the spawn-path handlers conflict with executed plan `13xo5k`'s recorded expectation?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE. `13xo5k`'s V-03 records "Spawn path: ... returns cleanly (no exception escapes)" as observed behavior, but that plan's scope was the `exit_code` crash, its own F-5 and conventions state the re-raise is deliberate (spec R5, "Do not convert either to a swallow"), and the pre-lift host bodies (`git show 70a2059f^:agent_workflows/oc_runipd.py`, `execute_item`) `raise` on the spawn path. The behavioral probe shows the `return` makes `run_queue` dispatch the next item, which `ccu3k7` names as the user-perceptible harm. So the `return` was certified, not decided; this plan restores the original. `13xo5k` is executed and is not edited.
- Carrier-Declined: resolved at authoring with no residual work.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 tools/lift_drift_scan.py 70a2059f 12a5c05b --exclude classify_recovery_disposition build_verify_and_continue_notice reconcile_disposition reconcile_item_on_interrupt` output run BEFORE E-02/E-03, showing the `StopAtCheckpoint`/`StopNowForce` spawn-path verb diffs on both hosts and `_record_forced_stop -> git_status(...) missing ['run_checked']`; paste the tool's import lines showing it reuses `runner_fork_scan`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff -- agent_workflows/runner_shared.py` for the two handlers showing `reconcile_disposition(repo, item, run_dir, 1)` and `raise`; paste the scanner re-run showing zero stop-handler verb diffs.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the new `_record_forced_stop` signature and the `grep -n "_record_forced_stop(" agent_workflows/*.py` caller list with each caller's `git_status_fn` argument; paste the scanner re-run showing `arity violations` no longer lists `_record_forced_stop`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_liftaudit_stop_halts_run.py -o addopts="" -q` summary showing all passing; then paste the same command's output with E-02 locally reverted showing the four `run_queue` tests FAILING on the dispatched-ids assertion (both ids dispatched); state that E-02 was restored before commit.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_lift_drift_scan.py -o addopts="" -q` passing; paste it FAILING once with a spawn-path `raise` reverted to `return` and once with `_record_forced_stop`'s `git_status_fn` default and `git_status(repo)` fallback restored; state both mutations were reverted.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the final summary line of a bare `python3 -m pytest` run (for example `N passed, M skipped ...`); name any failure and show it fails identically on a checkout without this change.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. The executor commits only the paths named in `- Scope-Paths:` via `aw commit <plan> -- <paths>`, never `git add -A`, and never pushes. Test claims must paste actual runner output. STOP CONDITIONS: if restoring `raise` breaks a test that asserts the spawn-path handler returns, report it (it certifies F-1) rather than weakening E-02; if a `_record_forced_stop` caller cannot supply `git_status_fn`, STOP rather than restoring a default. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence before the terminal transition, which the runner owns when it executes this plan in a lane and which the executor otherwise performs with `aw ipd finalize`.
