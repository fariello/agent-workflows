# IPD: Make the aw runners table dashboard return 143 on SIGTERM while keeping exit 0 on SIGINT, restore signal handlers, and pin both behaviorally

- Date: 2026-10-14
- Kind: child
- Concern: The `aw runners` table dashboard (`runners_monitor.run_table_dashboard`) reports SUCCESS (`0`) when it is terminated by `SIGTERM`. `runners_monitor.run_table_dashboard` installs one handler, `stop_cleanly(_sig, _frame)`, for BOTH `signal.SIGINT` and `signal.SIGTERM`; it raises `SystemExit(0)`, and the loop's `except (KeyboardInterrupt, SystemExit): return 0` arm turns either signal into exit `0`. Re-measured while authoring at HEAD `cb0f36161`: a real `os.killpg` against a running `python3 -m agent_workflows runners --interval 0.3 --no-color` and against `python3 -m agent_workflows pwatch --runners --table --interval 0.3 --no-color`, sent only after the first frame line was read from stdout, returned `rc=0` for `SIGINT` and `rc=0` for `SIGTERM` on both entry points (F-01). Backlog item `uu4rfe` (surfaced while authoring plan `ww744p` for backlog `x31lcm`) notes that `ww744p` changes only `pwatch.main`, so `aw runners --tree` (which delegates to `pwatch.main`) inherits `ww744p`'s `SIGTERM -> 143` behavior while the default `aw runners` table dashboard (and `aw pwatch --runners --table`, which delegates to `runners_monitor.run_table_dashboard` before `pwatch.main` installs its handlers, `ww744p` F-07) still exits `0` on `SIGTERM`. Backlog `uu4rfe` asks to survey supervisors and decide for consistency with `ww744p`'s ruling.
  THE DECISION: `SIGINT` stays `0` and `SIGTERM` becomes `143` (`EXIT_SIGTERM = 143`), returned after the `finally` block has restored the terminal (`pwatch.LEAVE_ALT_SCREEN`) and the caller's signal handlers. This matches `ww744p`'s ruling for `pwatch.main` on four grounds from the repository (OQ-01). (1) Consistency across both verbs and within each verb: without this change, `aw runners --tree` returns `143` on `SIGTERM` while bare `aw runners` returns `0`, and `aw pwatch` returns `143` on `SIGTERM` while `aw pwatch --runners --table` returns `0` (`ww744p` F-06, F-07). (2) Supervisor distinguishability: a process supervisor, `timeout` wrapper, or CI step teardown sending `SIGTERM` to stop a continuous dashboard loop cannot distinguish exit `0` from a clean `--once` snapshot finish. (3) Zero in-repository blast radius: the caller survey (F-02) shows no in-repository caller supervises `aw runners`, `runners_monitor.run_table_dashboard`, or `tools/watch-runners.py` by signal or branches on exit `0` after `SIGTERM`. (4) Existing repository convention: `143` is already the repository's returned `SIGTERM` code across the drivers (`render_stream.install_exit_signal_handler` and `oc_runipd.main`'s `return 143 if is_sigterm else 130`, DECISIONS D162) and `pwatch.main` (`ww744p`). Restoring `SIG_DFL` and re-sending `SIGTERM` so the process dies `WIFSIGNALED` is rejected because `runners_monitor.run_table_dashboard` and `runners_monitor.main` are called IN-PROCESS by `cli._dispatch`, by `pwatch.main` (`--runners --table`), and by `tests/test_runners_monitor.py`; killing the process from a library function would kill an embedding caller or pytest worker expecting a return value (OQ-01).
  A SECOND DEFECT IN THE SAME LINES, IN SCOPE FOR THE SAME REASON AS `ww744p` E-03: `runners_monitor.run_table_dashboard` installs `stop_cleanly` for `SIGINT` and `SIGTERM` and never restores the previous handlers when it returns. Measured in-process at HEAD `cb0f36161` (`once rc: 0 int restored: False term restored: False`, F-03): every in-process call (including the three existing `tests/test_runners_monitor.py` tests `test_main_once_json`, `test_main_once_agent`, and `test_aw_cli_dispatch_runners`) permanently replaces the host process's or pytest-xdist worker's `SIGINT` and `SIGTERM` handlers with `stop_cleanly`. E-03 saves the previous handlers before installing `stop_cleanly` and restores them in `finally`.
  WHY `chore` AND NOT `bug`: backlog item `uu4rfe` is filed as `chore` with no `- Blocks-Release:`, and that classification is preserved. No supervisor of the dashboard is known in the repository (F-02), and interactive Ctrl-C (`SIGINT`) already exits `0`.
