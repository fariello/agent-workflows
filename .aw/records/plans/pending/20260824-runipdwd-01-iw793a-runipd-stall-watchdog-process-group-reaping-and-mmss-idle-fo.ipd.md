# IPD: runipd stall watchdog process-group reaping and MmSs idle format

- Date: 2026-08-24
- Kind: child
- Concern: A live incident (run-20260825T010422Z-553957, reviewing IPD 5rzupk) hung for ~12 minutes with no forward progress. Root cause established by inspection: the child agent made a `hound` MCP web tool call that blocked on the network (the `hound` subprocess sat in `ep_poll`, 0 CPU, 6 open sockets), and a non-interactive runipd turn has NO timeout to break out of a wedged tool call, so it hung indefinitely. It only recovered when a human manually killed the `hound` PID. Two runipd defects made this worse: (1) NO stall watchdog - `Heartbeat` (runipd.py:194-236) only PRINTS a "still working ... since last event" line, it never ACTS on a stall; (2) NO process-group reaping - `terminate_process` (runipd.py:1008-1031) and the Popen at runipd.py:1096-1103 signal only the direct opencode PID (no `start_new_session`), so MCP children like `hound` and LSP servers orphan when the turn is killed (this is why the human had to kill `hound` directly rather than the driver reaping it). Additionally the idle counter is printed as raw seconds ("... 381s since last event") rather than MmSs, which is hard to read at a glance for multi-minute stalls.
- Scope: Make runipd self-heal a stalled turn instead of hanging forever: add a stall watchdog that reaps the child turn when no JSONL event arrives for a configurable window and marks the attempt interrupted/failed-safely so `resume` can retry; make child termination kill the whole PROCESS GROUP (opencode + hound + LSP) so no MCP/LSP subprocess orphans; and format the idle duration as `XmYs since last event` (matching the existing `elapsed` format) instead of bare seconds. Land it FIRST on the current standalone `tools/ipdrunner/runipd.py`, and write every change so it migrates unchanged into the packaged `agent_workflows/oc_runipd.py` when the awocrunner Set graduates the runner (the awocrunner core move is verbatim, so behavior-preserving edits here carry over automatically).
- Scope-Paths: tools/ipdrunner/runipd.py, tools/ipdrunner/test_runipd.py
- Status: to-review
- Set: runipdwd
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: iw793a

## Workflow history
- 2026-08-25 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): Completed drafting: fully authored, lint-conforming, ready to critique

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; single-child plan from the run-20260825T010422Z-553957 hung-hound-tool-call incident. Addresses stall watchdog + process-group reaping + MmSs idle format. Designed to land on the current runipd.py and migrate to the aw/oc_runipd.py version.

## Goal

Ensure a runipd turn that stalls on a wedged tool call (or any silent hang) is automatically detected, its whole child process group cleanly reaped (no orphaned MCP/LSP processes), and the attempt recorded as recoverable via `resume` - so no run hangs indefinitely and no human intervention is required; and make the idle duration in the progress output human-readable (`XmYs`).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Human-readable idle duration (smallest, independent)

- [ ] E-01 In `Heartbeat._run` (runipd.py:213-225), format the idle time as `{m}m{s:02d}s since last event` (reusing the same `divmod(..., 60)` shape already used for `elapsed` on the same line at runipd.py:217-218) instead of `{int(idle)}s since last event`. Keep the existing `elapsed` field unchanged. Output-only; no behavior change.
  - Depends on: none
  - Expected outcome: the progress line reads e.g. `(6m21s elapsed, 6m21s since last event)` rather than `(6m21s elapsed, 381s since last event)`.
  - Execution state: pending

### Task group 2: Process-group child so subprocesses can be reaped together

- [ ] E-02 In `run_opencode` (runipd.py:1096-1103), start the child in its own process group/session (`subprocess.Popen(..., start_new_session=True)` on POSIX) so opencode and all its descendants (MCP servers like `hound`, LSP servers) share a killable group. Update `terminate_process` (runipd.py:1008-1031) to signal the whole GROUP (`os.killpg(os.getpgid(pid), sig)`) through the existing SIGINT -> SIGTERM -> SIGKILL escalation (`_SIGINT_GRACE_SECONDS`=5, `_SIGTERM_GRACE_SECONDS`=2), falling back to the single-process path if `getpgid`/`killpg` is unavailable (non-POSIX). Preserve the existing stream-closing behavior.
  - Depends on: none
  - Expected outcome: terminating a turn kills opencode AND its MCP/LSP children (no orphans); verified by asserting the group receives the signal.
  - Execution state: pending

### Task group 3: Stall watchdog that acts on silence

