# IPD: runipd stall watchdog process-group reaping and MmSs idle format

- Date: 2026-08-24
- Kind: child
- Concern: A live incident (run-20260825T010422Z-553957, reviewing IPD 5rzupk) hung for ~12 minutes with no forward progress. Root cause established by inspection: the child agent made a `hound` MCP web tool call that blocked on the network (the `hound` subprocess sat in `ep_poll`, 0 CPU, 6 open sockets), and a non-interactive runipd turn has NO timeout to break out of a wedged tool call, so it hung indefinitely. It only recovered when a human manually killed the `hound` PID. Two runipd defects made this worse: (1) NO stall watchdog - `Heartbeat` (runipd.py:194-236) only PRINTS a "still working ... since last event" line, it never ACTS on a stall; (2) NO process-group reaping - `terminate_process` (runipd.py:1008-1031) and the Popen at runipd.py:1096-1103 signal only the direct opencode PID (no `start_new_session`), so MCP children like `hound` and LSP servers orphan when the turn is killed (this is why the human had to kill `hound` directly rather than the driver reaping it). Additionally the idle counter is printed as raw seconds ("... 381s since last event") rather than MmSs, which is hard to read at a glance for multi-minute stalls.
- Scope: Make runipd self-heal a stalled turn instead of hanging forever: add a stall watchdog that reaps the child turn when no JSONL event arrives for a configurable window and marks the attempt interrupted/failed-safely so `resume` can retry; make child termination kill the whole PROCESS GROUP (opencode + hound + LSP) so no MCP/LSP subprocess orphans; and format the idle duration as `XmYs since last event` (matching the existing `elapsed` format) instead of bare seconds. Land it FIRST on the current standalone `tools/ipdrunner/runipd.py`, and write every change so it migrates unchanged into the packaged `agent_workflows/oc_runipd.py` when the awocrunner Set graduates the runner (the awocrunner core move is verbatim, so behavior-preserving edits here carry over automatically).
- Scope-Paths: tools/ipdrunner/runipd.py, tools/ipdrunner/test_runipd.py
- Status: executed
- Set: runipdwd
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: iw793a

## Workflow history
- 2026-08-25 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): Validate-and-finalize: MmSs idle format, process-group reaping, and stall watchdog (StallTimeout -> interrupted -> resume re-queue) verified; implementation landed in ed52562 pre-approval, all E performed and all V pass with pasted evidence in the run report [Scope reconciliation - in-scope-unmodified tools/ipdrunner/runipd.py: verified present from commit ed52562 (landed before this run base HEAD); revalidated by full test suite + live group-reap demo, no further modification needed; in-scope-unmodified tools/ipdrunner/test_runipd.py: verified present from commit ed52562; all new tests re-run green, no further modification needed]
- 2026-08-25 approved (opencode its_direct/pt3-claude-opus-4.8-1m-us, --by-human): Human approval: GO (via operator in interactive session)
- 2026-08-25 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (watchdog must raise a distinct StallTimeout so execute_item marks the attempt interrupted, not exit-code failed-safely, else requeue_interrupted never retries it), PR-002 (E-04(c) asserts interrupted status + re-queue, not just terminate_process invoked), PR-003 (IPD-Z602 advisory assessed: E-03 is one concern/one code region/one V-item, no split); GO - PENDING HUMAN APPROVAL
- 2026-08-25 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): Completed drafting: fully authored, lint-conforming, ready to critique

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; single-child plan from the run-20260825T010422Z-553957 hung-hound-tool-call incident. Addresses stall watchdog + process-group reaping + MmSs idle format. Designed to land on the current runipd.py and migrate to the aw/oc_runipd.py version.

## Goal

Ensure a runipd turn that stalls on a wedged tool call (or any silent hang) is automatically detected, its whole child process group cleanly reaped (no orphaned MCP/LSP processes), and the attempt recorded as recoverable via `resume` - so no run hangs indefinitely and no human intervention is required; and make the idle duration in the progress output human-readable (`XmYs`).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Human-readable idle duration (smallest, independent)