- Scope: IN: (1) re-measure the subprocess signal exits on both `aw runners` and `aw pwatch --runners --table` and re-run the caller survey at the executing HEAD as a gate (E-01); (2) make `SIGTERM` return `143` (`EXIT_SIGTERM = 143`) and keep `SIGINT` and `KeyboardInterrupt` at `0` in `runners_monitor.run_table_dashboard`, with the `finally` terminal restore (`pwatch.LEAVE_ALT_SCREEN`) running on both paths (E-02); (3) save and restore the previous `SIGINT` and `SIGTERM` handlers in `runners_monitor.run_table_dashboard`'s `finally` block so every in-process caller gets its handlers back on every exit path (E-03); (4) add behavioral subprocess signal tests (`aw runners` `SIGTERM -> 143`, `aw runners` `SIGINT -> 0`, `aw pwatch --runners --table` `SIGTERM -> 143`) and in-process handler-restoration tests (`--once` and bounded patched-`sleep` `SIGTERM -> 143`) to `tests/test_runners_monitor.py` (E-04); (5) update `tools/README.md` to remove the `--runners --table` exception added by `ww744p` E-06 and document `aw runners` (`tools/watch-runners.py`) exit statuses and shim compatibility (E-05); (6) record the decision as the next free `DECISIONS.md` entry and add one `CHANGELOG.md` line (E-06). OUT: `agent_workflows/pwatch.py` (owned by `ww744p`), any `exit_contract` tuple change in `agent_workflows/command_surface.py` (forbidden by D162 because `143` is signal-derived), and any spec edit.
- Scope-Paths: agent_workflows/runners_monitor.py, tests/test_runners_monitor.py, tools/README.md, DECISIONS.md, CHANGELOG.md
- Item-Dependencies: executed:ww744p
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: uu4rfe
- Set: uu4rfe
- Order: 1
- Highest E allocated: 06
- Author: antigravity
- Id: 9380pe

## Workflow history
- 2026-10-14 to-review (antigravity): authored from backlog item uu4rfe; measured signal exits and handler leak at HEAD cb0f36161; ran caller survey; resolved OQ-01 from repository evidence

- 2026-10-14 draft (antigravity): created.

## Goal

Make the `aw runners` table dashboard (`runners_monitor.run_table_dashboard`, reached by `aw runners`, `tools/watch-runners.py`, and `aw pwatch --runners --table`) return `143` on `SIGTERM` while keeping exit `0` on `SIGINT`, matching `aw pwatch` (`ww744p`) and `aw runners --tree`. Restore the caller's `SIGINT` and `SIGTERM` handlers when `run_table_dashboard` returns, and pin both behaviors with outcome-based subprocess and in-process tests.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure before changing anything

