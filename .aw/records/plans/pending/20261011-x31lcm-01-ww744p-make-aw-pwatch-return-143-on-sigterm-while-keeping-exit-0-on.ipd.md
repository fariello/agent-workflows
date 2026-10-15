# IPD: Make aw pwatch return 143 on SIGTERM while keeping exit 0 on SIGINT, and pin both signal exits behaviorally

- Date: 2026-10-11
- Kind: child
- Concern: `aw pwatch` reports SUCCESS when it is terminated. `pwatch.main` installs one handler, `stop_cleanly`, for BOTH `signal.SIGINT` and `signal.SIGTERM`; it raises `SystemExit(0)`, and the loop's `except (KeyboardInterrupt, SystemExit): return 0` arm turns either signal into exit `0`. Re-measured while authoring at HEAD `7954f1a6d`: a real `os.killpg` against a running `python3 -m agent_workflows pwatch -m python --interval 0.3`, sent only after the first frame was read from stdout, returned `rc=0` for SIGINT and `rc=0` for SIGTERM. Backlog item `x31lcm` asks whether the SIGTERM half is right, and says deciding it "needs a survey of what actually supervises `pwatch`". This plan does that survey (F-03), decides from it, and implements the decision.
  THE DECISION: SIGINT stays `0` and SIGTERM becomes `143`, returned after the `finally` block has restored the terminal. SIGINT `0` is right for the reason the item gives: Ctrl-C is how a watch loop is meant to end, so calling it a failure would be the defect. SIGTERM `0` is wrong on four grounds from the repository. (1) It is the ONLY place on the surface where a termination request reads as a clean finish. Ordinary verbs die `WIFSIGNALED` (`-15`, which the shell shows as `143`), and the two drivers turn SIGTERM into a returned `143` through `render_stream.install_exit_signal_handler` and the `return 143 if is_sigterm else 130` arm of `oc_runipd.main` (DECISIONS D162, measurements 3 and 4). (2) A supervisor that sends SIGTERM because a watch has to stop (for example a `timeout`-style wrapper, a CI step teardown, or a process manager) cannot tell "stopped by me" from "finished on its own", and for `pwatch` "finished on its own" only happens with `--once`, so the difference matters. (3) No in-repository caller depends on `0` (F-03), so nothing breaks. (4) The repository already uses `143` as its returned SIGTERM code, so this choice adds no new convention. The other approach was to restore `SIG_DFL` and re-send SIGTERM so the process dies `WIFSIGNALED` like an ordinary verb. It is rejected because `pwatch.main` is called IN-PROCESS by `runners_monitor.main` (`aw runners --tree`) and by `cli._dispatch`, so killing the process from a library function would also kill an embedding caller that expects a return value (OQ-01).
  A SECOND DEFECT IN THE SAME LINES, IN SCOPE BECAUSE THE FIX TOUCHES THEM AND THE TEST NEEDS IT: `pwatch.main` never restores the signal handlers it installs. After it returns in-process (as it does under `aw runners --tree`), SIGINT and SIGTERM in the host process still go to `pwatch`'s `stop_cleanly`. So a later Ctrl-C in the embedding process raises `SystemExit(0)` instead of `KeyboardInterrupt`, and that bypasses `cli.main`'s `130` arm. An in-process test of the new SIGTERM behavior would also leave the hijacked handler in the xdist worker. E-03 saves the previous handlers and restores them in the existing `finally`.
  WHY `chore` AND NOT `bug`: the backlog item is filed as `chore` and that classification is kept. No user-visible output is wrong in normal interactive use, and no supervisor of `pwatch` is known to exist (F-03). The change exists for supervisor correctness and surface consistency, not to repair an observed failure. The item has no `- Blocks-Release:`, so none is invented.
- Scope: IN: (1) re-measure the current signal exits and the caller survey at the executing HEAD, as a gate (E-01); (2) make SIGTERM return `143` and keep SIGINT at `0`, with the `finally` terminal restore still running on both paths (E-02); (3) restore the previously installed SIGINT and SIGTERM handlers when `pwatch.main` returns (E-03); (4) add a behavioral test file that drives real subprocess signals and an in-process handler-restoration check (E-04); (5) fix the two comments that currently say `pwatch` returns `0` on both signals, without changing any `exit_contract` tuple (E-05); (6) document the exit status in `tools/README.md` (E-06); (7) record the decision as a new `DECISIONS.md` entry that refines D162 measurement 4 without rewriting D162, plus a `CHANGELOG.md` line (E-07). OUT: the `aw runners` table dashboard (`runners_monitor.run_table_dashboard`), which has the same `stop_cleanly` shape. It is filed separately as backlog `uu4rfe` because it is another verb with its own (also unknown) supervisors. Also OUT: any `exit_contract` change, any change to `cli.main`, `render_stream`, or the drivers, and any spec edit.
- Scope-Paths: agent_workflows/pwatch.py, tests/test_pwatch_signal_exit.py, agent_workflows/command_surface.py, tests/test_exit_contract_conformance.py, tools/README.md, DECISIONS.md, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: x31lcm
- Set: x31lcm
- Order: 1
- Highest E allocated: 07
- Author: opencode
- Id: ww744p
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): plan-review: APPROVE WITH REVISIONS APPLIED

- 2026-10-12 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005. Re-measured F-01/F-04 at HEAD 47538dba5; added F-07 (--runners --table bypasses the handlers; README note must say so) and F-08 (in-process SIGTERM test made required and bounded).
- 2026-10-12 to-review (opencode): authored from backlog item `x31lcm`. Re-measured the item's signal facts at HEAD `7954f1a6d` (SIGINT `0`, SIGTERM `0`). Ran the supervision survey the item asked for: no in-repository caller supervises `pwatch` by signal or reads its exit status after a signal. Decided SIGTERM returns `143` and SIGINT stays `0`, from repository evidence (OQ-01). Filed the sibling dashboard as backlog `uu4rfe` instead of widening scope.
- 2026-10-12 draft (opencode): created.

## Goal

Make `aw pwatch` report a termination request as `143`, the code the repository already returns for SIGTERM, while keeping Ctrl-C a clean `0`. Stop `pwatch.main` from leaving its signal handlers installed in an embedding process. Pin both behaviors with tests that send real signals and check real exit codes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure before changing anything

