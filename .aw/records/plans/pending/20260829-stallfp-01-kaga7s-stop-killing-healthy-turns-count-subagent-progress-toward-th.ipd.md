# IPD: Stop killing healthy turns: count subagent progress toward the stall watchdog and make the heartbeat show the stall countdown

- Date: 2026-08-29
- Kind: child
- Concern: The driver KILLS HEALTHY TURNS. `StallWatchdog` (oc_runipd.py:132-167) and `Heartbeat` are advanced ONLY by lines arriving on the child's stdout (`heartbeat.touch()`/`watchdog.touch()`, oc_runipd.py:1775-1776). When opencode delegates to a Task/subagent, the subagent's work produces NO parent-stdout events - the stdout stream only ever carries `step_start`/`step_finish`/`text`/`tool_use` (verified by tallying every recent `sessions/*.jsonl`) - so the driver sees total silence and at DEFAULT_STALL_TIMEOUT (600.0s, oc_runipd.py:1629) terminates work that was progressing. PROVEN on run-20260829T142239Z-3051088 (review of w0ln4q): the child stdout log `sessions/01-w0ln4q-attempt-1.jsonl` was last written 14:23:40 with a final event of type `tool_use` (the subagent invocation), while opencode's own log shows the spawned child session...` (carrying `parentID=`<child-session>`...`, the turn's session) advancing to step 77 and streaming as late as 14:30:19; the run was then killed with `{"event": "ipd-stalled", "stall_timeout": 600.0}`. Cost: silently discarded long subagent work (hours, repeatedly). SEPARATELY, genuine hangs DO exist (jolfpj on 2026-08-28 blocked forever on an unanswerable `external_directory` permission prompt in a non-interactive `--auto` run, opencode #36868/#43888), so the timeout cannot simply be raised - the fix must DISTINGUISH real progress from a real hang. Compounding the confusion, the heartbeat prints `still working on X (Nm elapsed, Nm since last event)`, which reads as reassurance while a kill countdown is silently running.
- Scope: Make the stall decision progress-aware and the display honest. (1) Add a progress source that observes SUBAGENT activity attributable to the current turn and `touch()`es the watchdog/heartbeat from it, so a turn whose work is inside a Task is not treated as idle. The attribution key exists: opencode's log emits a child-session `created id=<child> ...` line and subsequent child lines carry `parentID=<parent session>`; the driver already knows its turn's session id (it captures it for continuity), so it can match `parentID` to its own session and count that as progress. Treat the log as an OPTIONAL, best-effort signal: if it cannot be read/parsed, behavior degrades to today's stdout-only watchdog (never a hard dependency, never a crash). (2) Make the heartbeat state the countdown instead of implying health: report time since last observed progress AND the remaining time before the stall kill (e.g. `no progress 7m30s; stall kill in 2m30s`), and name WHICH source last showed progress (stdout vs subagent). (3) Preserve the true-hang guarantee: an unanswerable permission prompt still produces no progress from EITHER source and must still be killed at the timeout. Apply to BOTH drivers (`oc_runipd.py` and `agy_runipd.py`) and their shared renderer (`render_stream.Heartbeat`, which both import).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/render_stream.py, tests/
- Item-Dependencies: none
- Status: to-review
- Set: stallfp
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: kaga7s

## Workflow history
- 2026-08-29 to-review (aw set): Authored review-ready: subagent progress must count toward the stall watchdog; heartbeat must show the kill countdown. Evidence-backed by run-20260829T142239Z (healthy turn killed) and jolfpj (true hang preserved).

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Stop the driver from terminating turns that are genuinely progressing inside a subagent, by feeding subagent activity into the stall watchdog, while keeping the real-hang kill intact and making the heartbeat state the actual countdown instead of implying everything is fine.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: observe subagent progress

- [ ] E-01 Add a progress observer (a small module or a class alongside `StallWatchdog`) that tails opencode's log and yields "progress at time T" whenever it sees a line whose `parentID=` equals the CURRENT turn's session id, or a `created id=<child> ...` line spawned by it (so a freshly spawned subagent counts immediately, before its first `parentID` line). It MUST be best-effort: unreadable/missing/rotated log, unparseable lines, or an unknown session id degrade silently to yielding nothing. It must not block, must not raise into the turn, and must be bounded (tail from the current offset only; never re-read a 140MB+ file from the start).
  - Depends on: none
  - Expected outcome: given a log containing child lines with `parentID=<our session>`, the observer reports progress timestamps; given an unreadable or irrelevant log it reports nothing and raises nothing.
  - Execution state: pending

- [ ] E-02 Wire the observer into the turn loop in `oc_runipd.py` so it `touch()`es BOTH `heartbeat` and `watchdog` on observed subagent progress, alongside the existing stdout touches at oc_runipd.py:1775-1776. Record which source last showed progress (`stdout` or `subagent`) so the display can name it. Do NOT change the timeout value or the kill path.
  - Depends on: E-01
  - Expected outcome: a turn that emits no stdout but whose subagent is active is NOT killed at the timeout; the watchdog's idle clock resets from subagent progress.
  - Execution state: pending

- [ ] E-03 Apply the same wiring to `agy_runipd.py`, which carries its own copy of the watchdog/heartbeat integration (its Heartbeat lines are at agy_runipd.py:274-275). Prefer importing the shared observer rather than duplicating it, so the two drivers cannot drift.
  - Depends on: E-01
  - Expected outcome: `aw agy run` gets identical protection; a grep shows one observer implementation imported by both drivers, not two copies.
  - Execution state: pending

### Task group 2: honest countdown display

- [ ] E-04 Change `render_stream.Heartbeat` (render_stream.py:229-258, imported by both drivers) so its line states the countdown and the progress source instead of only "still working": report time since last OBSERVED PROGRESS and the remaining time until the stall kill, and name the source of the last progress. Keep the line a single short stderr line in the existing shape/format conventions (no color dependence for meaning).
  - Depends on: E-02
  - Expected outcome: during a quiet stretch the user sees the shrinking time-to-kill and whether progress is coming from stdout or a subagent, instead of an unqualified "still working".
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `StallWatchdog` (oc_runipd.py:132-167) is a daemon thread comparing `time.monotonic() - self._last_activity` against `self.timeout`, terminating the child via `terminate_process`. `touch()` is the only way to reset it, and it is called from exactly two places (oc_runipd.py:1775-1776), both inside `for line in process.stdout`.
- `DEFAULT_STALL_TIMEOUT = 600.0` (oc_runipd.py:1629); it is already overridable per run via `options["stall_timeout"]` / `--stall-timeout`, so the fix does not need a new knob.
- `Heartbeat` lives in the SHARED `render_stream.py` (:229-258) and is imported by both drivers, so a display change lands once. The watchdog wiring, however, is duplicated per driver (agy_runipd.py:274-275 mirrors it) - the `dhuape` backlog item tracks the broader unification.
- The child stdout event vocabulary is only `step_start`/`step_finish`/`text`/`tool_use` (tallied across recent `sessions/*.jsonl`); there is NO subagent-progress event on stdout, which is why an out-of-band signal is required.
- The driver already captures the turn's opencode session id (it prints session-continuity hints), so the parent-session key needed for `parentID` attribution is available without new plumbing.

## Findings

- ROOT CAUSE: the stall decision is stdout-only. Subagent work is invisible to it, so "no stdout" is wrongly equated with "no progress".
- EVIDENCE (false positive): run-20260829T142239Z-3051088 reviewing w0ln4q. `sessions/01-w0ln4q-attempt-1.jsonl` last written 14:23:40, final event type `tool_use` (the Task call). opencode's log shows the child session...` with `parentID=`<child-session>`...` reaching step 77 and streaming at 14:30:19. Killed at 14:33:40 with `{"event":"ipd-stalled","stall_timeout":600.0}` - i.e. ~10 minutes of real subagent work discarded.
- EVIDENCE (true positive, must be preserved): jolfpj on 2026-08-28 logged `message=asking ... permission=external_directory patterns=["<repo-root>/*"]` in a non-interactive `--auto` run and then produced nothing from ANY source; the same watchdog correctly ended it. Upstream context: opencode #36868 / #43888.
- THE DISCRIMINATOR: in the false-positive case a child session attributable to our turn was advancing; in the true-hang case nothing advanced anywhere. So subagent-attributable activity is exactly the missing signal, and `parentID=` is the attribution key (verified present on child lines).
- The heartbeat's current wording actively misleads: it says "still working" while a kill countdown runs, which is why a stalled-but-doomed turn is indistinguishable from a healthy one at a glance.
- HONEST LIMIT: reading opencode's log is coupling to another tool's internal artifact - format/location may change across versions. Hence it MUST be best-effort and degrade to today's behavior, and the plan pins the observed version (1.18.25, seen in the `created ... version=` line) in the test fixture rather than assuming stability.

## Proposed changes (ordered, validatable)

1. New shared progress observer: tail opencode's log from the current offset, emit progress when a line's `parentID` matches the turn's session (or a `created` line spawns a child for it); fully best-effort.
2. `oc_runipd.py`: touch heartbeat+watchdog from the observer as well as stdout; track last-progress source.
3. `agy_runipd.py`: same wiring via the shared observer (no second implementation).
4. `render_stream.Heartbeat`: state time-since-progress, time-to-kill, and the progress source.
5. `tests/`: false-positive regression, true-hang preservation, best-effort degradation, and the display assertions.

## Deferred / out of scope (with reason)

- Fixing the upstream opencode subagent-permission hang (#36868/#43888): not ours to fix; this plan makes the driver survive and correctly classify it.
- Raising or removing `DEFAULT_STALL_TIMEOUT`: deliberately NOT done. Raising it would delay real-hang detection and does not fix the wrong signal; the timeout stays 600s and becomes meaningful once progress is measured correctly.
- Emitting subagent progress into the run ledger (`events.jsonl`) for `aw runs` visibility: valuable but separate reporting work; tracked by backlog `em0z50` (per-artifact disposition lines + end-of-run summary).
- Broader unification of the two drivers: backlog `dhuape`; this plan shares only the observer.

## Scope check

- Over-scope: none.
- Under-scope: none (observer + both drivers + shared display + tests is the complete fix; fixing only oc would leave `aw agy run` killing healthy turns).

## Required tests / validation

- FALSE-POSITIVE REGRESSION (the bug): stdout goes quiet after a `tool_use` while an attributable subagent is active -> turn survives, no `ipd-stalled`. Must fail before the fix.
- TRUE-HANG PRESERVATION: no stdout and no attributable subagent activity -> still killed at the timeout, `ipd-stalled` recorded.
- ATTRIBUTION: a child session with a DIFFERENT `parentID` does not count as our progress.
- DEGRADATION: missing / unreadable / garbage log -> observer returns nothing, raises nothing, watchdog behaves as today.
- BOUNDEDNESS: observer reads from its start offset only (no full re-read of a large log).
- BOTH DRIVERS: the regression is asserted for oc AND agy; one shared observer (grep proves no duplicate).
- DISPLAY: heartbeat shows time-since-progress + a DECREASING time-to-kill + the progress source; bare "still working" gone.

Validation command: `python3 -m pytest tests/test_stall_progress.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_render_stream.py -q` plus a full default suite `python3 -m pytest -p no:randomly` (paste ACTUAL output; never claim success unrun).

## Spec / documentation sync

- Update the `--stall-timeout` CLI help to say the timeout measures time since last observed progress (stdout OR subagent), not merely stdout silence.
- Note the best-effort opencode-log coupling near the observer so a future reader knows it is an optional signal, not a contract.

## Open questions

### OQ-01: Should the driver depend on opencode's internal log at all, or wait for an upstream subagent-progress event on stdout?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: Use the log now, as a BEST-EFFORT signal only. Waiting for upstream is not viable: the failure is active and expensive (hours of discarded work, twice in 14 hours), and we do not control opencode's release cadence. The coupling risk is real but bounded by the fail-safe rule - if the log's location or format changes, the observer yields nothing and we degrade to exactly today's behavior rather than breaking. If opencode later emits subagent progress on stdout, that becomes a second progress source and the log observer can be dropped without changing the watchdog contract.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Pasted output of a named unit test (e.g. `tests/test_stall_progress.py`) that feeds the observer a FIXTURE log (pinned to the observed opencode format, version 1.18.25) containing: a `created id=<child> ... version=1.18.25` line for our session, subsequent child lines carrying `parentID=<our session>`, and unrelated lines carrying a DIFFERENT `parentID`. Assert it reports progress for ours and NOT for the unrelated ones (no false attribution). Plus three degradation cases each asserting "returns nothing, raises nothing": missing file, unreadable/permission-denied file, and garbage/truncated lines. Plus an assertion that it reads only from the current offset (e.g. it does not re-read content written before it started; prove with a pre-seeded large fixture).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: THE FALSE-POSITIVE REGRESSION, pasted: a test that drives a fake child which emits a `tool_use` on stdout and then NOTHING on stdout, while a fixture log shows child-session activity attributable to the turn, with a SHORT `stall_timeout` (e.g. 2s) so the test is fast. Assert the turn is NOT terminated and no `ipd-stalled` event is recorded - this is exactly the w0ln4q failure and MUST fail before the fix and pass after. Plus a test asserting the recorded last-progress source is `subagent` in that case and `stdout` when stdout is active.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: The same false-positive regression for the agy driver, pasted from `tests/test_agy_runipd_cli.py` (or the agy equivalent), proving `aw agy run` also survives a subagent-only stretch. PLUS `grep -c "def .*progress_observer\|class .*ProgressObserver" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` showing 0 in BOTH (the observer lives in one shared module, not copied), and a grep showing both import it.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted test output asserting the heartbeat line contains BOTH the time since last observed progress AND the remaining time before the stall kill, and names the progress source. Assert the countdown DECREASES across two successive renders with a fixed clock (e.g. "stall kill in 2m30s" then "... 2m15s"), so it is a real countdown and not static text. Assert the phrase "still working" alone (with no countdown) no longer appears. THE TRUE-HANG PRESERVATION TEST, also pasted: with NO stdout and NO attributable subagent activity, the watchdog still fires at the timeout and the run records `ipd-stalled` - proving the fix did not disable real-hang detection. Finally paste a full default-suite run `python3 -m pytest -p no:randomly` summary line showing green.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (make the stall decision progress-aware and the display honest); E-items are ordered sub-steps (observer -> oc wiring -> agy wiring -> display).

Execution contract:

1. Open questions: OQ-01 resolved; execution requires explicit human approval.
2. Scope fence: touch ONLY `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `agent_workflows/render_stream.py`, and `tests/` (plus the one new observer module). Do NOT change `DEFAULT_STALL_TIMEOUT`, do NOT alter the kill path, and do NOT attempt to fix the upstream opencode permission hang. If the work seems to need more, STOP and report.
3. Honesty rule (HARD MUST): every V-item's Observed evidence is the ACTUAL pasted output of the named command. A V-item whose test was not run stays `Result: pending`.
4. Fail-safe rule: the log observer is BEST-EFFORT. It must never raise into the turn, never block, and never become a hard dependency; if it cannot read or parse, behavior degrades to today's stdout-only watchdog. A missing log must not turn into a hung or crashed run.
5. Do-not-weaken rule: the true-hang kill MUST survive. If a change makes V-04's true-hang test pass only by lengthening or disabling the timeout, that is a failure - the guarantee is "no progress from any source for the timeout => killed".
6. Commit ONLY this plan's own changed files, path-scoped; never `git add -A`/bare/`-a`; never push; never `--no-verify`.
7. Lifecycle move on completion: verify all V items with pasted output, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`.