- [x] E-01 In `Heartbeat._run` (runipd.py:213-225), format the idle time as `{m}m{s:02d}s since last event` (reusing the same `divmod(..., 60)` shape already used for `elapsed` on the same line at runipd.py:217-218) instead of `{int(idle)}s since last event`. Keep the existing `elapsed` field unchanged. Output-only; no behavior change.
  - Depends on: none
  - Expected outcome: the progress line reads e.g. `(6m21s elapsed, 6m21s since last event)` rather than `(6m21s elapsed, 381s since last event)`.
  - Execution state: performed
  - Execution note: implemented in commit ed52562; `Heartbeat.format_idle` at runipd.py:215-218 returns `{m}m{s:02d}s` and `format_message` at runipd.py:220-227 emits `... since last event` with the unchanged `elapsed` field.

### Task group 2: Process-group child so subprocesses can be reaped together

- [x] E-02 In `run_opencode` (runipd.py:1096-1103), start the child in its own process group/session (`subprocess.Popen(..., start_new_session=True)` on POSIX) so opencode and all its descendants (MCP servers like `hound`, LSP servers) share a killable group. Update `terminate_process` (runipd.py:1008-1031) to signal the whole GROUP (`os.killpg(os.getpgid(pid), sig)`) through the existing SIGINT -> SIGTERM -> SIGKILL escalation (`_SIGINT_GRACE_SECONDS`=5, `_SIGTERM_GRACE_SECONDS`=2), falling back to the single-process path if `getpgid`/`killpg` is unavailable (non-POSIX). Preserve the existing stream-closing behavior.
  - Depends on: none
  - Expected outcome: terminating a turn kills opencode AND its MCP/LSP children (no orphans); verified by asserting the group receives the signal.
  - Execution state: performed
  - Execution note: commit ed52562; `start_new_session=True` on POSIX at runipd.py:1421-1422; `terminate_process` at runipd.py:1299-1337 signals the group via `os.getpgid`/`os.killpg` with the SIGINT(5s)->SIGTERM(2s)->SIGKILL escalation and single-process fallback, preserving `_close_process_streams`.

### Task group 3: Stall watchdog that acts on silence

- [x] E-03 Add a stall watchdog to the streaming loop in `run_opencode` (runipd.py:1107-1126). Track the last-event monotonic time (the loop already calls `heartbeat.touch()` per line at runipd.py:1112). If no JSONL line arrives for a configurable `stall_timeout` (default 600s; `0`/None disables), reap the child via the E-02 group-aware `terminate_process` and signal the stall to the caller as a DISTINCT condition (NOT a normal return): raise a dedicated `StallTimeout(DriverError)` from `run_opencode` (or set an unambiguous sentinel the caller checks) so `execute_item` does NOT fall through to `reconcile_disposition`/exit-code classification (runipd.py:1261-1262), which would otherwise misclassify the SIGKILLed turn as `failed-safely` and prevent `requeue_interrupted` (which only re-queues `interrupted`, runipd.py:1346-1348) from retrying it. In `execute_item`, handle `StallTimeout` in a branch modeled on the existing `KeyboardInterrupt` handler (runipd.py:1230-1238): set `item["status"] = "interrupted"`, record `attempt["interrupted_at"] = utc_now()` and a distinct `attempt["stall_timeout"] = <seconds>` (or `attempt["interrupt_reason"] = "stall_timeout"`), append an `ipd-stalled` event, and let the run loop move on so `resume` re-queues it via `reconcile_interrupted`/`requeue_interrupted`. Implement the timeout without blocking indefinitely on `for line in process.stdout` (a daemon watchdog thread that trips `terminate_process`, whose pipe close then unblocks the loop, is acceptable); the reap must be idempotent with the existing `except BaseException: terminate_process(...)` path. Add a `--stall-timeout SECONDS` flag (on `start` and `resume`) plumbed through `state["options"]`, defaulting to the constant. The watchdog enforces the timeout in ALL output modes including `raw` (safety must not depend on verbosity; see OQ-02).
  - Depends on: E-02
  - Expected outcome: a turn emitting no events for longer than `stall_timeout` is auto-terminated (whole group), its attempt ends as `interrupted` (with a `stall_timeout` reason) NOT `failed-safely`, and `resume` re-queues it - instead of hanging indefinitely as in run-20260825T010422Z-553957.
  - Execution state: performed
  - Execution note: commit ed52562; `StallTimeout(DriverError)` at runipd.py:253-256; `StallWatchdog` at runipd.py:259-307 runs off the stream loop independent of the heartbeat print thread (OQ-02 satisfied in `raw` mode); `run_opencode` at runipd.py:1424-1467 wires the watchdog, group-reaps via `terminate_process`, and raises `StallTimeout` from both the `except BaseException` path and the post-loop check; `execute_item` at runipd.py:1581-1607 handles `StallTimeout` setting `item["status"]="interrupted"`, `attempt["interrupt_reason"]="stall_timeout"`, `attempt["stall_timeout"]`, appends an `ipd-stalled` event, and returns so `requeue_interrupted` re-queues on resume; `--stall-timeout` on start+resume plumbed via `state["options"]`, `DEFAULT_STALL_TIMEOUT=600.0` at runipd.py:1296.