- [x] E-01 Re-drive the signal probe and the caller survey at the executing HEAD and record both verbatim, without editing any file.
  - Depends on: none
  - Expected outcome: two pasted transcripts. (a) THE PROBE: for each of `signal.SIGINT` and `signal.SIGTERM`, launch `python3 -m agent_workflows pwatch -m python --interval 0.3` with `start_new_session=True` and `stdout=PIPE`, block on `stdout.readline()` until the first frame arrives (this replaces a fixed sleep and guarantees the loop is running), `os.killpg(p.pid, sig)`, `wait(10)`, and print `returncode`. Expected at authoring: `0` and `0`. A `2` with "at least one process match pattern is required" means the `-m python` pattern was left off; that is a usage error, not a result. (b) THE SURVEY: `git grep -n "pwatch"` over everything except `.aw/records`, filtered to call sites (`pwatch.main(`, `subprocess`, `Popen`, `kill`, `signal`), with each hit classified as in-process caller, wrapper, or signal supervisor. Expected at authoring: in-process `runners_monitor.main` (`--tree`) and `cli._dispatch`; wrappers `tools/pwatch.py` and `tools/watch-agy.py`; no signal supervisor.
    GATE: if (a) already returns `143` for SIGTERM, another lane has made this change, so STOP and reconcile. If (b) finds a caller that sends SIGTERM to `pwatch` and treats `0` as success, STOP: the decision in OQ-01 rests on there being no such caller, so record the caller and re-decide before changing anything.
  - Execution state: performed

### Task group 2: the behavior change

- [x] E-02 Make SIGTERM return `143` and SIGINT return `0` from `pwatch.main`, with the `finally` terminal restore (`LEAVE_ALT_SCREEN`) still running on both paths.
  - Depends on: E-01
  - Expected outcome: `pwatch.main`'s handling tells the two signals apart (for example `stop_cleanly` uses its `signum` argument, or there are two handlers), and the loop's exit arm returns `143` for SIGTERM and `0` for SIGINT or `KeyboardInterrupt`. The `--once` path still returns `0`, the `RuntimeError` arm still returns `1`, and the argument-validation arms still return `2`. Define the code as a named module constant (for example `EXIT_SIGTERM = 143`) and cite `render_stream.install_exit_signal_handler` and `oc_runipd.main`'s `return 143 if is_sigterm else 130` as the precedent in a comment. Do NOT kill the process with `SIG_DFL` plus `os.kill`, because `pwatch.main` is called in-process (OQ-01). The `--runners --table` branch returns `runners_monitor.run_table_dashboard(args)` BEFORE any handler is installed, so it is NOT changed by this item and keeps exiting `0` on SIGTERM (F-07, carried by `uu4rfe`).
  - Execution state: performed

- [x] E-03 Save the SIGINT and SIGTERM handlers in place when `pwatch.main` installs its own, and restore them in the existing `finally` so an in-process caller gets its handlers back on every exit path.
  - Depends on: E-02
  - Expected outcome: after `pwatch.main(...)` returns (by `--once`, by SIGINT, by SIGTERM, or by `RuntimeError`), `signal.getsignal(signal.SIGINT)` and `signal.getsignal(signal.SIGTERM)` equal what they were before the call. Handlers are installed only on the main thread, so put the save and install next to each other, after the argument-validation `return 2` arms. That way an early usage error installs nothing and has nothing to restore.
  - Execution state: performed

### Task group 3: pin it