- [ ] E-03 Add a stall watchdog to the streaming loop in `run_opencode` (runipd.py:1107-1126). Track the last-event monotonic time (the loop already calls `heartbeat.touch()` per line at runipd.py:1112). If no JSONL line arrives for a configurable `stall_timeout` (default e.g. 600s; `0`/None disables), reap the child via the E-02 group-aware `terminate_process`, record a distinct reason on the attempt (e.g. `stall_timeout` / status `interrupted` so `reconcile_interrupted`/`requeue_interrupted` re-queue it on `resume`), and return control without hanging. Implement the timeout without blocking indefinitely on `for line in process.stdout` (e.g. a watchdog thread that trips termination, or a bounded read); the reap must be idempotent with the existing `except BaseException: terminate_process(...)` path. Add a `--stall-timeout SECONDS` flag (on `start` and `resume`) plumbed through `state["options"]`, defaulting to the constant; `raw` mode (interval 0) may opt out or keep the default - document the choice.
  - Depends on: E-02
  - Expected outcome: a turn emitting no events for longer than `stall_timeout` is auto-terminated (whole group) and marked interrupted/recoverable, instead of hanging indefinitely as in run-20260825T010422Z-553957.
  - Execution state: pending

### Task group 4: Tests

- [ ] E-04 In `tools/ipdrunner/test_runipd.py`, add tests: (a) `Heartbeat` idle formatting renders `XmYs since last event` for a >60s idle (unit-test the formatting helper, injecting a fake idle/elapsed); (b) `terminate_process` signals the process group (use a fake process exposing a pid + a stubbed `os.killpg`/`getpgid`, assert group signaling and the SIGINT->SIGTERM->SIGKILL escalation, plus the non-POSIX fallback); (c) the stall watchdog trips: a stubbed child that produces no output within a short test `stall_timeout` is terminated and the attempt is marked interrupted/recoverable (assert `terminate_process` was invoked and the attempt reason/status recorded), and conversely a child that keeps emitting lines is NOT terminated.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: passing tests pinning all three behaviors (format, group reap, watchdog trip + no-false-trip).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `Heartbeat` (runipd.py:194-236) is print-only; it tracks `_last_activity` (via `touch()`) and `_start`, printing every `interval` (15s, or 0=disabled in `raw` mode). It does not terminate anything.
- The child is launched with `subprocess.Popen(argv, ..., stdout=PIPE, stderr=STDOUT, bufsize=1)` (runipd.py:1096-1103) with NO `start_new_session`, so children are in the driver's own process group and are not reaped by signaling the opencode PID alone.
- `terminate_process` (runipd.py:1008-1031) already implements SIGINT(5s)->SIGTERM(2s)->SIGKILL on the single process and closes streams; it needs to escalate over the GROUP. Constants `_SIGINT_GRACE_SECONDS`/`_SIGTERM_GRACE_SECONDS` at runipd.py:1004-1005.
- Interrupted-attempt recovery already exists: `reconcile_interrupted` and `requeue_interrupted` re-queue non-terminal attempts on `resume`; the watchdog should mark the attempt so those paths pick it up (this dovetails with the pr2nd0 F-05 `interrupted_at` work).
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

- [ ] V-01 validates E-01
  - Required evidence: pasted test/manual output showing the progress line renders `XmYs since last event` (e.g. `6m21s since last event`) for a >60s idle.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted test output asserting `terminate_process` signals the process GROUP (killpg) through the SIGINT->SIGTERM->SIGKILL escalation, plus the non-POSIX single-process fallback; and a manual check that after termination no opencode/hound/LSP children remain in `ps`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted test output showing a no-output child is auto-terminated after a short test `stall_timeout` and its attempt marked interrupted/recoverable, AND a child that keeps emitting lines is NOT terminated (no false trip); the `--stall-timeout` flag present in `--help`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `python3 tools/ipdrunner/test_runipd.py` (or pytest) output with all new tests passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (make a runipd turn resilient to a silent/wedged tool call) across three tightly-related, single-file changes - detect (watchdog), tear down cleanly (process-group reap), and read clearly (MmSs) - plus their tests. Directly motivated by a real incident.

### Execution contract

1. Open questions RESOLVED: OQ-01 (600s default, configurable) and OQ-02 (watchdog active regardless of output mode) are non-blocking and resolved. No blocking open question remains.
2. Scope fence: touch ONLY `tools/ipdrunner/runipd.py` and `tools/ipdrunner/test_runipd.py`. Keep edits confined to `run_opencode`, `terminate_process`, `Heartbeat`, the argparse flag, and tests, with NO new external dependencies, so the awocrunner verbatim core move carries them over. Do NOT edit `agent_workflows/oc_runipd.py` (it may not exist yet) or the pr2nd0 plan. If a fix seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests/checks passed, paste the ACTUAL runner output (the test run and a manual stall/reap demonstration showing no orphaned children); never claim a pass from narration or an unchecked box.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push. A concurrent runipd run may be active in this tree; leave its edits and state untouched.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit (via the lifecycle workflow).