### Task group 4: Tests

- [x] E-04 In `tools/ipdrunner/test_runipd.py`, add tests: (a) `Heartbeat` idle formatting renders `XmYs since last event` for a >60s idle (unit-test the formatting helper, injecting a fake idle/elapsed); (b) `terminate_process` signals the process group (use a fake process exposing a pid + a stubbed `os.killpg`/`getpgid`, assert group signaling and the SIGINT->SIGTERM->SIGKILL escalation, plus the non-POSIX fallback); (c) the stall watchdog trips: a stubbed child that produces no output within a short test `stall_timeout` is terminated (assert `terminate_process` invoked) AND the attempt ends specifically as `item["status"] == "interrupted"` with a `stall_timeout` reason recorded (NOT `failed-safely`/exit-code classification), such that `requeue_interrupted` would re-queue it (assert the interrupted status directly, and optionally that a follow-up `requeue_interrupted` re-queues the item); and conversely a child that keeps emitting lines within the window is NOT terminated and completes normally (no false trip).
  - Depends on: E-01, E-02, E-03
  - Expected outcome: passing tests pinning all three behaviors (format, group reap, watchdog trip + no-false-trip).
  - Execution state: performed
  - Execution note: commit ed52562; test_runipd.py: `test_heartbeat_idle_formatting_over_60s`/`_under_60s` (a); `test_terminate_process_signals_process_group_with_escalation` + `test_terminate_process_non_posix_fallback` (b); `test_stall_watchdog_terminates_silent_child_and_marks_interrupted` asserting `interrupt_reason=="stall_timeout"`, `status=="interrupted"`, and `requeue_interrupted` re-queues, plus `test_stall_watchdog_does_not_trip_on_active_child` (c). Full suite: Ran 53 tests, OK.

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `Heartbeat` (runipd.py:194-236) is print-only; it tracks `_last_activity` (via `touch()`) and `_start`, printing every `interval` (15s, or 0=disabled in `raw` mode). It does not terminate anything.
- The child is launched with `subprocess.Popen(argv, ..., stdout=PIPE, stderr=STDOUT, bufsize=1)` (runipd.py:1096-1103) with NO `start_new_session`, so children are in the driver's own process group and are not reaped by signaling the opencode PID alone.
- `terminate_process` (runipd.py:1008-1031) already implements SIGINT(5s)->SIGTERM(2s)->SIGKILL on the single process and closes streams; it needs to escalate over the GROUP. Constants `_SIGINT_GRACE_SECONDS`/`_SIGTERM_GRACE_SECONDS` at runipd.py:1004-1005.
- Interrupted-attempt recovery already exists but is STATUS-SPECIFIC: `reconcile_interrupted` (runipd.py:1297-1340) only acts on items still marked `running` and sets them `interrupted`; `requeue_interrupted` (runipd.py:1343-1359) re-queues ONLY `interrupted` items on `resume`. On a NORMAL `run_opencode` return, `execute_item` classifies the turn by exit code via `reconcile_disposition` (runipd.py:1261-1262). Therefore a watchdog kill that merely ends the stream loop and returns normally would be classified `failed-safely` (SIGKILL exit) and would NOT be re-queued. The watchdog MUST surface a distinct condition (a `StallTimeout` exception handled like the existing `KeyboardInterrupt` branch at runipd.py:1230-1238) to force `status="interrupted"`. This dovetails with the pr2nd0 F-05 `interrupted_at` work.
- Tests are run via `python3 tools/ipdrunner/test_runipd.py` (and `python3 -m pytest tools/ipdrunner/test_runipd.py`).
- Migration note: the awocrunner Set (child 01, ckxgx4) moves this file VERBATIM into `agent_workflows/oc_runipd.py`; keeping these edits self-contained in `run_opencode`/`terminate_process`/`Heartbeat` (no new external deps) means they carry over unchanged. Whichever Set lands second re-applies against the moved file.
- Contributor contract: path-scoped commits only, no push, no em/en dashes in user-facing prose.