- [ ] E-01 Re-drive the signal probe on `aw runners` and `aw pwatch --runners --table` and the caller survey at the executing HEAD and record both verbatim, without editing any file.
  - Depends on: none
  - Expected outcome: two pasted transcripts. (a) THE PROBE: using an isolated temporary `--repo` directory (so `runners_monitor.find_active_runners` does not follow `.git` into a parent checkout's live runs), launch `python3 -m agent_workflows runners --repo <tmp_dir> --interval 0.3 --no-color` and `python3 -m agent_workflows pwatch --runners --table --repo <tmp_dir> --interval 0.3 --no-color` for each of `signal.SIGINT` and `signal.SIGTERM` with `start_new_session=True` and `stdout=PIPE`, block on `stdout.readline()` until the first frame header arrives (no fixed sleep), send `os.killpg(p.pid, sig)`, `wait(timeout=10)`, and print `returncode`. Expected at authoring before E-02: `0` for `SIGINT` and `0` for `SIGTERM` on both commands. (b) THE SURVEY: `git grep -n "runners_monitor\|run_table_dashboard\|watch-runners\|aw runners" -- ":!.aw/records"`, with every call site classified as in-process caller, CLI wrapper, test caller, or signal supervisor. Expected at authoring: in-process callers `cli._dispatch` (both `argv_list[0] == "runners"` and `args.command == "runners"`), `pwatch.main` (`--runners --table` branch and data-helper calls), and `tests/test_runners_monitor.py`; wrapper `tools/watch-runners.py`; no signal supervisor.
    GATE: if (a) already returns `143` for `SIGTERM`, another lane has made this change, so STOP and reconcile. If (b) finds a caller that sends `SIGTERM` to `aw runners` or `run_table_dashboard` and treats `0` as success, STOP: the decision in OQ-01 rests on there being no such caller, so record the caller and re-decide before changing anything.
  - Execution state: pending

### Task group 2: the behavior change and handler restoration

- [ ] E-02 Make `SIGTERM` return `143` and `SIGINT` (or `KeyboardInterrupt`) return `0` from `runners_monitor.run_table_dashboard`, with the `finally` terminal restore (`pwatch.LEAVE_ALT_SCREEN`) still running on both paths.
  - Depends on: E-01
  - Expected outcome: define a named module constant `EXIT_SIGTERM = 143` in `agent_workflows/runners_monitor.py` with a brief comment citing `pwatch.EXIT_SIGTERM` (`ww744p`), `render_stream.install_exit_signal_handler`, and `oc_runipd.main`'s `return 143 if is_sigterm else 130` as the repository precedent. In `runners_monitor.run_table_dashboard`, `stop_cleanly(signum: int, _frame: object) -> None` distinguishes the signal (`raise SystemExit(EXIT_SIGTERM if signum == signal.SIGTERM else 0)`), and the loop's exception arms return `0` on `KeyboardInterrupt` and `exc.code if isinstance(exc.code, int) else 0` on `SystemExit`. The `--once`, `--json`, and `--agent` paths still return `0`, and `runners_monitor.main` still exits `2` on invalid arguments via `build_parser().parse_args`. Do NOT kill the process with `SIG_DFL` plus `os.kill`, because `run_table_dashboard` and `runners_monitor.main` are called in-process (OQ-01).
  - Execution state: pending

- [ ] E-03 Save the `signal.SIGINT` and `signal.SIGTERM` handlers in place before `runners_monitor.run_table_dashboard` installs `stop_cleanly`, and restore them in the `finally` block so every in-process caller gets its handlers back on every exit path.
  - Depends on: E-02
  - Expected outcome: in `runners_monitor.run_table_dashboard`, save `prev_sigint = signal.getsignal(signal.SIGINT)` and `prev_sigterm = signal.getsignal(signal.SIGTERM)` immediately before calling `signal.signal(signal.SIGINT, stop_cleanly)` and `signal.signal(signal.SIGTERM, stop_cleanly)`, and restore both handlers in `finally` (alongside the existing `if is_interactive:` `pwatch.LEAVE_ALT_SCREEN` write) so that after `run_table_dashboard` or `runners_monitor.main` returns (via `--once`, `--json`, `--agent`, `SIGINT`, `SIGTERM`, or an uncaught exception), `signal.getsignal(signal.SIGINT)` and `signal.getsignal(signal.SIGTERM)` equal what they were before the call.
  - Execution state: pending

### Task group 3: pin both behaviors with outcome-based tests

- [ ] E-04 Add behavioral tests for subprocess signal exits and in-process signal handler restoration to `tests/test_runners_monitor.py`.
  - Depends on: E-02, E-03
  - Expected outcome: five new tests in `tests/test_runners_monitor.py`, each driving the code with an isolated `tmp_path` (`--repo str(tmp_path)`) and asserting on real outputs and state. (1) Subprocess `SIGTERM` test on `python3 -m agent_workflows runners --repo <tmp_path> --interval 0.3 --no-color` (`start_new_session=True`, `stdout=PIPE`), reading the first line from stdout before sending `os.killpg(p.pid, signal.SIGTERM)` (no fixed sleep), waiting with `timeout=10`, and asserting `returncode == 143`. (2) Subprocess `SIGINT` test with the same shape sending `signal.SIGINT` and asserting `returncode == 0`. (3) Subprocess `SIGTERM` test on `python3 -m agent_workflows pwatch --runners --table --repo <tmp_path> --interval 0.3 --no-color` sending `signal.SIGTERM` after the first line arrives and asserting `returncode == 143` (verifying the `pwatch --runners --table` delegation path from `ww744p` F-07). (4) In-process handler-restoration test on `--once`: install sentinel functions for `SIGINT` and `SIGTERM`, call `runners_monitor.main(["--once", "--no-color", "--repo", str(tmp_path)])` with stdout redirected, and assert `rc == 0` and `signal.getsignal` returns both sentinels afterward (restoring original handlers in `try/finally`). (5) REQUIRED bounded in-process `SIGTERM` test (matching `ww744p` F-08): install sentinel handlers, patch `runners_monitor.time.sleep` to a function that increments a call counter, raises `AssertionError` if called a second time, and calls `os.kill(os.getpid(), signal.SIGTERM)` on the first call; call `runners_monitor.main(["--no-color", "--repo", str(tmp_path)])` with stdout redirected; and assert `rc == 143`, the sleep helper ran once, and both sentinel handlers are restored afterward. No test may read `runners_monitor.py` source or assert on comments/docstrings (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE").
  - Execution state: pending

### Task group 4: keep documentation and decision records true

- [ ] E-05 Update `tools/README.md` to remove the `--runners --table` exception from the `aw pwatch` exit-status note and document `aw runners` (`tools/watch-runners.py`).
  - Depends on: E-02
  - Expected outcome: in the `## aw pwatch (was pwatch.py)` section of `tools/README.md` (which `ww744p` E-06 updated with an exit-status note naming `--runners --table` as the exception that still exited `0` on `SIGTERM`), remove the `--runners --table` exception so the note states that `aw pwatch` (including `--runners --table`) and `aw runners` exit `0` after `--once` or Ctrl-C (`SIGINT`) and `143` when sent `SIGTERM`, restoring the terminal in every case; and under `### Backwards Compatibility` (or an adjacent note), mention `tools/watch-runners.py` alongside `tools/watch-agy.py` as the compatibility shim forwarding to `agent_workflows.runners_monitor` (`aw runners`). This is user-facing prose, so it must contain no em or en dashes (`AGENTS.md`).
  - Execution state: pending

- [ ] E-06 Record the decision as the next free `DECISIONS.md` entry number at execution (D168 at authoring; re-read the last `### D<n>` heading immediately before writing, since `ww744p` also allocates a `D<n>` entry) and add one `CHANGELOG.md` `Changed:` line under the pending release.
  - Depends on: E-02
  - Expected outcome: the `DECISIONS.md` entry uses the standard `Context` / `Decision` / rejected alternatives / `Applied` structure. It answers backlog `uu4rfe`, records the `runners_monitor` supervision survey result (F-02), names both rejected alternatives (keep `0` on `SIGTERM`; restore `SIG_DFL` and re-send `SIGTERM` to die `WIFSIGNALED`) with the reason for each, notes that `aw runners` (both default table dashboard and `--tree`) and `aw pwatch` (including `--runners --table`, closing `ww744p` F-07) now uniformly return `0` on `SIGINT` and `143` on `SIGTERM` while restoring caller signal handlers, and confirms `runners` keeps `exit_contract=(0, 1, 2)` under D162. Existing `DECISIONS.md` entries (including D162 and `ww744p`'s entry) are NOT edited in place. The `CHANGELOG.md` line is user-facing and contains no em or en dashes (`AGENTS.md`).
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Tests assert OUTCOMES, not code structure (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16). E-04 sends real signals to subprocesses and drives in-process entry points, asserting on return codes and `signal.getsignal` values without inspecting source text.
- DECISIONS D162 rules that `CommandDeclaration.exit_contract` enumerates only codes produced by a command's normal return path and excludes signal-derived codes (`130`, `143`). `command_surface.get_declaration("runners").exit_contract` is `(0, 1, 2)` and must NOT be widened to include `143`.
- The repository's established returned `SIGTERM` code is `143`: `render_stream.install_exit_signal_handler` and `oc_runipd.main`'s `return 143 if is_sigterm else 130` (D162 measurement 3), and sibling plan `ww744p` (`pwatch.main`).
- Sibling plan `ww744p` (backlog `x31lcm`, `- Status: approved`) owns `agent_workflows/pwatch.py` and adds an exit-status note to `tools/README.md` that explicitly notes `aw pwatch --runners --table` as an exception still returning `0` on `SIGTERM` (`ww744p` F-07, E-06, V-06). Declaring `- Item-Dependencies: executed:ww744p` ensures `ww744p` executes first while its F-07 exception is still true on disk, and this plan (`9380pe`) then closes the exception in `runners_monitor.run_table_dashboard` and `tools/README.md`.
- Run the test suite BARE as `python3 -m pytest` (`pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`). Use `-o addopts=""` only for per-test counts on narrowed runs (`AGENTS.md`).
- Omit `- Readiness:` when authoring; `/plan-review` owns that field (`AGENTS.md`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | **The backlog item's signal measurement reproduces at the authoring HEAD on both entry points reaching `run_table_dashboard`.** `runners_monitor.run_table_dashboard` defines `stop_cleanly(_sig, _frame)` raising `SystemExit(0)`, registers it for both `signal.SIGINT` and `signal.SIGTERM`, and catches `(KeyboardInterrupt, SystemExit)` returning `0`. Both `aw runners` and `aw pwatch --runners --table` reach `run_table_dashboard` and return `0` on `SIGINT` and `0` on `SIGTERM`. | Subprocess probe at HEAD `cb0f36161` (sending `os.killpg` only after reading the first stdout line): `aw runners SIGINT rc=0 first_line_seen=True`, `aw runners SIGTERM rc=0 first_line_seen=True`, `aw pwatch --runners --table SIGINT rc=0 first_line_seen=True`, `aw pwatch --runners --table SIGTERM rc=0 first_line_seen=True`. |
| F-02 | **Supervision survey: nothing in the repository supervises `aw runners`, `runners_monitor.run_table_dashboard`, or `tools/watch-runners.py` by signal or branches on exit `0` after `SIGTERM`.** Callers outside `.aw/records` are: in-process `cli._dispatch` (`argv_list[0] == "runners"` and `args.command == "runners"`, calling `runners_monitor.main`), in-process `pwatch.main` (`if getattr(args, "runners", False) and getattr(args, "table", False): return runners_monitor.run_table_dashboard(args)`, plus helper calls `find_active_runners`, `extract_journey_info`, `classify_activity`, `format_bytes`), standalone wrapper `tools/watch-runners.py` (`return runners_monitor.main(sys.argv[1:])`), and in-process tests in `tests/test_runners_monitor.py`. None sends `SIGTERM` or expects `0` after `SIGTERM`. | `git grep -n "runners_monitor\|run_table_dashboard\|watch-runners\|aw runners" -- ":!.aw/records"` at HEAD `cb0f36161`, classified by call site. |
| F-03 | **`runners_monitor.run_table_dashboard` leaks its `SIGINT` and `SIGTERM` handlers into in-process callers.** It calls `signal.signal(signal.SIGINT, stop_cleanly)` and `signal.signal(signal.SIGTERM, stop_cleanly)` and never restores the previous handlers in `finally` (which only writes `pwatch.LEAVE_ALT_SCREEN`). After any in-process call (`cli._dispatch`, `pwatch.main` with `--runners --table`, or `tests/test_runners_monitor.py`), `SIGINT` and `SIGTERM` in the calling process or pytest-xdist worker remain bound to `stop_cleanly` (`raise SystemExit(0)`). | In-process probe at HEAD `cb0f36161` with sentinel handlers around `runners_monitor.main(["--once", "--no-color"])`: `once rc: 0 int restored: False term restored: False`. Bounded patched-`sleep` in-process `SIGTERM` probe: `inproc sigterm rc: 0 calls: 1`. |
| F-04 | **Passing an isolated `--repo <tmp_path>` avoids worktree-to-primary-repo runner discovery during probes and tests.** `runners_monitor.find_active_runners` inspects `repo / ".git"` when `repo / ".aw" / "records" / "runs"` is absent and resolves a linked worktree back to `primary_repo / ".aw" / "records" / "runs"`. Passing `--repo <tmp_path>` makes `find_active_runners` return `[]` immediately without sleeping in `sample_runners` or reading `/proc`, so subprocess signal probes finish in ~0.45s and are isolated from live runners in the host repository. | `runners_monitor.find_active_runners` worktree resolution branch; timing probe at HEAD `cb0f36161` with `tempfile.TemporaryDirectory()` (`dt=0.450s` to `0.468s`). |
| F-05 | **`command_surface.py` and `test_exit_contract_conformance.py` need no edits for `uu4rfe`.** `command_surface.get_declaration("runners").exit_contract` is `(0, 1, 2)`, which is already conformant under D162 (signal-derived `143` is excluded). Unlike `pwatch`, neither the `CommandDeclaration.exit_contract` comment in `agent_workflows/command_surface.py` nor the docstring in `tests/test_exit_contract_conformance.py` mentions `runners` or `runners_monitor`. | `command_surface.COMMAND_INVENTORY` declaration for `"runners"`; `git grep -n "runners_monitor" agent_workflows/command_surface.py tests/test_exit_contract_conformance.py` (0 hits). |
| F-06 | **`ww744p` E-06 adds a `--runners --table` exception note to `tools/README.md` that this plan must retire after `ww744p` executes.** `ww744p` is `approved` in `pending/` and its V-06 requires `git diff tools/README.md` to carry the `--runners --table` exception because `run_table_dashboard` was out of `ww744p`'s scope. Ordering this plan after `ww744p` via `- Item-Dependencies: executed:ww744p` keeps `ww744p` V-06 valid during `ww744p`'s execution and lets E-05 remove the exception once `run_table_dashboard` also exits `143` on `SIGTERM`. | Plan `ww744p` F-07, E-06, V-06; `tools/README.md` `## aw pwatch (was pwatch.py)` section. |

## Proposed changes (ordered, validatable)

1. **Re-measure at executing HEAD (E-01).** Re-run the subprocess signal probe (for both `aw runners` and `aw pwatch --runners --table`) and the caller survey before editing any file.
2. **Return `143` on `SIGTERM` and `0` on `SIGINT` (E-02).** Define `EXIT_SIGTERM = 143` in `agent_workflows/runners_monitor.py` and update `runners_monitor.run_table_dashboard` so `SIGTERM` returns `143` while `SIGINT` and `KeyboardInterrupt` return `0`, with `finally` still restoring the terminal.
3. **Restore signal handlers in `finally` (E-03).** Save the previous `SIGINT` and `SIGTERM` handlers before installing `stop_cleanly` in `runners_monitor.run_table_dashboard` and restore them in `finally`.
4. **Pin both behaviors with tests (E-04).** Add subprocess `SIGTERM`/`SIGINT` tests (covering both `aw runners` and `aw pwatch --runners --table`) and in-process handler-restoration tests (`--once` and bounded `SIGTERM`) to `tests/test_runners_monitor.py`.
5. **Sync documentation and decision records (E-05, E-06).** Update `tools/README.md` to remove the `--runners --table` exception and mention `tools/watch-runners.py`; append a new `DECISIONS.md` entry and a `CHANGELOG.md` line.

## Deferred / out of scope (with reason)

- **`aw pwatch` tree-watcher signal handling in `agent_workflows/pwatch.py`.** Already owned by approved sibling plan `ww744p`, which this plan depends on (`executed:ww744p`).
  - Carrier: ww744p
  - Carrier-Evidence: .aw/records/plans/pending/20261011-x31lcm-01-ww744p-make-aw-pwatch-return-143-on-sigterm-while-keeping-exit-0-on.ipd.md
- **Adding `143` to `runners`'s `exit_contract` in `agent_workflows/command_surface.py`.** Refused on D162, not deferred: `143` from `SIGTERM` is signal-derived and D162 excludes signal-derived codes from `exit_contract`.
  - Carrier-Declined: a decision not to act creates no obligation. Recorded in OQ-01 and E-06.
- **Dying `WIFSIGNALED` (restore `SIG_DFL` and re-send `SIGTERM`) instead of returning `143`.** Rejected in OQ-01 because `runners_monitor.run_table_dashboard` and `runners_monitor.main` are called in-process by `cli._dispatch`, `pwatch.main`, and `tests/test_runners_monitor.py`.
  - Carrier-Declined: a rejected alternative creates no obligation. Recorded in OQ-01 and E-06.

## Scope check

- Over-scope: E-03 (restoring `SIGINT` and `SIGTERM` handlers in `finally`) goes slightly beyond the backlog item's question, for the exact same reason as `ww744p` E-03: it is in the same lines E-02 edits, F-03 proves `run_table_dashboard` currently leaks `stop_cleanly` into every in-process caller (including existing `tests/test_runners_monitor.py` tests in pytest-xdist workers), and E-04's in-process tests require it.
- Under-scope: backlog `uu4rfe` asks to decide whether the `aw runners` table dashboard should return `143` on `SIGTERM` like `aw pwatch`. Per the backlog graduation contract (`AGENTS.md`), this plan resolves the question from repository evidence (OQ-01) and implements and verifies the change in one pass.
- Right-sizing: six `E-*` items, each addressing one concern (`E-01` baseline probe/survey, `E-02` `SIGTERM` exit code, `E-03` handler restoration, `E-04` behavioral tests, `E-05` user docs in `tools/README.md`, `E-06` `DECISIONS.md` + `CHANGELOG.md`).

## Required tests / validation

- `python3 -m pytest tests/test_runners_monitor.py -o addopts="" -v` with output pasted, showing all existing and new tests pass.
- The E-01 subprocess signal probe run again after E-02, pasted, showing `SIGINT rc=0` and `SIGTERM rc=143` for both `aw runners` and `aw pwatch --runners --table`.
- `python3 -m pytest tests/test_pwatch_signal_exit.py tests/test_exit_contract_conformance.py tests/test_completion.py tests/test_cli_parser_conflict_policy.py tests/test_cli_dest_shadowing.py -o addopts=""` as the targeted regression suite, with output pasted.
- A bare `python3 -m pytest`, with the summary pasted and any failures compared by failure set against an unmodified tree at the same HEAD.
- `aw ipd lint --phase pre-transition` conforming on this plan; `aw check` passing after the `DECISIONS.md` and `CHANGELOG.md` edits; `aw sanitize --agent` passing with no `fail`.

## Spec / documentation sync

- `tools/README.md` is updated to remove the `--runners --table` exception from the `aw pwatch` exit-status note and document `aw runners` / `tools/watch-runners.py` (E-05).
- `DECISIONS.md` gets the new decision entry and `CHANGELOG.md` gets one `Changed:` line under the pending release (E-06).
- `docs/cli-output-contract.md` and `agent_workflows/command_surface.py`: no changes needed (F-05; D162 excludes signal-derived codes from `exit_contract`).
- No `.spec.md` is in `- Scope-Paths:` because no specification in `.aw/records/specs/` describes `runners_monitor` or `aw runners` signal handling.

## Open questions

### OQ-01: Should `runners_monitor.run_table_dashboard` return `143` on `SIGTERM` while keeping `0` on `SIGINT`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE: return `143` (`EXIT_SIGTERM = 143`) on `SIGTERM` and keep `0` on `SIGINT` (and `KeyboardInterrupt`), restoring the terminal and the caller's signal handlers in `finally`. Three options were evaluated: (a) Keep `0` on `SIGTERM`: rejected because it leaves an internal inconsistency within both verbs (`aw runners --tree` returns `143` via `pwatch.main` while bare `aw runners` returns `0`; `aw pwatch` returns `143` while `aw pwatch --runners --table` returns `0`), and prevents any supervisor from distinguishing termination by `SIGTERM` from a clean `--once` completion. (b) Restore `SIG_DFL` and re-send `SIGTERM` (`WIFSIGNALED`): rejected because `runners_monitor.run_table_dashboard` and `runners_monitor.main` are library entry points called in-process by `cli._dispatch`, `pwatch.main` (`--runners --table`), and `tests/test_runners_monitor.py` (F-02), so killing the process would kill an embedding caller or test worker. (c) Return `143` on `SIGTERM` and `0` on `SIGINT`: chosen. It aligns `run_table_dashboard` with `pwatch.main` (`ww744p`) and the drivers (`render_stream.install_exit_signal_handler`, `oc_runipd.main`, D162), breaks no in-repository caller (F-02), and preserves in-process callability. Reversible by changing one constant return path. REVERSIBLE: yes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste both transcripts from the executing HEAD before any file is edited: (a) the subprocess signal probe output for `SIGINT` and `SIGTERM` against `python3 -m agent_workflows runners --repo <tmp_dir> --interval 0.3 --no-color` and `python3 -m agent_workflows pwatch --runners --table --repo <tmp_dir> --interval 0.3 --no-color`, each sent after `stdout.readline()` returned the first line, showing `rc=0` and `rc=0`; (b) the `git grep` caller survey with each hit classified, showing no signal supervisor; and `git status --short` showing no modified files. The observation is produced by `runners_monitor.main` and `pwatch.main` delegating to `runners_monitor.run_table_dashboard`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the same E-01 subprocess signal probe run again after the change, pasted, showing `SIGINT rc=0` and `SIGTERM rc=143` for both `python3 -m agent_workflows runners --repo <tmp_dir> --interval 0.3 --no-color` and `python3 -m agent_workflows pwatch --runners --table --repo <tmp_dir> --interval 0.3 --no-color`. Also paste `python3 -m agent_workflows runners --once --no-color >/dev/null; echo rc=$?` showing `rc=0`, and `python3 -m agent_workflows runners --bad-flag; echo rc=$?` showing `rc=2`. The observation is produced by `runners_monitor.run_table_dashboard` and `runners_monitor.main`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted passing output of E-04's in-process handler-restoration tests (sentinel handlers equal before and after `--once` and after the bounded in-process `SIGTERM`, which also returns `143`). Also paste the `git diff` hunk of `agent_workflows/runners_monitor.py` showing `prev_sigint` and `prev_sigterm` saved before `signal.signal(...)` and restored in `finally`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted output of `python3 -m pytest tests/test_runners_monitor.py -o addopts="" -v` showing every test passed with test names visible. Then prove falsifiability: temporarily change `EXIT_SIGTERM = 143` to `0` in `agent_workflows/runners_monitor.py`, re-run `python3 -m pytest tests/test_runners_monitor.py -o addopts=""`, paste the failing `SIGTERM` assertions, revert `EXIT_SIGTERM = 143`, and paste `git diff --stat` showing only the intended changes remain. Also paste `grep -nE "\binspect\b|\bast\.|read_text|open\(.*runners_monitor\.py" tests/test_runners_monitor.py` showing no hits (confirming no code-pinning), and an interpreter print of `command_surface.get_declaration("runners").exit_contract` showing `(0, 1, 2)`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `git diff tools/README.md` showing the `--runners --table` exception removed from the `aw pwatch` exit-status note and `aw runners` / `tools/watch-runners.py` documented. Pasted output of `grep -nP "\x{2013}|\x{2014}" tools/README.md` limited to the modified/added lines showing zero em or en dashes.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the pasted new `DECISIONS.md` entry with its number, the supervision survey summary, the two rejected alternatives (`0` on `SIGTERM`; `SIG_DFL` re-raise), and the D162 `exit_contract=(0, 1, 2)` confirmation, plus `git diff DECISIONS.md` showing no earlier entry was edited. The pasted `CHANGELOG.md` line and `grep -nP "\x{2013}|\x{2014}" CHANGELOG.md` over the added line showing no em or en dashes. Pasted `aw check` output and `aw sanitize --agent` output over all changed files with no `fail`. Pasted bare `python3 -m pytest` summary and targeted regression suite (`python3 -m pytest tests/test_pwatch_signal_exit.py tests/test_exit_contract_conformance.py tests/test_completion.py tests/test_cli_parser_conflict_policy.py tests/test_cli_dest_shadowing.py -o addopts=""`).
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only the files this plan declares, through `aw commit <plan> -- <paths>`. Never use `git add -A` or `-a`, and never push (`AGENTS.md`). Check the staged set with `git diff --cached --name-only` before every commit and unstage anything you did not change with `git restore --staged <path>`. When you report tests, paste the ACTUAL runner output. A claimed pass with no transcript does not satisfy any `V-*` item.

SCOPE FENCE. The declared `- Scope-Paths:` are five files: `agent_workflows/runners_monitor.py`, `tests/test_runners_monitor.py`, `tools/README.md`, `DECISIONS.md`, and `CHANGELOG.md`. No `.spec.md` is declared because no spec governs `runners_monitor` signal handling. `agent_workflows/pwatch.py` is owned by `ww744p` (which this plan depends on via `executed:ww744p`) and is not modified here.

POST-GATE LIFECYCLE. Execution requires explicit human approval. `- Status:` is `to-review`, and this plan omits `- Readiness:` because `/plan-review` writes that field, not the author (`AGENTS.md`). Under `aw oc run` or `aw agy run`, the runner owns `finalize` once every `V-*` has pasted evidence with `Result: pass` and `aw ipd lint --phase pre-transition` conforms. When executed by hand with no runner, the executor performs the transition through `aw ipd finalize`. Backlog item `uu4rfe` is set to `graduated` by the runner on verification; the executor must not set it `done` during plan production.