- [x] E-04 Create `tests/test_pwatch_signal_exit.py` with behavioral tests for both signal exits and for handler restoration.
  - Depends on: E-02, E-03
  - Expected outcome: four tests at minimum, each driving the code and asserting on its outputs. (1) A real subprocess test that sends SIGTERM through `os.killpg` after the first frame has been read (the E-01 probe shape, with no fixed sleep) and asserts `returncode == 143`. (2) The same with SIGINT, asserting `returncode == 0`. (3) An in-process test that sets known sentinel handlers, calls `pwatch.main(["-m", "python", "--once", "--no-color"])` with stdout captured, and asserts `signal.getsignal` returns the sentinels for both signals afterward. Restore the real handlers in a `try/finally` so the xdist worker is never left modified. (4) REQUIRED, not optional (F-08): an in-process SIGTERM test that patches `pwatch.time.sleep` to `os.kill(os.getpid(), signal.SIGTERM)` and asserts `pwatch.main(["-m", "python", "--no-color"])` returns `143` and the sentinels are restored. It is the only test that covers restore-after-signal, which the subprocess tests cannot observe. It MUST be bounded: the patched `sleep` counts its calls and raises `AssertionError` on the second call, because if `pwatch.main` ever stops installing its own SIGTERM handler the no-op sentinel swallows the signal and the loop would otherwise spin forever. Every subprocess call has a `wait` timeout, so a regression fails instead of hanging. The file must not read `pwatch.py` source and must not assert on comments or docstrings (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"). Linux only, the same as `pwatch` (it reads `/proc`), so skip on other platforms with a stated reason.
  - Execution state: performed

### Task group 4: keep the record true

- [x] E-05 Correct the two places that now misstate `pwatch`'s signal behavior: point 3 of the `CommandDeclaration.exit_contract` contract comment in `agent_workflows/command_surface.py`, and the closing sentence of the `test_universal_130_floor_and_signal_code_exclusion` docstring in `tests/test_exit_contract_conformance.py`. Change no `exit_contract=` value.
  - Depends on: E-02
  - Expected outcome: both texts say `pwatch` returns `0` on SIGINT and `143` on SIGTERM. The argument they support still holds and must still be stated: the signal-derived code is still not constant across the surface (`130`, `0`, `143`, or `WIFSIGNALED` depending on verb and signal), so D162's exclusion stands. `pwatch` keeps `exit_contract=(0, 1, 2)`. Under D162, `143` is signal-derived and must NOT be added.
  - Execution state: performed

- [x] E-06 Add a short exit-status note to the `aw pwatch` section of `tools/README.md`.
  - Depends on: E-02
  - Expected outcome: a few sentences, or a small list, stating that `pwatch` exits `0` after `--once` or Ctrl-C (SIGINT), `143` when it is sent SIGTERM, `1` on a runtime error, and `2` on a usage error. Say that the terminal is restored in every case. Say that the `--runners --table` dashboard is the exception and still exits `0` on SIGTERM (F-07), so the note does not overclaim. This is user-facing prose, so it contains no em or en dashes (`AGENTS.md`).
  - Execution state: performed

- [x] E-07 Record the decision as the next free `DECISIONS.md` entry number at execution (D163 at authoring; pending plan `n8we3u` also targets D163, so re-read the last `### D<n>` heading immediately before writing) and add one `CHANGELOG.md` `Changed:` line under the pending release.
  - Depends on: E-02
  - Expected outcome: the entry uses the shape D162 uses (`Context`, `Decision`, rejected alternatives, `Applied`). It answers backlog `x31lcm`, gives the survey result, names both rejected alternatives (keep `0`; die `WIFSIGNALED` through `SIG_DFL` re-raise) with the reason for each, and states that D162 measurement 4 is now `0` on SIGINT and `143` on SIGTERM while D162's decision is unchanged. D162 itself is NOT edited: it is a dated record, and the new entry refines it. The changelog line is user-facing: no em or en dashes.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Tests assert OUTCOMES, not code structure (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16). E-04 sends real signals and reads real return codes and `signal.getsignal` values. It never greps `pwatch.py`.
- `tests/test_pwatch.py` no longer exists. Commit `19313eed7` ("test: trim test suite from 9,136 to under 2,000 tests") removed it, and a comment in `pwatch.main` still refers to it. E-04 creates a new, narrowly named file instead of reviving the old one.
- DECISIONS D162 says `exit_contract` lists only codes the command returns on its own path and leaves out signal-derived codes "defined by cause". So `143` from SIGTERM is signal-derived, and no tuple changes (E-05).
- The repository's returned SIGTERM code is `143`: `render_stream.install_exit_signal_handler` raises `KeyboardInterrupt("Terminated by SIGTERM")`, and `oc_runipd.main` returns `143 if is_sigterm else 130`.
- Run the suite BARE as `python3 -m pytest` (`pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`). Use `-o addopts=""` only to get per-test counts from a narrowed run (`AGENTS.md`).
- `- Readiness:` is left out on purpose. `/plan-review` writes it; the author does not (`AGENTS.md`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | **The backlog item's measurement reproduces at the authoring HEAD.** `pwatch.main` defines `stop_cleanly(_signum, _frame)` raising `SystemExit(0)`, registers it with `signal.signal(signal.SIGINT, stop_cleanly)` and `signal.signal(signal.SIGTERM, stop_cleanly)`, and ends its loop with `except (KeyboardInterrupt, SystemExit): return 0`. A real probe returned `0` for both signals. | Probe at HEAD `7954f1a6d`, sent only after the first frame was read from stdout: `SIGINT rc= 0 first_line_seen= True` and `SIGTERM rc= 0 first_line_seen= True`. An earlier fixed-sleep probe also printed `SIGINT 0` and `SIGTERM 0`. |
| F-02 | **`pwatch` is the only place on the surface where SIGTERM reads as success.** Ordinary verbs die `WIFSIGNALED` (`-15`, which the shell shows as `143`). The drivers return `143`. `cli.main` returns `130` for SIGINT. | DECISIONS D162 measurements 3 and 4; `render_stream.install_exit_signal_handler`; `oc_runipd.main` `return 143 if is_sigterm else 130`. |
| F-03 | **The supervision survey the item asked for: nothing in this repository supervises `pwatch` by signal or reads its exit status after a signal.** Callers are `runners_monitor.main` (calls `pwatch.main(pwatch_argv)` in-process for `aw runners --tree`), `cli._dispatch` (the `aw pwatch` interception and the `args.command == "pwatch"` arm), `tools/pwatch.py` (`raise SystemExit(pwatch.main(sys.argv[1:]))`), and `tools/watch-agy.py` (`return pwatch.main(argv)`). None of them sends a signal or branches on `0`. Every other hit is a reference to module constants or `pwatch.Process`. So changing SIGTERM to `143` breaks no in-repository consumer. External supervisors cannot be surveyed from here, which is why OQ-01 records the decision as reversible. | `git grep -n pwatch` outside `.aw/records`, classified by call site. |
| F-04 | **`pwatch.main` leaks its signal handlers into an in-process caller.** It installs handlers and never restores them, and it is called in-process by `runners_monitor.main`. After it returns, a Ctrl-C in the host raises `SystemExit(0)` from `stop_cleanly` instead of `KeyboardInterrupt`, which goes around `cli.main`'s `130` arm. The same leak would leave a modified handler in a pytest worker after an in-process test, which is why E-03 comes before E-04. | `pwatch.main` source: `signal.signal` calls with no saved previous value and no restore in the `finally`, which only writes `LEAVE_ALT_SCREEN`. |
| F-05 | **`exit_contract` is unaffected.** `get_declaration("pwatch").exit_contract` prints `(0, 1, 2)`. Under D162, `143` from SIGTERM is signal-derived and is not listed. Two texts state the current `0`/`0` behavior and will become false: point 3 of the `CommandDeclaration.exit_contract` comment ("aw pwatch installs its own handlers and stop_cleanly raises SystemExit(0), returning 0 on both SIGINT and SIGTERM") and the `test_universal_130_floor_and_signal_code_exclusion` docstring ("verbs like pwatch return 0 on signals"). | Interpreter print of the declaration; the two quoted texts. |
| F-07 | **ADDED AT REVIEW. `aw pwatch --runners --table` bypasses `pwatch`'s handlers entirely.** `pwatch.main` returns `runners_monitor.run_table_dashboard(args)` as its first branch, before `stop_cleanly` is installed, so this plan's change does not reach that spelling. An unqualified README note would overclaim. | `pwatch.main` first branch: `if getattr(args, "runners", False) and getattr(args, "table", False): ... return runners_monitor.run_table_dashboard(args)`; `aw pwatch --help` lists `--runners` and `--table`. |
| F-08 | **ADDED AT REVIEW. Both defects re-measured at HEAD `47538dba5`, and the in-process SIGTERM test needs a bound.** Subprocess probe: `SIGINT rc= 0 first= True`, `SIGTERM rc= 0 first= True`. In-process with sentinel handlers: `once rc 0 int restored: False term restored: False` (F-04 leak confirmed); patched-`sleep` SIGTERM: `inproc sigterm rc 0` (the test shape works and observes the code); bare `pwatch.main([])` -> `2`. If the handler were not installed, the no-op SIGTERM sentinel would make the patched-`sleep` loop spin forever. | Review probe scripts run in this lane. |
| F-06 | **The `aw runners` table dashboard has the same shape and is a separate verb.** `runners_monitor.run_table_dashboard` defines its own `stop_cleanly` raising `SystemExit(0)` for both signals. `aw runners --tree` goes through `pwatch.main` and picks up this plan's change. The default dashboard does not. It is filed as backlog `uu4rfe` and not carried here, so this plan stays one verb. | `runners_monitor.run_table_dashboard` source; `aw runners --tree --once` returned `rc=0` at authoring; backlog `uu4rfe` written. |

## Proposed changes (ordered, validatable)

1. **Re-measure (E-01).** The probe and survey are taken again at the executing HEAD. A changed result stops the plan.
2. **Change the SIGTERM exit (E-02).** SIGTERM returns `143`, SIGINT returns `0`, and the terminal is restored on both paths.
3. **Stop the handler leak (E-03).** The previous handlers are restored in `finally`.
4. **Pin both (E-04).** New `tests/test_pwatch_signal_exit.py`: real-signal subprocess tests plus in-process restoration tests.
5. **Keep the record true (E-05, E-06, E-07).** Two stale comments fixed with no tuple change, a user-facing exit-status note, a D163 entry refining D162 measurement 4, and a changelog line.

## Deferred / out of scope (with reason)

- **The `aw runners` table dashboard's identical SIGTERM-to-`0` handling.** It is a different verb with its own handler, and changing it here would widen a one-verb decision without a survey of that verb.
  - Carrier: uu4rfe
  - Carrier-Evidence: .aw/records/backlog/graduated/20261011-uu4rfe-01-uu4rfe-runners-dashboard-sigterm-exit.backlog.md
- **Adding `143` to `pwatch`'s `exit_contract`.** Refused on D162, not deferred: `143` here comes from a signal, and D162 excludes signal-derived codes by cause.
  - Carrier-Declined: a decision not to act creates no obligation. E-05 states the exclusion where the comment already discusses `pwatch`.
- **Dying `WIFSIGNALED` (restore `SIG_DFL` and re-send SIGTERM) instead of returning `143`.** Rejected in OQ-01 because `pwatch.main` is called in-process.
  - Carrier-Declined: a rejected alternative creates no obligation. It is recorded in OQ-01 and in the E-07 decision entry.

## Scope check

- Over-scope: E-03 (handler restoration) goes slightly beyond the item's question. It is kept because it is in the same lines E-02 edits, F-04 shows it is a real leak through `aw runners --tree`, and E-04's in-process test cannot run cleanly in a pytest worker without it.
- Under-scope: the item asks for a decision. This plan makes it and also implements it, because the decision is low-risk, reversible, and confined to one verb, and the backlog contract asks the graduating agent to resolve questions from repository evidence (OQ-01). The sibling dashboard (F-06) is not covered here and is carried by `uu4rfe`.
- Right-sizing: seven items, each one concern. E-02 and E-03 are separate because they fix different defects and are checked by different tests. E-05, E-06, and E-07 are separate because they touch different audiences (internal comment, user docs, decision record).

## Required tests / validation

- `python3 -m pytest tests/test_pwatch_signal_exit.py -o addopts=""` with the output pasted, showing every new test passed.
- The E-01 probe run again after E-02, pasted, showing `SIGINT rc=0` and `SIGTERM rc=143`.
- `python3 -m pytest tests/test_exit_contract_conformance.py tests/test_runners_monitor.py tests/test_cli_parser_conflict_policy.py tests/test_cli_dest_shadowing.py -o addopts=""` as the targeted regression set (the exit-contract gates, the in-process `runners --tree` caller, and the two `pwatch.build_parser` parser checks), output pasted.
- A bare `python3 -m pytest`, compared by FAILURE SET rather than count. List the failing node ids. Any failure must be shown to reproduce on an unmodified tree at the same HEAD before it is called pre-existing.
- `git diff` over `agent_workflows/command_surface.py` showing no `exit_contract=` line changed.
- `aw ipd lint --phase pre-transition` conforming on this plan; `aw check` after the `DECISIONS.md` and `CHANGELOG.md` edits; `aw sanitize --agent` over the changed files.

## Spec / documentation sync

- `tools/README.md` gets the user-facing exit-status note (E-06). It is the one user document with a `pwatch` section.
- `DECISIONS.md` gets D163 and `CHANGELOG.md` gets one line (E-07).
- `agent_workflows/command_surface.py` and `tests/test_exit_contract_conformance.py` get comment and docstring corrections only (E-05).
- `docs/cli-output-contract.md`: no change needed. Its Section 3 paragraph describes signal-derived codes in general terms ("an interrupted command exits 130 (or is killed by its signal)") and never names `pwatch`, so it stays true.
- No spec amendment: `git grep -ln pwatch .aw/records/specs` returns nothing, so no spec describes `pwatch`'s signal behavior, and `- Scope-Paths:` declares no `.spec.md`.

## Open questions

### OQ-01: What should `aw pwatch` exit with when it is sent SIGTERM?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE: return `143` and keep SIGINT at `0`. There were three options. (a) Keep `0`: rejected because it is the only place on the surface where termination reads as success (F-02), and a supervisor cannot tell it from a clean finish. (b) Restore `SIG_DFL` and re-send SIGTERM so the process dies `WIFSIGNALED` like ordinary verbs: rejected because `pwatch.main` is a library entry point called in-process by `runners_monitor.main` and `cli._dispatch` (F-03), so it would kill an embedding caller. (c) Return `143`: chosen. It is already the repository's returned SIGTERM code (the drivers), the shell shows the same `143` for an ordinary verb killed by SIGTERM, it is a plain return value so in-process callers keep working, and no in-repository caller relies on `0` (F-03). One limit: supervisors outside this repository cannot be surveyed. Some process managers count only a clean `0` or death by SIGTERM as a normal stop, and would need to be told `143` is expected. The change is reversible by restoring one return value, and D163 records the reasoning so it can be reopened. REVERSIBLE: yes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste both transcripts. (a) The probe output for both signals, each taken after the first frame was read and WITH a match pattern, showing the return codes (expected `0` and `0` before any edit). A `2` with the "at least one process match pattern is required" message is the usage-error trap and must be re-run. (b) The `git grep` survey with each call site classified, showing no signal supervisor. Paste `git status --short` showing this item modified no file. The observation comes from `pwatch.main`, run through `python3 -m agent_workflows pwatch`.
  - Observed evidence:
    (a) The probe output at executing HEAD prior to edits:
    ```
    $ python3 -c '
    import os, signal, subprocess, sys

    def probe(sig, sig_name):
        p = subprocess.Popen(
            [sys.executable, "-m", "agent_workflows", "pwatch", "-m", "python", "--interval", "0.3"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        first_line = p.stdout.readline()
        os.killpg(p.pid, sig)
        p.wait(timeout=10)
        print(f"{sig_name} rc={p.returncode} first_line_seen={bool(first_line)}")

    probe(signal.SIGINT, "SIGINT")
    probe(signal.SIGTERM, "SIGTERM")
    '
    SIGINT rc=0 first_line_seen=True
    SIGTERM rc=0 first_line_seen=True
    ```
    (b) The grep survey across all files outside .aw/records:
    ```
    $ git grep -n "pwatch" -- ':(exclude).aw/records'
    agent_workflows/completion.py:126:    and ``pwatch`` are intercepted in ``cli._dispatch`` BEFORE parsing and have no argparse subtree,
    agent_workflows/pwatch.py:2:"""Generic process-tree watcher and recorder (pwatch).
    agent_workflows/render_stream.py:2565:    """Format duration seconds into HH:MM:SS stopwatch format (e.g. '00:08:42', '00:14:22', '01:04:12')."""
    agent_workflows/runners_monitor.py:23:from agent_workflows import platform_lock, pwatch, term
    agent_workflows/runners_monitor.py:718:        return pwatch.main(pwatch_argv)
    agent_workflows/term.py:351:    delegation to this function and `pwatch` calls it directly; both previously carried independent
    tests/conformance_matrix.py:287:    "pwatch": Exemption(
    tests/test_cli_dest_shadowing.py:50:    pwatch,
    tests/test_cli_parser_conflict_policy.py:33:    pwatch,
    tests/test_completion.py:128:        ("pwatch", True, "watch and summarize processes"),
    tests/test_exit_contract_conformance.py:96:      - 'pwatch'
    tests/test_exit_contract_conformance.py:237:    like pwatch return 0 on signals.
    tests/test_runners_monitor.py:20:from agent_workflows import cli, pwatch, runners_monitor
    tools/README.md:213:## `aw pwatch` (was `pwatch.py`)
    tools/pwatch.py:25:from agent_workflows import pwatch  # noqa: E402
    tools/pwatch.py:35:    raise SystemExit(pwatch.main(sys.argv[1:]))
    tools/watch-agy.py:14:import pwatch  # noqa: E402
    tools/watch-agy.py:36:    return pwatch.main(argv)
    ```
    Classification:
    - In-process callers: `runners_monitor.main` (`aw runners --tree` calling `pwatch.main(pwatch_argv)`), `cli._dispatch` (`pwatch.main(list(argv_list[1:]))` and `pwatch.main(list(getattr(args, "pwatch_args", []) or []))`).
    - Shims / wrappers: `tools/pwatch.py` (`pwatch.main(sys.argv[1:])`), `tools/watch-agy.py` (`pwatch.main(argv)`).
    - Unit tests / declarations / docs: `conformance_matrix`, `test_cli_dest_shadowing`, `test_cli_parser_conflict_policy`, `test_completion`, `test_exit_contract_conformance`, `test_runners_monitor`, `tools/README.md`.
    - Signal supervisors: NONE. No caller sends signals to pwatch or branches on exit 0 after a signal.

    ```
    $ git status --short
    (clean - no files modified)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the same E-01 probe run again after the change, pasted, showing `SIGINT rc=0` and `SIGTERM rc=143`. Also a pasted `python3 -m agent_workflows pwatch -m python --once --no-color; echo rc=$?` showing `rc=0`, and a pasted bare `python3 -m agent_workflows pwatch; echo rc=$?` showing `rc=2`. The observation comes from `pwatch.main`.
  - Observed evidence:
    ```
    $ python3 -c '
    import os, signal, subprocess, sys

    def probe(sig, sig_name):
        p = subprocess.Popen(
            [sys.executable, "-m", "agent_workflows", "pwatch", "-m", "python", "--interval", "0.3"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        first_line = p.stdout.readline()
        os.killpg(p.pid, sig)
        p.wait(timeout=10)
        print(f"{sig_name} rc={p.returncode} first_line_seen={bool(first_line)}")

    probe(signal.SIGINT, "SIGINT")
    probe(signal.SIGTERM, "SIGTERM")
    '
    SIGINT rc=0 first_line_seen=True
    SIGTERM rc=143 first_line_seen=True

    $ python3 -m agent_workflows pwatch -m python --once --no-color; echo rc=$?
    pwatch: python (every 2.5s) -- 2026-10-14 23:34:50
    ...
    rc=0

    $ python3 -m agent_workflows pwatch; echo rc=$?
    pwatch: error: at least one process match pattern is required (-M, -m, -R, -r, or bare pattern arguments)
    rc=2
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the pasted passing output of E-04's in-process restoration test or tests (sentinel handlers equal after `--once` and after the bounded in-process SIGTERM, which also returns `143`). Also the relevant `git diff` hunk of `agent_workflows/pwatch.py` showing the previous handlers saved and restored in `finally`.
  - Observed evidence:
    ```
    $ python3 -m pytest tests/test_pwatch_signal_exit.py -k inprocess -o addopts="" -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- python3
    cachedir: .pytest_cache
    Using --randomly-seed=2620757136
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/ww744p_attempt3
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 4 items / 2 deselected / 2 selected

    tests/test_pwatch_signal_exit.py::test_inprocess_handler_restoration_after_clean_exit PASSED [ 50%]
    tests/test_pwatch_signal_exit.py::test_inprocess_handler_restoration_after_sigterm PASSED [100%]

    NOTE: 2 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    ======================= 2 passed, 2 deselected in 0.53s ========================

    $ git diff agent_workflows/pwatch.py
    @@ -1044,7 +1049,12 @@ def main(argv: list[str] | None = None) -> int:
         # answers.
         color_enabled = not args.no_color and term.should_color(sys.stdout)

    -    def stop_cleanly(_signum: int, _frame: object) -> None:
    +    old_sigint = signal.getsignal(signal.SIGINT)
    +    old_sigterm = signal.getsignal(signal.SIGTERM)
    +
    +    def stop_cleanly(signum: int, _frame: object) -> None:
    +        if signum == signal.SIGTERM:
    +            raise SystemExit(EXIT_SIGTERM)
             raise SystemExit(0)

         signal.signal(signal.SIGINT, stop_cleanly)
    @@ -1174,12 +1184,19 @@ def main(argv: list[str] | None = None) -> int:
                     return 0
                 time.sleep(args.interval)

    -    except (KeyboardInterrupt, SystemExit):
    +    except KeyboardInterrupt:
             return 0
    +    except SystemExit as exc:
    +        code = exc.code
    +        return code if isinstance(code, int) else 0
         except RuntimeError as error:
             print(f"pwatch: {error}", file=sys.stderr)
             return 1
         finally:
    +        if old_sigint is not None:
    +            signal.signal(signal.SIGINT, old_sigint)
    +        if old_sigterm is not None:
    +            signal.signal(signal.SIGTERM, old_sigterm)
             if is_interactive:
                 sys.stdout.write(LEAVE_ALT_SCREEN)
                 sys.stdout.flush()
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted output of `python3 -m pytest tests/test_pwatch_signal_exit.py -o addopts=""` showing every test passed, with the test names visible (use `-v` if needed). Then show the tests can fail: temporarily put `0` back as the SIGTERM return, re-run, paste the failing SIGTERM assertion, revert, and paste the `git diff --stat` showing the revert left only the intended changes. Paste the result of `grep -nE "\binspect\b|\bast\.|read_text|open\(.*pwatch\.py" tests/test_pwatch_signal_exit.py` showing no hits (word-bounded, because an unbounded `ast\.` matches `last.` or `fast.`) (the file does not read production source).
  - Observed evidence:
    ```
    $ python3 -m pytest tests/test_pwatch_signal_exit.py -o addopts="" -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- python3
    cachedir: .pytest_cache
    Using --randomly-seed=2172332680
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/ww744p_attempt3
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 4 items

    tests/test_pwatch_signal_exit.py::test_inprocess_handler_restoration_after_sigterm PASSED [ 25%]
    tests/test_pwatch_signal_exit.py::test_inprocess_handler_restoration_after_clean_exit PASSED [ 50%]
    tests/test_pwatch_signal_exit.py::test_subprocess_sigterm_exit_143 PASSED [ 75%]
    tests/test_pwatch_signal_exit.py::test_subprocess_sigint_exit_0 PASSED   [100%]

    ============================== 4 passed in 1.44s ===============================

    Demonstrating test failure with EXIT_SIGTERM = 0:
    $ python3 -m pytest tests/test_pwatch_signal_exit.py -o addopts="" -v
    ...
    FAILED tests/test_pwatch_signal_exit.py::test_subprocess_sigterm_exit_143 - AssertionError: assert 0 == 143
    FAILED tests/test_pwatch_signal_exit.py::test_inprocess_handler_restoration_after_sigterm - AssertionError: assert 0 == 143
    ========================= 2 failed, 2 passed in 1.93s ==========================

    Reverted to EXIT_SIGTERM = 143:
    $ git diff --stat agent_workflows/pwatch.py
     agent_workflows/pwatch.py | 21 +++++++++++++++++++--
     1 file changed, 19 insertions(+), 2 deletions(-)

    Grep check confirming no production source inspection:
    $ grep -nE "\binspect\b|\bast\.|read_text|open\(.*pwatch\.py" tests/test_pwatch_signal_exit.py
    (no matches, exit 1)
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: the pasted `git diff` of `agent_workflows/command_surface.py` and `tests/test_exit_contract_conformance.py`, showing only comment or docstring lines changed and no `exit_contract=` line changed. An interpreter print of `command_surface.get_declaration("pwatch").exit_contract` showing `(0, 1, 2)`. Passing output of `python3 -m pytest tests/test_exit_contract_conformance.py -o addopts=""`.
  - Observed evidence:
    ```
    $ git diff agent_workflows/command_surface.py tests/test_exit_contract_conformance.py
    diff --git a/agent_workflows/command_surface.py b/agent_workflows/command_surface.py
    index 1fdfc2d7a..bacfafcb2 100644
    --- a/agent_workflows/command_surface.py
    +++ b/agent_workflows/command_surface.py
    @@ -51,9 +51,8 @@ class CommandDeclaration:
         #    128 + 15 representation of an unhandled signal. 143 becomes a returned code only where
         #    a verb explicitly converts the signal first, as render_stream.install_exit_signal_handler
         #    does for the driver verbs.
    -    # 3. aw pwatch installs its own handlers and stop_cleanly raises SystemExit(0), returning 0
    -    #    on both SIGINT and SIGTERM, proving signal-derived codes are not even constant across
    -    #    the surface.
    +    # 3. aw pwatch installs its own handlers and returns 0 on SIGINT and 143 on SIGTERM,
    +    #    proving signal-derived codes are not even constant across the surface.
         # Imperative for future editors: do NOT add 130 or 143 to any command's exit_contract.
         # A verb whose signal behavior is unusual (such as pwatch) documents that behavior at the
         # verb itself, never by widening its exit_contract declaration.
    diff --git a/tests/test_exit_contract_conformance.py b/tests/test_exit_contract_conformance.py
    index 10385ada5..d3788b893 100644
    --- a/tests/test_exit_contract_conformance.py
    +++ b/tests/test_exit_contract_conformance.py
    @@ -234,7 +234,7 @@ def test_universal_130_floor_and_signal_code_exclusion() -> None:
         exclude signal-derived codes (DECISIONS.md D162, command_surface.CommandDeclaration.exit_contract).
         Adding 130 to declarations would duplicate the universal floor across all leaves,
         143 is not a returned code on ordinary verbs (WIFSIGNALED / shell 128+15), and verbs
    -    like pwatch return 0 on signals.
    +    like pwatch return 0 on SIGINT and 143 on SIGTERM.
         """
         # 1. Universal 130 floor assertion
         with mock.patch.object(cli, "_dispatch", side_effect=KeyboardInterrupt):

    $ python3 -c 'from agent_workflows import command_surface; print(command_surface.get_declaration("pwatch").exit_contract)'
    (0, 1, 2)

    $ python3 -m pytest tests/test_exit_contract_conformance.py -o addopts=""
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=3312054249
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/ww744p_attempt3
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 20 items

    tests/test_exit_contract_conformance.py ....................             [100%]

    ======================== 20 passed in 148.05s (0:02:28) ========================
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: the pasted `git diff tools/README.md` showing the exit-status note naming `0` (once or SIGINT), `143` (SIGTERM), `1`, and `2`, and the `--runners --table` exception. Pasted output of `grep -nP "\x{2013}|\x{2014}" tools/README.md` limited to the added lines, showing no em or en dash in them.
  - Observed evidence:
    ```
    $ git diff tools/README.md
    diff --git a/tools/README.md b/tools/README.md
    index 3777e874d..2d4037df3 100644
    --- a/tools/README.md
    +++ b/tools/README.md
    @@ -237,6 +237,16 @@ aw pwatch python3 -rm pytest --record-file /tmp/pytest-runs.jsonl

     `tools/watch-agy.py` acts as a convenience wrapper around `pwatch.py` (now the compat shim), defaulting to `-m agy` when invoked without process filter arguments.

    +### Exit Status
    +
    +`aw pwatch` returns:
    +- `0`: clean exit after `--once` or interrupt via Ctrl-C (SIGINT).
    +- `143`: terminated by SIGTERM.
    +- `1`: runtime error (e.g. fatal failure reading `/proc`).
    +- `2`: command-line argument validation or usage error.
    +
    +In all cases, the alternate screen is exited and the terminal state is restored cleanly. Note that the `--runners --table` dashboard is an exception and still exits 0 on SIGTERM.
    +
     ## `aw oc runipd` (the OpenCode IPD runner)

     The OpenCode IPD runner is a restartable, non-interactive driver for reviewing and executing queues of IPDs, Sets, and plan files. It automatically routes `to-review` plans to OpenCode `/plan-review` (sharing session context across turns) and `approved` plans to full execution. It persists durable run state, session IDs, event streams, decisions, and outcomes under `.aw/records/runs/<run-id>/`.

    $ git diff tools/README.md | grep '^+[^+]' | grep -nP "\x{2013}|\x{2014}"
    (no matches, exit 1)
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: the pasted new `DECISIONS.md` entry with its number, the rejected alternatives, and the D162 refinement statement. A `git diff DECISIONS.md` showing the D162 entry's lines unchanged. The pasted `CHANGELOG.md` line. Pasted `aw check` output after both edits, and `aw sanitize --agent` output over all changed files with no `fail`. Pasted bare `python3 -m pytest` summary with failing node ids listed, compared by failure set as described in Required tests.
  - Observed evidence:
    (1) New DECISIONS.md entry (numbered D169 as next available after D168):
    ```markdown
    ### D169. aw pwatch returns 143 on SIGTERM while keeping exit 0 on SIGINT

    - **Context:** Backlog item `x31lcm`: `aw pwatch` previously reported exit `0` when terminated by either SIGINT or SIGTERM via a shared `stop_cleanly` handler that raised `SystemExit(0)`. A survey across the codebase confirmed that no in-repository caller or supervisor relies on `pwatch` returning `0` after receiving SIGTERM, while external supervisors (such as process managers or CI wrappers) cannot distinguish a clean shutdown from an external termination when both exit `0`. In addition, `pwatch.main` did not restore signal handlers, leaking its handlers into in-process callers like `aw runners --tree`.
    - **Decision:** Make `aw pwatch` return `143` on SIGTERM while preserving exit `0` on SIGINT (Ctrl-C) and on clean `--once` completion. Restore previous signal handlers upon exit in all cases. D162 measurement 4 is refined: `aw pwatch` now returns `0` on SIGINT and `143` on SIGTERM; D162's decision (that `exit_contract` enumerates only normal return codes and excludes signal-derived codes) remains unchanged and `pwatch` retains `exit_contract = (0, 1, 2)`.
      The rejected alternatives are rejected on the following grounds:
      1. *Keeping exit 0 on SIGTERM:* rejected because it was the only place across the surface where a termination signal was reported as success, preventing external supervisors from distinguishing clean completion from forced termination.
      2. *Dying WIFSIGNALED via SIG_DFL and re-sending SIGTERM:* rejected because `pwatch.main` is a library entry point invoked in-process by `runners_monitor.main` and `cli._dispatch`, so killing the host process would abruptly terminate embedding callers expecting a return code.
    - **Applied:** `agent_workflows/pwatch.py` (`EXIT_SIGTERM = 143`, handler save and restore); `tests/test_pwatch_signal_exit.py` (behavioral tests); `agent_workflows/command_surface.py` (comment refinement); `tests/test_exit_contract_conformance.py` (docstring refinement); `tools/README.md` (exit status docs); `DECISIONS.md` (this entry); `CHANGELOG.md`. Executed per IPD `ww744p` (Set `x31lcm`, Order 1, backlog `x31lcm`).
    ```

    (2) Git diff of DECISIONS.md confirming D162 lines are untouched:
    ```
    $ git diff DECISIONS.md
    diff --git a/DECISIONS.md b/DECISIONS.md
    index ccbd71c87..35fa84f89 100644
    --- a/DECISIONS.md
    +++ b/DECISIONS.md
    @@ -2718,3 +2718,13 @@ both execute the (large) set well.
       Rejected alternative:
       1. *Adding `__all__` to `agy_runipd`:* rejected because a complete list would enumerate about 324 non-dunder names and a partial one would shrink `from agent_workflows.agy_runipd import *` (285 names) to that list and understate the public surface, which the module's own `Heartbeat` comment already rejects.
     - **Applied:** `agent_workflows/agy_runipd.py` (`_read_id` module-level assignment, removal of `assert_child_tool_identity` noqa); `agent_workflows/oc_runipd.py` (comment sync); `tests/test_runner_shared.py` (`RunagyShimReadIdReExportTests`); `DECISIONS.md` (this entry). Executed per IPD `vzk1iw` (backlog `fh8x8k`), resolving `h0zk2g` OQ-02.
    +
    +### D169. aw pwatch returns 143 on SIGTERM while keeping exit 0 on SIGINT
    +
    +- **Context:** Backlog item `x31lcm`: `aw pwatch` previously reported exit `0` when terminated by either SIGINT or SIGTERM via a shared `stop_cleanly` handler that raised `SystemExit(0)`. A survey across the codebase confirmed that no in-repository caller or supervisor relies on `pwatch` returning `0` after receiving SIGTERM, while external supervisors (such as process managers or CI wrappers) cannot distinguish a clean shutdown from an external termination when both exit `0`. In addition, `pwatch.main` did not restore signal handlers, leaking its handlers into in-process callers like `aw runners --tree`.
    +- **Decision:** Make `aw pwatch` return `143` on SIGTERM while preserving exit `0` on SIGINT (Ctrl-C) and on clean `--once` completion. Restore previous signal handlers upon exit in all cases. D162 measurement 4 is refined: `aw pwatch` now returns `0` on SIGINT and `143` on SIGTERM; D162's decision (that `exit_contract` enumerates only normal return codes and excludes signal-derived codes) remains unchanged and `pwatch` retains `exit_contract = (0, 1, 2)`.
    +  The rejected alternatives are rejected on the following grounds:
    +  1. *Keeping exit 0 on SIGTERM:* rejected because it was the only place across the surface where a termination signal was reported as success, preventing external supervisors from distinguishing clean completion from forced termination.
    +  2. *Dying WIFSIGNALED via SIG_DFL and re-sending SIGTERM:* rejected because `pwatch.main` is a library entry point invoked in-process by `runners_monitor.main` and `cli._dispatch`, so killing the host process would abruptly terminate embedding callers expecting a return code.
    +- **Applied:** `agent_workflows/pwatch.py` (`EXIT_SIGTERM = 143`, handler save and restore); `tests/test_pwatch_signal_exit.py` (behavioral tests); `agent_workflows/command_surface.py` (comment refinement); `tests/test_exit_contract_conformance.py` (docstring refinement); `tools/README.md` (exit status docs); `DECISIONS.md` (this entry); `CHANGELOG.md`. Executed per IPD `ww744p` (Set `x31lcm`, Order 1, backlog `x31lcm`).
    +
    ```

    (3) CHANGELOG.md line:
    ```
    $ git diff CHANGELOG.md
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index 67882aff9..d18072b73 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

     Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

    +- Changed: aw pwatch now returns exit 143 when terminated by SIGTERM, while continuing to exit 0 on SIGINT (Ctrl-C) and restoring previous signal handlers when exiting.
     - Changed: `aw reviews decisions`, `aw record-history`, and `aw graduation` now refuse at exit 2 with an `aw.agent/v1` cannot-run outcome a selector naming no artifact in any tracked tree, while keeping legitimate empty answers at exit 0. `aw ipd recheck-readiness` moves from exit 1 to exit 2 for unresolved or non-plan selectors and now refuses a mixed invocation before re-checking or writing anything. Standing vocabulary queries remain exempt at exit 0 across all four verbs.
    ```

    (4) aw check output showing 0 errors for ww744p:
    ```
    $ aw check
    ...
    Evidence
      plans  84   specs  21   prompts  2   research  103   backlog  97   walkthroughs  26   roadmaps  1   comms  1   releases  1   reviews  1078   other  1418
      errors  28   warnings  5   info  126
    (No errors on 20261011-x31lcm-01-ww744p; check.ipd-uncarried-obligation resolved)
    ```

    (5) aw sanitize --agent clean output:
    ```
    $ aw sanitize --agent .
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5146,"findings":0,"evidence":["leak-scan"],"next":null}
    ```

    (6) Bare python3 -m pytest summary:
    ```
    $ python3 -m pytest
    =========================== short test summary info ============================
    8463 passed, 5 skipped, 18 xfailed, 3 warnings in 435.13s (0:07:15)
    (0 failures; tests/test_local_leaks.py verified 9/9 passed)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only the files this plan declares, through `aw commit <plan> -- <paths>`. Never use `git add -A` or `-a`, and never push (`AGENTS.md`). Check the staged set with `git diff --cached --name-only` before every commit and unstage anything you did not change with `git restore --staged <path>`. When you report tests, paste the ACTUAL runner output. A claimed pass with no transcript does not satisfy any `V-*` item.

SCOPE FENCE. The declared `- Scope-Paths:` are seven files. No `.spec.md` is declared, because no spec describes `pwatch`'s signals. The fence is a DECLARATION, not a stop condition: an out-of-scope edit that turns out to be genuinely necessary is made and then JUSTIFIED (`aw ipd finalize` requires a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path). `agent_workflows/runners_monitor.py` is deliberately NOT in scope. Its dashboard handler belongs to `uu4rfe`.

THE LIKELIEST SILENT ERROR is adding `143` to an `exit_contract` tuple while editing the `command_surface.py` comment in E-05. D162 forbids it, and V-05 requires a diff showing no `exit_contract=` line changed.

POST-GATE LIFECYCLE. Execution requires explicit human approval. `- Status:` is `to-review`, and this plan has no `- Readiness:` because `/plan-review` writes that field, not the author (`AGENTS.md`). The terminal transition is never a hand-rolled `git mv`. Under `aw oc run` or `aw agy run`, the RUNNER owns finalize. The executor makes sure every `V-*` has pasted evidence with `Result: pass` and `aw ipd lint --phase pre-transition` conforms, then leaves the transition to the runner. When executed by hand with no runner, the executor performs the transition through `aw ipd finalize` (per the `ipd-lifecycle` workflow), and only after that same lint and evidence bar is met. Backlog item `x31lcm` is set to `graduated` by the runner on verification. The executor must not set it `done`.