## Findings

| ID | Severity | Persona | Finding |
|---|---|---|---|
| F-01 | High | Reliability engineer | A non-interactive turn has no per-turn stall timeout; a wedged `hound` MCP web call hung run-553957 for ~12 min until a human killed the tool. runipd must self-heal a stall. |
| F-02 | High | Systems engineer | Child is not started in its own process group and `terminate_process` signals only the opencode PID, so MCP (`hound`) and LSP children orphan on termination. |
| F-03 | Low | UI/UX | The idle duration prints as raw seconds (`381s since last event`), hard to read for multi-minute stalls; should be `XmYs` like the adjacent `elapsed` field. |

## Proposed changes (ordered, validatable)

1. Format `Heartbeat` idle as `XmYs since last event` (output-only).
2. Start the child with `start_new_session=True` and make `terminate_process` reap the whole process group (POSIX; single-process fallback otherwise).
3. Add a stall watchdog to the stream loop that group-reaps a silent turn after `--stall-timeout` and marks the attempt recoverable.
4. Tests for format, group reaping, and watchdog trip/no-false-trip.

## Deferred / out of scope (with reason)

- Bounding the `hound`/MCP tool calls themselves with a client-side timeout (so the remote failure surfaces as a failed tool, not a wedged turn) is a SEPARATE concern (the MCP/runbook prompt layer, not the driver process lifecycle) and is filed as its own backlog item; this IPD makes the DRIVER resilient regardless of any single tool's behavior.
- The general child-lifecycle hardening in pr2nd0 (F-01 signal escalation, F-05 `interrupted_at`) overlaps conceptually; this IPD is scoped to the stall watchdog + group reaping + idle format specifically and does not modify pr2nd0. If pr2nd0 has already landed group-aware termination by execution time, E-02 becomes a verify-and-extend rather than a rewrite (note it in the workflow history).
- No change to the `aw`/packaged runner in THIS plan; the migration note documents how these edits carry into `oc_runipd.py`.

## Scope check

- Over-scope: none. Confined to `run_opencode`, `terminate_process`, `Heartbeat`, a CLI flag, and tests in the runner file + its test.
- Under-scope: none. Covers detection (watchdog), clean teardown (group reap), recoverability (mark interrupted), and the readability fix, with tests.

## Required tests / validation

- `python3 tools/ipdrunner/test_runipd.py` (and/or `python3 -m pytest tools/ipdrunner/test_runipd.py`) green, including the new format/group-reap/watchdog tests.
- Manual: run a turn with a tiny `--stall-timeout` against a stubbed no-output child and confirm it is auto-terminated (whole group; no orphaned children in `ps`) and the attempt is re-queued on `resume`; confirm the progress line shows `XmYs since last event`.
- `pre-commit run --files tools/ipdrunner/runipd.py tools/ipdrunner/test_runipd.py`.

## Spec / documentation sync

- Update the `ipdrunner/` section of `tools/README.md` to mention `--stall-timeout` only if it enumerates flags; otherwise N/A (the awocrunner child 04 owns the broader `aw oc runipd` doc). Note the new flag in `--help` (handled by argparse).

## Open questions

### OQ-01: What default stall-timeout balances long legitimate model/tool turns against real hangs?

- Blocking: no
- Status: deferred
- Owner: author
- Resolution or deferral rationale: RESOLVED with a conservative default of 600s (10 min) which is longer than the ~12-min incident only because that incident was a true hang; a legitimate single tool/model step rarely exceeds several minutes of total silence. Made configurable via `--stall-timeout` (0 disables) so operators tune it. Non-blocking; the value is a constant an operator can override.

### OQ-02: Should `raw` output mode (heartbeat disabled, interval 0) also enforce the stall watchdog?

- Blocking: no
- Status: deferred
- Owner: author
- Resolution or deferral rationale: RESOLVED: the watchdog is independent of the heartbeat PRINTING and should still enforce the timeout in `raw` mode (safety must not depend on verbosity); E-03 wires the watchdog off the stream loop, not the `Heartbeat` print thread. Non-blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted test/manual output showing the progress line renders `XmYs since last event` (e.g. `6m21s since last event`) for a >60s idle.
  - Observed evidence: a 381s idle renders `... (0m00s elapsed, 6m21s since last event)` (matches expected `6m21s since last event`); `test_heartbeat_idle_formatting_over_60s` and `_under_60s` pass. Full pasted output in run-20260825T035151Z-1236581/execution-report.md (V-01).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted test output asserting `terminate_process` signals the process GROUP (killpg) through the SIGINT->SIGTERM->SIGKILL escalation, plus the non-POSIX single-process fallback; and a manual check that after termination no opencode/hound/LSP children remain in `ps`.
  - Observed evidence: `test_terminate_process_signals_process_group_with_escalation` and `test_terminate_process_non_posix_fallback` pass; a live-process demo showed a grandchild (simulating a wedged hound/LSP) sharing the child's pgid and both reaped by `terminate_process` with no orphan surviving (`child alive? False`, `grandchild alive? False`). Full pasted output in run-20260825T035151Z-1236581/execution-report.md (V-02).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted test output showing a no-output child is auto-terminated after a short test `stall_timeout` and its attempt marked interrupted/recoverable, AND a child that keeps emitting lines is NOT terminated (no false trip); the `--stall-timeout` flag present in `--help`.
  - Observed evidence: `test_stall_watchdog_terminates_silent_child_and_marks_interrupted` (no-output child with `--stall-timeout 0.3` ends `status=="interrupted"`, `interrupt_reason=="stall_timeout"`, `stall_timeout==0.3`, and `requeue_interrupted` re-queues `stall1`) and `test_stall_watchdog_does_not_trip_on_active_child` (no false trip) pass; `--stall-timeout` appears in both `start --help` and `resume --help`. Full pasted output in run-20260825T035151Z-1236581/execution-report.md (V-03).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted `python3 tools/ipdrunner/test_runipd.py` (or pytest) output with all new tests passing.
  - Observed evidence: `python3 tools/ipdrunner/test_runipd.py` -> `Ran 53 tests in 3.353s / OK`; `pytest -k "heartbeat_idle or terminate_process_signals or terminate_process_non_posix or stall_watchdog"` -> `6 passed`; `pre-commit run --files tools/ipdrunner/runipd.py tools/ipdrunner/test_runipd.py` -> all hooks Passed. Full pasted output in run-20260825T035151Z-1236581/execution-report.md (V-04).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (make a runipd turn resilient to a silent/wedged tool call) across three tightly-related, single-file changes - detect (watchdog), tear down cleanly (process-group reap), and read clearly (MmSs) - plus their tests. Directly motivated by a real incident.

### Execution contract

1. Open questions RESOLVED: OQ-01 (600s default, configurable) and OQ-02 (watchdog active regardless of output mode) are non-blocking and resolved. No blocking open question remains.
2. Scope fence: touch ONLY `tools/ipdrunner/runipd.py` and `tools/ipdrunner/test_runipd.py`. Keep edits confined to `run_opencode`, `terminate_process`, `Heartbeat`, the argparse flag, and tests, with NO new external dependencies, so the awocrunner verbatim core move carries them over. Do NOT edit `agent_workflows/oc_runipd.py` (it may not exist yet) or the pr2nd0 plan. If a fix seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests/checks passed, paste the ACTUAL runner output (the test run and a manual stall/reap demonstration showing no orphaned children); never claim a pass from narration or an unchecked box.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push. A concurrent runipd run may be active in this tree; leave its edits and state untouched.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit (via the lifecycle workflow).
