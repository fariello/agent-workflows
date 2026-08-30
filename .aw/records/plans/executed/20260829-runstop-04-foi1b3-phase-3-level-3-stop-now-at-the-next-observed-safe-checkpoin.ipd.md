# IPD: Phase 3: level 3 stop-now at the next observed safe checkpoint with KNOWN disposition

- Date: 2026-08-29
- Kind: child
- Blocks-Release: next
- From-Backlog: kjzlgw
- Concern: Spec c4gd2h level 3 (STOP-NOW) stops the CURRENT agent turn at its next SAFE checkpoint rather than letting it finish, and because it stopped at a DEFINED point the interrupted item's disposition is KNOWN (recorded stopped/incomplete, never `unknown_outcome`). This is the level that makes SIGTERM meaningful instead of fatal. Spec OQ-01 is RESOLVED: no agent cooperation is needed, because the driver already consumes the child's structured event stream line-by-line (`oc_runipd.py:1765-1786`, `--format json`) and the session JSONL carries discrete `step_start`/`tool_use` records, so the driver can define a safe checkpoint unilaterally.
- Scope: Implement level 3 in BOTH drivers: define a SAFE CHECKPOINT as the instant after a completed tool/step event and before the next is dispatched (observable from the existing stream loop, spec R10), stop the turn there, record the interrupted item with KNOWN certainty, and end in the Phase-0 `clean_shutdown`. Does NOT implement the immediate interrupt or `unknown_outcome` (Phase 4), signal handlers, or the CLI verb (Phase 5).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_stop.py, tests/test_runner_stop_level3.py
- Item-Dependencies: executed:1qxuke
- Status: executed
- Set: runstop
- Order: 4
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: foi1b3

## Workflow history
- 2026-08-30 executed (opencode (its_direct/pt3-claude-opus-5-1m-us)): Level 3 (STOP-NOW) in BOTH drivers: the safe checkpoint is OBSERVED from the child's own event stream (re-verified vocabulary: 122 step_start / 122 step_finish / 135 all-completed tool_use / 85 text), parsed independently of output_mode so it fires under clean, raw, AND quiet, with each driver reading its OWN schema. The stop routes through Phase 0's clean_shutdown (observed reaping the child pid), and reconcile_disposition now intercepts the deliberate stop so it is recorded interrupted + certainty known + last completed operation instead of the failed-safely the fallback produced. Bounded wait detected out-of-band (sub-second injected deadline, silent child, 4.69s) with escalation recorded but NOT performed (Phase 5's job). 46 new tests; both blocker defects mutation-verified as genuinely caught; zero net-new full-suite failures measured against a clean base worktree (19 == 19, failure sets identical). [Scope reconciliation - in-scope-unmodified agent_workflows/agy_runipd.py: MODIFIED by this execution in commit 0c564a50; appears unmodified only because the stale-digest gate forced a second `aw ipd begin` AFTER that commit, which re-froze base_head to it. NOT not-needed: the suggested wording would be false.; in-scope-unmodified agent_workflows/oc_runipd.py: MODIFIED by this execution in commit 0c564a50; appears unmodified only because the stale-digest gate forced a second `aw ipd begin` AFTER that commit, which re-froze base_head to it. NOT not-needed: the suggested wording would be false.; in-scope-unmodified agent_workflows/runner_stop.py: MODIFIED by this execution in commit 0c564a50; appears unmodified only because the stale-digest gate forced a second `aw ipd begin` AFTER that commit, which re-froze base_head to it. NOT not-needed: the suggested wording would be false.; in-scope-unmodified tests/test_runner_stop_level3.py: MODIFIED by this execution in commit 0c564a50; appears unmodified only because the stale-digest gate forced a second `aw ipd begin` AFTER that commit, which re-froze base_head to it. NOT not-needed: the suggested wording would be false.]
- 2026-08-29 approved (aw set): status set to approved
- 2026-08-29 /plan-review (OpenCode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-401..PR-407. Confirmed the spec OQ-01 evidence is REAL by parsing the cited session file (135 `tool_use`, every one carrying `part.state.status == "completed"`, plus 122 `step_start`, 122 `step_finish`, 85 `text`), so completion is an observed field and `step_finish` is the cleaner boundary. Then found two BLOCKERs. (1) Nothing owned the disposition path: a level-3 stop leaves NO outcome JSON (the runbook has the agent write it at turn end), the plan is not in `executed/`, and the terminated child exits nonzero, so `reconcile_disposition` falls through to `return ("partial" if exit_code == 0 else "failed-safely")` (`oc_runipd.py:1848`) and records a DELIBERATE operator stop as `failed-safely` - the exact crash-versus-intent conflation spec R21 forbids and a verdict R22 forbids. E-03 now owns intercepting it, and V-03 FAILS on a pasted `failed-safely`/`partial` and additionally requires a control case proving genuine failures still reconcile normally. (2) E-01 pinned checkpoint detection to `render_event`, which is invoked ONLY under `output_mode == "clean"` (:1780-1781), so the whole feature would silently never fire under `raw`/`quiet`; E-01 now requires mode-independent parsing and V-01 requires all three modes. Also corrected the honesty of the mechanism: the child is a one-shot `opencode run` with no stop channel and the cited `StallWatchdog` precedent calls `terminate_process` (:159-169), so level 3 is termination at an observed boundary and shares its mechanism with level 4, differing only in timing - "KNOWN" means no previously observed operation was cut mid-flight, not that the agent finished tidily. Recorded the oc-vs-agy event-schema asymmetry (`tool_use`/`state.status` vs `step_update`/`DONE`) for CID-3, noted that a blocking `for line in process.stdout` cannot notice a deadline so E-04 needs the out-of-band watchdog shape, required a short injected deadline so V-04 cannot pass by waiting out a real budget, fixed the off-by-one poll citation (:1774-1775 -> :1775-1776), aligned the R4 assertion with `2ouj70`'s observe-and-report semantics, and switched full-suite evidence to `make test-all`.
- 2026-08-29 reviewed (aw set): status set to reviewed
- 2026-08-29 to-review (aw set): Authored review-ready from spec c4gd2h (graduation of backlog kjzlgw).

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.

## Goal

Implement level 3 (STOP-NOW): interrupt the current agent turn at the next OBSERVED safe checkpoint derived from the child's own event stream, so the interrupted item's disposition is KNOWN rather than indeterminate (spec R10, R18, A3), with no agent cooperation and no prompt/protocol change.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the observable safe checkpoint

- [x] E-01 In BOTH drivers, define and implement the SAFE CHECKPOINT as the instant AFTER a COMPLETED tool/step event and BEFORE the next is dispatched, derived from the existing per-line event loop (`oc_runipd.py:1772-1783`). Verified against the cited real session JSONL: a `tool_use` event carries `part.state.status`, and all 135 `tool_use` records in that file have `status == "completed"`, so "completed" is an OBSERVED field, not an inference; the file also holds 122 `step_start` and 122 `step_finish` records, so `step_finish` is the cleaner completion signal than `step_start`. Prefer `step_finish` / `tool_use` with `state.status == "completed"`, and treat any other status as NOT a checkpoint. IMPORTANT correction: the checkpoint detection MUST NOT be built on `render_event`, which is invoked ONLY in `clean` output mode (`oc_runipd.py:1780-1781`); in `raw` and `quiet` modes no event is parsed at all, so a `render_event`-based checkpoint would silently never fire in those modes. Parse the event type in the per-line loop independently of `output_mode` (a minimal `json.loads` + type/status read, reusing `render_stream`'s field names, not its rendering). For `agy_runipd.py` the equivalent completion signal is `step_update` with `state == "DONE"` (`agy_runipd.py:217`, :226), not the oc field names; do not assume one schema across both drivers. No agent cooperation, no time-based condition (spec R10).
  - Depends on: none
  - Expected outcome: a helper reports "at a safe checkpoint" only immediately after a COMPLETED event line is consumed, in ALL THREE output modes (`clean`, `raw`, `quiet`); a test feeding a partial/interleaved line, and one feeding a non-completed status, show it does NOT report a checkpoint; and the agy path is driven by `step_update`/`DONE` rather than the oc field names.
  - Execution state: performed
- [x] E-02 On a level-3 request observed by the Phase-1 poll at the per-line point (beside `heartbeat.touch()`/`watchdog.touch()`, `oc_runipd.py:1775-1776`; `agy_runipd.py:1844-1845`), stop the current turn at the next safe checkpoint, then route to `runner_shutdown.clean_shutdown(...)` rather than performing local teardown (spec R5). BE HONEST ABOUT THE MECHANISM: the child is a ONE-SHOT `opencode run ...` subprocess (`oc_runipd.py:1694`, argv built :1694-1740) with NO cooperative stop channel - there is no "please wind down" input the driver can send it. So "stopping the turn at a checkpoint" is implemented as TERMINATING the child (via Phase 0's `clean_shutdown`, which owns the reaper) at a moment chosen by observation. The cited precedent does exactly this: `StallWatchdog._run` calls `terminate_process(self.process)` when it fires (`oc_runipd.py:159-169`). Therefore level 3 and level 4 use the SAME kill mechanism and differ ONLY in WHEN it is issued (level 3 waits for an observed completed-event boundary; level 4 does not wait). Record that plainly in the code comment so no reader believes the child is being asked to cooperate. Any interruption of a tool the driver cannot see inside remains impossible; the checkpoint guarantees only that no PREVIOUSLY OBSERVED operation was cut mid-flight.
  - Depends on: E-01
  - Expected outcome: with a fake child emitting 5 scripted events and a level-3 request after event 2, the turn stops after the next COMPLETED event (never mid-event), the child and its group are reaped through `clean_shutdown`, and the four Phase-0 invariants hold; the code comment states that the mechanism is termination-at-an-observed-boundary, not agent cooperation.
  - Execution state: performed

### Task group 2: KNOWN disposition

- [x] E-03 Record the interrupted item per spec R18 with KNOWN certainty: the level that interrupted it, the last completed operation observed, the observed git state, and what a resume must do first. It MUST NOT be recorded `unknown_outcome` (that is level 4 only) and MUST NOT be recorded executed/complete/successful (spec R22). This REQUIRES intercepting the existing disposition path, which today would MISREPORT the stop: a level-3 stop leaves no outcome JSON (the runbook has the agent write `outcomes/<NN>-<id6>.json` at turn END, so a mid-turn stop never produces it), the plan is not in `executed/`, and the terminated child exits nonzero - so `reconcile_disposition` (`oc_runipd.py:1813-1848`) falls through to its final `return ("partial" if exit_code == 0 else "failed-safely")` at :1848 and labels a DELIBERATE operator stop as `failed-safely`. That is precisely the crash-versus-intent conflation spec R21 forbids and the fabricated verdict R22 forbids. So this E-item must add a deliberate-stop branch to `reconcile_disposition` (both drivers) that runs BEFORE the outcome/exit-code fallback and yields a stopped/incomplete disposition carrying level + KNOWN certainty, rather than letting the existing fallback assign a failure.
  - Depends on: E-02
  - Expected outcome: the ledger shows the interrupted item as stopped/incomplete with KNOWN certainty and the last completed event index/name; it is NOT `failed-safely` and NOT `partial`; zero `unknown_outcome` entries exist after a level-3 stop; and a genuine failure (no stop requested) still reconciles to `failed-safely` as before.
  - Execution state: performed

### Task group 3: bounded wait

- [x] E-04 Detect and RECORD a wind-down budget breach (spec R11, OQ-01) when no further event arrives after a level-3 request so no checkpoint is reachable, using the deadline recorded by Phase 1. Record the breach as an escalation-required signal; do NOT perform the escalation here (Phase 5 owns it, spec A7). Note the deliberate R10 boundary, so no reader thinks this contradicts it: R10 forbids defining the SAFE CHECKPOINT by elapsed time, and this deadline does not do that - it defines only the GIVE-UP point after which no checkpoint will be awaited. Both facts must be stated in the code comment, since a later reader could otherwise "simplify" the checkpoint into a timeout. Blocking-read caveat: the per-line loop `for line in process.stdout` BLOCKS when a child goes silent, so a deadline cannot be noticed from inside that iteration; the breach detector therefore needs the out-of-band supervisor shape `StallWatchdog` already uses (a daemon thread observing the process, `oc_runipd.py:159-169`), not a check placed after the next line arrives.
  - Depends on: E-02
  - Expected outcome: with a fake child that goes silent after a level-3 request, the driver records a budget-breach/escalation-required marker within a bounded time of the Phase-1 deadline and does not wait indefinitely, PROVEN with a short injected deadline (sub-second) so the test cannot pass by waiting out a real multi-minute budget; the marker is the single signal Phase 5 will act on; no escalation action is taken here.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Spec OQ-01 RESOLVED, with the mechanism already present: `oc_runipd.py:1765-1786` spawns the child with `--format json` and iterates `for line in process.stdout`, and the captured session JSONL for a real run contains `{"type":"step_start",...}` and `{"type":"tool_use",...}` records (verified against `.aw/records/runs/run-20260829T053827Z-2084502/sessions/01-jolfpj-attempt-1.jsonl`). A safe checkpoint is therefore observable by the driver alone.
- `StallWatchdog` (`oc_runipd.py:1769`, touched per line at :1776) is the in-repo PRECEDENT for the driver acting on stream observation - and note what it DOES when it fires: `terminate_process(self.process)` (:159-169). So the precedent for "the driver stops a turn" is a KILL, which is why level 3's mechanism is termination at an observed boundary (see E-02), not cooperative shutdown.
- The child is a one-shot `opencode run` subprocess with no stop channel: argv is built at `oc_runipd.py:1694-1740` (`--format json`, `--session`, `--dir`, prompt) and the driver's only controls over a running turn are reading its stdout and signalling it. There is no prompt-level or IPC "wind down" affordance, and adding one is an explicit spec non-goal (OQ-01 resolution).
- Phase 1 (`gq6m2u`) already polls at the per-line point beside `heartbeat.touch()`/`watchdog.touch()` (`oc_runipd.py:1775-1776`; `agy_runipd.py:1844-1845`; the original draft's :1774-1775 was off by one), which is exactly where a level-3 request must be noticed.
- Phase 0 (`2ouj70`) owns the reaper and the invariants; level 3 must END in `clean_shutdown`, not perform its own teardown (spec R5). Note `2ouj70`'s reviewed R4 semantics are OBSERVE-AND-REPORT, so this child asserts the tree is UNCHANGED by cleanup, not that it is clean.
- `render_event` lives in `render_stream.py:135` and is called ONLY under `output_mode == "clean"` (`oc_runipd.py:1780-1781`). In `raw` and `quiet` modes nothing parses the event line, so checkpoint detection must NOT depend on `render_event` or it will never fire in those modes.
- Event-schema asymmetry between drivers (relevant to CID-3): oc emits `{"type": "tool_use", "part": {"state": {"status": "completed"}}}` and `step_start`/`step_finish` (verified counts in the cited session file: 135 `tool_use` all `completed`, 122 `step_start`, 122 `step_finish`, 85 `text`), while agy emits `step_update` with `state == "DONE"` (`agy_runipd.py:188-226`). The two drivers need the same SEMANTICS with different field reads.
- The per-item outcome JSON is written by the agent at turn END (runbook step 6), so a mid-turn stop yields NO outcome file. Combined with `reconcile_disposition`'s fallback (`oc_runipd.py:1848`), an un-intercepted level-3 stop is recorded `failed-safely`.
- Validation-command trap: default `addopts` (`pyproject.toml:122`) is `-m 'not slow'`, so a bare `python -m pytest -q` deselects `slow` subprocess tests; use `make test-all` for full-suite evidence.

## Findings

The definition of SAFE must be observable, per spec R10 (no elapsed-time definitions):

| Candidate boundary | Observable? | Verdict |
|---|---|---|
| after a completed `tool_use`/step event, before the next dispatch | yes, from the existing stream loop | CHOSEN |
| mid-tool-call | no (driver cannot see inside the tool) | rejected |
| after N seconds | yes but time-based | rejected by R10 |
| agent-emitted checkpoint marker | requires prompt change + per-agent negotiation | rejected (OQ-01) |

Why KNOWN certainty follows: because the driver stops between discrete events it has already observed, it knows the last completed operation, so the interrupted item's disposition is recorded as stopped/incomplete with that position (spec R18). This is the ONLY difference from Phase 4's level 4 (spec: "the only difference between 3 and 4 is outcome CERTAINTY, not cleanliness").

VERIFIED, and it narrows what "KNOWN" may claim (2026-08-29). The cited session file is real and its event vocabulary is exactly as the spec's OQ-01 resolution assumed: 135 `tool_use` (every one carrying `part.state.status == "completed"`), 122 `step_start`, 122 `step_finish`, 85 `text`. So completion is an OBSERVED field rather than an inference, and `step_finish` is a cleaner boundary than `step_start`. But two limits follow that the original draft did not state:

1. The stop is a TERMINATION, not a cooperative wind-down. The child is a one-shot `opencode run` with no stop channel, and the in-repo precedent for driver-initiated stopping (`StallWatchdog`) calls `terminate_process`. Level 3 and level 4 therefore share one mechanism and differ only in the instant it fires. "KNOWN" means "no PREVIOUSLY OBSERVED operation was cut mid-flight", NOT "the agent finished tidily" - the agent may still have had unflushed intent, and any write it began after its last emitted event is unobserved.
2. Uncommitted work is NOT covered by the checkpoint. The runbook has the agent commit its own changes and write the outcome JSON at turn END, so a checkpoint stop typically leaves work committed-or-not depending on where the agent was, and leaves NO outcome file. That is why E-03 must intercept the disposition path rather than trust it.

VERIFIED failure of the existing disposition path (2026-08-29). With no outcome file, the plan not in `executed/`, and a terminated child exiting nonzero, `reconcile_disposition` reaches its final fallback `return ("partial" if exit_code == 0 else "failed-safely")` (`oc_runipd.py:1848`) and records a deliberate operator stop as **`failed-safely`**. That conflates intent with breakage (spec R21) and asserts a verdict the driver did not establish (spec R22). E-03 now owns intercepting it; without that interception this child would satisfy its own V-03 wording while still writing a false disposition.

R10 boundary, stated deliberately: R10 forbids defining the safe CHECKPOINT by elapsed time. E-04's deadline is not a checkpoint definition, it is the give-up bound after which no checkpoint is awaited. Also note `for line in process.stdout` BLOCKS on a silent child, so the breach cannot be detected inside the per-line loop; it needs the out-of-band watchdog-style thread.

A bounded-wait obligation exists: if no further event arrives after a level-3 request, the driver cannot reach a checkpoint. The wind-down budget recorded in Phase 1 (spec R11) governs that wait; exceeding it must ESCALATE to level 4 with the escalation recorded, never hang. Escalation ENFORCEMENT is Phase 5 (spec A7), so this child records the deadline breach and defers the escalation action, which a V-item pins.

## Proposed changes (ordered, validatable)

1. Define the safe checkpoint from the existing per-line event stream, parsed independently of `output_mode` (which `render_event` is not), with per-driver field reads: oc `step_finish`/`tool_use` + `state.status == "completed"`, agy `step_update` + `state == "DONE"`.
2. On a level-3 request, terminate the turn at that observed boundary in both drivers via `clean_shutdown`, documenting that the mechanism is termination-at-a-boundary rather than agent cooperation.
3. Intercept `reconcile_disposition` so a deliberate stop records stopped/incomplete with KNOWN certainty and the last completed operation (spec R18), instead of falling through to `failed-safely`.
4. Detect and record a budget breach from an out-of-band watchdog-style thread (the blocking stdout read cannot notice it), leaving escalation to Phase 5.
5. New `tests/test_runner_stop_level3.py` driving a fake child with the real event vocabularies, covering all three output modes, the non-completed-status case, the disposition control case, and a short injected breach deadline.

## Deferred / out of scope (with reason)

- The immediate interrupt, `unknown_outcome`, and resume refusal: Phase 4 (`m0z0ti`).
- Signal handlers and `aw oc/agy run stop`: Phase 5 (`71vjbn`); tests here request level 3 by writing the Phase-1 record.
- ENFORCING escalation on a budget breach: Phase 5 (spec A7). This child records the breach so Phase 5 has one authoritative signal to act on.
- Any change to the agent prompt or a per-agent capability handshake: explicitly rejected by spec OQ-01's resolution.

## Scope check

- Over-scope: none. No immediate interrupt, no signals, no CLI. E-03's touch on `reconcile_disposition` is in-scope, not scope creep: without it the level cannot record an honest disposition at all.
- Under-scope: as originally written, YES, in two ways now fixed. (1) Nothing owned intercepting `reconcile_disposition`, whose fallback records a deliberate stop as `failed-safely` (`oc_runipd.py:1848`), so R18/R21/R22 were unmet while V-03's wording could still be satisfied; E-03 now owns it and V-03 fails on that value. (2) Checkpoint detection was pinned to `render_event`, which runs only in `clean` output mode, so the feature would silently not work under `raw`/`quiet`; E-01 now requires mode-independent parsing and V-01 requires all three modes. The observable checkpoint definition (R10), stop-at-checkpoint (A3), the KNOWN disposition record (R18), and budget-breach detection (R11) each have an E-item and a 1:1 V-item.

## Required tests / validation

- `python -m pytest tests/test_runner_stop_level3.py -q -m ''` passes (pass `-m ''` so `slow`-marked subprocess tests in this file are not silently deselected).
- Spec acceptance A3 is demonstrated: the turn stops at a checkpoint, the item is recorded stopped/incomplete with KNOWN certainty (explicitly NOT `unknown_outcome`, and explicitly NOT `failed-safely`/`partial`), and the four Phase-0 invariants hold with R4 asserted as "unchanged by cleanup".
- The fake child emits scripted events using the REAL vocabularies: `step_finish` / `tool_use` with `part.state.status == "completed"` for the oc path, and `step_update` with `state == "DONE"` for the agy path. A non-completed status and a partial line are both tested as non-checkpoints.
- Checkpoint detection is proven in all three output modes (`clean`, `raw`, `quiet`).
- A test proves the stop happens after a COMPLETED event, not mid-event, by asserting the last observed event's index and status.
- A CONTROL test proves a genuine failure (no stop requested) still reconciles to `failed-safely`, so the deliberate-stop branch does not mask real failures.
- The budget-breach test uses a short injected deadline and asserts bounded elapsed time, with the child silent.
- No test uses a wall-clock sleep to define the CHECKPOINT (spec R10); the give-up deadline is time-based by design and is not a checkpoint.
- `make test-all` (`python -m pytest tests/ -m ''`) remains green: the FULL suite, since a bare `python -m pytest -q` deselects `-m 'not slow'` per `pyproject.toml:122`.

## Spec / documentation sync

- Record in the driver comment that the safe-checkpoint definition is spec c4gd2h OQ-01's resolution, citing the event-stream mechanism, so a future reader does not reintroduce an agent-cooperation handshake.
- Record in the same comment that the stop MECHANISM is termination at an observed boundary (the child is one-shot with no stop channel; `StallWatchdog` is the precedent), that level 3 and level 4 share it and differ only in timing, and that "KNOWN" therefore means "no previously observed operation was cut mid-flight" rather than "the agent finished tidily". This is the honesty boundary a reader is most likely to overstate.
- Record why the checkpoint parse is independent of `output_mode` (because `render_event` runs only in `clean`), so a later refactor does not route it back through `render_event`.
- No user-facing doc change yet; Phase 5 documents SIGTERM = level 3.

## Open questions

### OQ-01: If no further event arrives after a level-3 request, does level 3 hang?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: no. The wind-down budget recorded in Phase 1 (spec R11) bounds the wait; on breach the driver must escalate to level 4 with the escalation RECORDED rather than waiting indefinitely. This child DETECTS and records the breach; Phase 5 (`71vjbn`) enforces the escalation action, because escalation spans levels and spec A7 validates it there. A V-item here pins the detection so the two phases cannot disagree.

## Execution notes (2026-08-30)

WHAT WAS BUILT. The level-3 machinery lives in `agent_workflows/runner_stop.py` (the shared module both drivers already consult, so nothing is duplicated per driver): `is_oc_safe_checkpoint` / `is_agy_safe_checkpoint` (per-driver completion predicates over each driver's OWN schema), `CheckpointObserver` (the shared control flow, taking the detector as a parameter), `StopAtCheckpoint`, `stopped_disposition` / `stopped_stop_event` (the KNOWN-certainty record, spec R18/R21), and `deadline_seconds_remaining` / `budget_breach_event` / `BudgetBreachWatch` (the bounded-wait DETECTOR, spec R11). Each driver wires those at its existing per-line loop and adds a deliberate-stop branch to `reconcile_disposition`.

FOUR DECISIONS TAKEN AUTONOMOUSLY, all recorded in the run's decisions register (D1-D4) and all reversible:

1. `interrupted` is the stopped status, rather than a new one. It is ALREADY in both drivers' vocabulary and in `runner_shutdown.KNOWN_ITEM_STATUSES`, so the ledger stays coherent (spec R3) and the existing `requeue_interrupted` already retries it in recovery mode. A new status would have broken Phase 0's coherence check and the resume path simultaneously. The level/certainty detail rides a separate `stopped` record, so nothing is lost by reusing the status.
2. The stop is raised as an exception (`StopAtCheckpoint`) rather than flagged and polled. It unwinds into each driver's EXISTING `except BaseException` handler, which already routes to the shared reaper, so no second teardown path is created (spec R5).
3. A level-3 run exits NONZERO, unlike levels 1-2's 0. Its own item is `interrupted`, which is not a success state; only items the stop never STARTED are excused. Spec A1/A4 mandate 0 for the between-turn levels; no acceptance criterion requires 0 for level 3, and claiming success for a turn that did not finish would be the fabrication R22 forbids.
4. `BudgetBreachWatch` shortens its poll interval to the remaining budget. With a sub-second injected deadline a fixed 1s interval would report the breach a second late, which would make a bounded-time assertion fail for a purely cosmetic reason.

HONESTY BOUNDARY, recorded in the code comments so a later reader cannot overstate it. The child is a one-shot `opencode run` / `agy` subprocess with NO cooperative stop channel, so "stopping the turn at a checkpoint" IS TERMINATION, at an instant chosen by observation. Levels 3 and 4 SHARE that mechanism and differ only in WHEN it is issued. "KNOWN" therefore means no PREVIOUSLY OBSERVED operation was cut mid-flight, NOT that the agent finished tidily: anything begun after its last emitted event is unobserved, and uncommitted work is not covered.

EVENT VOCABULARY RE-VERIFIED, not inherited on trust. Parsing the session file cited by the spec's OQ-01 resolution gave exactly the counts the plan claimed: 122 `step_start`, 122 `step_finish`, 135 `tool_use` (every one `part.state.status == "completed"`), 85 `text`.

DEPENDENCY NOTE. `1qxuke` (Phase 2) is `executed` but its code sits on `aw/lane/1qxuke`, not on `main`. Following the pattern the earlier phases of this Set used, its feature commit `dc6b0a8` was merged into this lane (`113bdf9b`) so this phase builds on the real Phase 0-2 code rather than reimplementing it.

FULL-SUITE EVIDENCE (`make test-all`, i.e. `python3 -m pytest tests/ -m ''`):

```text
19 failed, 3386 passed, 3 skipped, 4 xfailed in 113.84s (0:01:53)
```

The 19 failures are PRE-EXISTING and unrelated (CLI subparser descriptions, command-surface declarations, `run_viewer`). Measured rather than asserted: the same suite was run in a clean detached worktree at this lane's pre-change base `113bdf9b`, giving

```text
19 failed, 3340 passed, 3 skipped, 4 xfailed in 174.94s (0:02:54)
```

and a set comparison of the two failure lists reports `NET-NEW failures (after - base): NONE`, `FIXED (base - after): NONE`, `identical sets: True`. So this change adds 46 passing tests (3340 -> 3386) and zero net-new failures. The baseline worktree was removed afterwards.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted pytest output showing the checkpoint helper reports a checkpoint ONLY after a COMPLETED event line, and does NOT report one for (a) a partial/interleaved line and (b) an event whose status is not completed. Must be shown for ALL THREE output modes (`clean`, `raw`, `quiet`), since `render_event` runs only in `clean` and a `render_event`-based implementation would silently never fire in the other two. Must also show the agy path driven by `step_update`/`state == "DONE"` rather than the oc field names. Plus an assertion that no `time.sleep`/deadline defines the condition (spec R10).
  - Observed evidence: all 19 predicate/observer/fence tests pass, ALL THREE output modes fire end-to-end, both driver schemas are proven non-interchangeable, R10 is asserted on the source, and the `clean`-only mutation was injected and CAUGHT. Detail below.

    The predicate, the observer, and the structural fences (`python3 -m pytest tests/test_runner_stop_level3.py -m '' -p no:randomly -o addopts="" -v -k "SafeCheckpointDefinition or CheckpointObserver or BothDriversWire"`):

    ```text
    collected 46 items / 27 deselected / 19 selected

    tests/test_runner_stop_level3.py::SafeCheckpointDefinitionTests::test_a_malformed_or_missing_state_is_not_a_checkpoint PASSED [  5%]
    tests/test_runner_stop_level3.py::SafeCheckpointDefinitionTests::test_a_non_completed_status_is_not_a_checkpoint PASSED [ 10%]
    tests/test_runner_stop_level3.py::SafeCheckpointDefinitionTests::test_a_partial_or_interleaved_line_is_not_a_checkpoint PASSED [ 15%]
    tests/test_runner_stop_level3.py::SafeCheckpointDefinitionTests::test_agy_uses_its_own_schema_step_update_done PASSED [ 21%]
    tests/test_runner_stop_level3.py::SafeCheckpointDefinitionTests::test_non_object_json_is_not_a_checkpoint PASSED [ 26%]
    tests/test_runner_stop_level3.py::SafeCheckpointDefinitionTests::test_oc_completed_tool_event_is_a_checkpoint PASSED [ 31%]
    tests/test_runner_stop_level3.py::SafeCheckpointDefinitionTests::test_oc_step_finish_is_a_checkpoint PASSED [ 36%]
    tests/test_runner_stop_level3.py::SafeCheckpointDefinitionTests::test_the_checkpoint_condition_is_not_defined_by_elapsed_time PASSED [ 42%]
    tests/test_runner_stop_level3.py::SafeCheckpointDefinitionTests::test_the_detector_matches_the_real_session_vocabulary PASSED [ 47%]
    tests/test_runner_stop_level3.py::SafeCheckpointDefinitionTests::test_the_two_schemas_do_not_cross_contaminate PASSED [ 52%]
    tests/test_runner_stop_level3.py::CheckpointObserverTests::test_agy_observer_is_driven_by_step_update_done PASSED [ 57%]
    tests/test_runner_stop_level3.py::CheckpointObserverTests::test_no_stop_without_a_request_however_many_checkpoints_pass PASSED [ 63%]
    tests/test_runner_stop_level3.py::CheckpointObserverTests::test_stops_at_the_first_completed_event_after_the_request PASSED [ 68%]
    tests/test_runner_stop_level3.py::CheckpointObserverTests::test_the_recorded_position_is_the_completed_events_own PASSED [ 73%]
    tests/test_runner_stop_level3.py::CheckpointObserverTests::test_the_request_is_monotonic PASSED [ 78%]
    tests/test_runner_stop_level3.py::BothDriversWireLevel3Tests::test_both_drivers_use_the_shared_observer_and_their_own_detector PASSED [ 84%]
    tests/test_runner_stop_level3.py::BothDriversWireLevel3Tests::test_checkpoint_detection_is_not_routed_through_the_clean_only_renderer PASSED [ 89%]
    tests/test_runner_stop_level3.py::BothDriversWireLevel3Tests::test_no_new_ledger_substrate_was_introduced PASSED [ 94%]
    tests/test_runner_stop_level3.py::BothDriversWireLevel3Tests::test_no_signal_handler_is_registered_yet PASSED [100%]

    ====================== 19 passed, 27 deselected in 0.20s =======================
    ```

    Non-checkpoints are covered by name above: `test_a_non_completed_status_is_not_a_checkpoint` (statuses `running`/`pending`/`error`/`""`/`None`), `test_a_partial_or_interleaved_line_is_not_a_checkpoint` (truncated line, bare `{"type": "tool_use"`, blank, non-JSON, and a glued interleave), `test_non_object_json_is_not_a_checkpoint`, and `test_a_malformed_or_missing_state_is_not_a_checkpoint`. `test_oc_step_finish_is_a_checkpoint` also asserts `step_start` is NOT one.

    AGY PATH ON ITS OWN SCHEMA, and the anti-cross-contamination proof (`test_the_two_schemas_do_not_cross_contaminate`): `is_agy_safe_checkpoint` accepts `step_update`+`DONE` and REJECTS oc's `tool_use`+`state.status == "completed"`, while `is_oc_safe_checkpoint` does the converse. A single-schema implementation therefore fails here rather than silently never firing on one driver.

    ALL THREE OUTPUT MODES, driven end-to-end through the real driver (`-k "AllOutputModes"`; full block pasted under V-02):

    ```text
    tests/test_runner_stop_level3.py::AllOutputModesTests::test_checkpoint_fires_in_clean_mode PASSED [ 62%]
    tests/test_runner_stop_level3.py::AllOutputModesTests::test_checkpoint_fires_in_quiet_mode PASSED [ 75%]
    tests/test_runner_stop_level3.py::AllOutputModesTests::test_checkpoint_fires_in_raw_mode PASSED [ 87%]
    ```

    R10 (no time-based checkpoint) is asserted on the SOURCE of the two predicates and of `CheckpointObserver.observe`, which must contain none of `time.`/`sleep`/`monotonic`/`deadline`/`budget` (`test_the_checkpoint_condition_is_not_defined_by_elapsed_time`).

    MUTATION-VERIFIED, so this item is not self-certifying. Injecting the exact defect the plan warned about - gating the observe call on `clean` mode, i.e. `if output_mode == "clean" and observer.observe(line):` - produced the mode-dependent failure and NOTHING else:

    ```text
    FAILED tests/test_runner_stop_level3.py::AllOutputModesTests::test_checkpoint_fires_in_quiet_mode
    FAILED tests/test_runner_stop_level3.py::AllOutputModesTests::test_checkpoint_fires_in_raw_mode
    2 failed, 1 passed in 2.24s
    E   AssertionError: None is not an instance of <class 'dict'> : output_mode=raw: no stop was
    E   recorded, so the checkpoint never fired in this mode
    ```

    That is the proof the three-mode requirement has teeth: `clean` still passed while `raw`/`quiet` failed. The mutation was reverted and the suite re-run green (46 passed) before finalizing.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted pytest output for spec A3 showing the event index at which the turn stopped (proving it stopped after a completed event, not mid-event), the process-table observation that the child AND its process group were reaped via `clean_shutdown`, and the remaining three Phase-0 invariants (lock re-acquirable, ledger parses, and `git status --porcelain` UNCHANGED by cleanup per `2ouj70`'s observe-and-report R4 semantics - not "clean"). Plus evidence the stop went through `clean_shutdown` rather than a local `terminate_process` call (spec R5).
  - Observed evidence: the turn stopped at scripted event 5 (the first COMPLETED event; events 1-4 are non-checkpoints), the child was reaped through `clean_shutdown` (`reaped [1324908]`), and all four Phase-0 invariants were OBSERVED with R4 as unchanged-by-cleanup. Detail below.

    Spec A3, driving the REAL drivers over a fake child (`python3 -m pytest tests/test_runner_stop_level3.py -m '' -p no:randomly -o addopts="" -v -k "AllOutputModes or StopAtCheckpoint or AgyDriverParity"`):

    ```text
    collected 46 items / 38 deselected / 8 selected

    tests/test_runner_stop_level3.py::StopAtCheckpointTests::test_the_run_stops_and_leaves_later_items_queued PASSED [ 12%]
    tests/test_runner_stop_level3.py::StopAtCheckpointTests::test_the_stop_is_recorded_as_a_deliberate_non_failure_event PASSED [ 25%]
    tests/test_runner_stop_level3.py::StopAtCheckpointTests::test_the_stop_routes_through_the_shared_clean_shutdown PASSED [ 37%]
    tests/test_runner_stop_level3.py::StopAtCheckpointTests::test_the_turn_stops_after_the_completed_event_never_mid_event PASSED [ 50%]
    tests/test_runner_stop_level3.py::AllOutputModesTests::test_checkpoint_fires_in_clean_mode PASSED [ 62%]
    tests/test_runner_stop_level3.py::AllOutputModesTests::test_checkpoint_fires_in_quiet_mode PASSED [ 75%]
    tests/test_runner_stop_level3.py::AllOutputModesTests::test_checkpoint_fires_in_raw_mode PASSED [ 87%]
    tests/test_runner_stop_level3.py::AgyDriverParityTests::test_agy_stops_at_its_own_step_update_done_checkpoint PASSED [100%]

    ======================= 8 passed, 38 deselected in 5.03s =======================
    ```

    THE EVENT INDEX, observed from a real run's own ledger (probe script over the same fixtures). The fake child emits four NON-checkpoints (`step_start`, two `text`, and a `tool_use` with `status: running`), writes the stop request before event 3, and makes event 5 the first COMPLETED event. The driver stopped at exactly 5, so it stopped after a completed event and not on the merely-next line (which would have been 3) nor on the live tool (4):

    ```json
    {
      "at": "2026-08-30T08:14:04+00:00",
      "certainty": "known",
      "events_observed": 5,
      "failure": false,
      "git_state": "?? .aw/records/runs/",
      "last_completed_event": "tool_use:read",
      "last_completed_event_index": 5,
      "level": 3,
      "level_name": "now",
      "requester": "test-operator",
      "stopped_deliberately": true
    }
    ```

    NEVER MID-EVENT, proven by a defect witness rather than only by the index: the child writes `CHILD_RAN_PAST_CHECKPOINT` if it survives past event 5. Observed `=== child ran past checkpoint witness file present: False`.

    THE STOP WENT THROUGH `clean_shutdown`, NOT A LOCAL `terminate_process` (spec R5). The per-turn call has no lock and no repo, so it reports SKIPPED for those and prints its per-invariant report (spec R23) - text that can only exist if the shared routine actually ran. Note the REAPED PID, which is the child being killed at the observed boundary:

    ```text
    clean shutdown: lock_released, tree_observed NOT satisfied
      children_reaped (R1): ok - reaped [1324908]
      lock_released (R2): SKIPPED - no run lock held by this caller
      ledger_coherent (R3): ok - 2 item(s), all in a defined state
      tree_observed (R4): SKIPPED - no repository supplied
    clean shutdown: all invariants satisfied
      children_reaped (R1): ok - no live child agent process among 0 tracked
      lock_released (R2): ok - lock file removed; lock free=True
      ledger_coherent (R3): ok - 2 item(s), all in a defined state
      tree_observed (R4): ok - 1 dirty path(s) left exactly as found (nothing stashed, reset, or moved)
    ```

    THE FOUR PHASE-0 INVARIANTS, observed rather than asserted from code:

    ```text
    === ps for surviving descendants of /tmp/probe-abeshftj/repo
    NONE (no survivor)                      <- R1 (process GROUP: no descendant left)
    === driver.lock re-acquirable:
    lock file exists: False                 <- R2 (released AND removed, so trivially free)
    === observe_ledger: (True, '2 item(s), all in a defined state')   <- R3
    === git status UNCHANGED-by-cleanup check: before-set subset of after-set: True   <- R4
    === git stash list: ''                  <- nothing hidden behind the operator's back
    ```

    R4 is asserted as UNCHANGED-by-cleanup, NOT clean, matching `2ouj70`'s reviewed observe-and-report semantics: the dirty set may only have GROWN (by the turn's own work), never shrunk, which is the direction a stash/reset/checkout would move it.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted ledger contents after a level-3 stop showing the interrupted item with KNOWN certainty and its last completed operation, zero `unknown_outcome` entries, and no executed/complete/success marking (spec R22). CRITICALLY, the pasted disposition must NOT be `failed-safely` or `partial`: that is what the un-intercepted `reconcile_disposition` fallback (`oc_runipd.py:1848`) produces, so evidence showing either value means E-03's interception is missing and this item FAILS. Must also paste a CONTROL case: a genuine failure with no stop requested still reconciles to `failed-safely`, proving the new branch did not swallow real failures. A prose claim of "recorded correctly" fails this item.
  - Observed evidence: the interrupted item is `interrupted` with `certainty: known` and `last_completed_event: tool_use:read`, explicitly NOT `failed-safely`/`partial`, with ZERO `unknown_outcome` in the run dir; the genuine-failure control still yields `failed-safely`; and removing the interception reproduced `failed-safely` exactly as predicted. Detail below.

    `python3 -m pytest tests/test_runner_stop_level3.py -m '' -p no:randomly -o addopts="" -v -k "StoppedDisposition or KnownDisposition"`:

    ```text
    collected 46 items / 38 deselected / 8 selected

    tests/test_runner_stop_level3.py::StoppedDispositionRecordTests::test_a_genuine_failure_still_reconciles_to_failed_safely PASSED [ 12%]
    tests/test_runner_stop_level3.py::StoppedDispositionRecordTests::test_an_empty_or_falsy_stopped_record_does_not_trigger_the_branch PASSED [ 25%]
    tests/test_runner_stop_level3.py::StoppedDispositionRecordTests::test_it_is_never_unknown_outcome_and_never_a_success PASSED [ 37%]
    tests/test_runner_stop_level3.py::StoppedDispositionRecordTests::test_it_records_level_certainty_position_git_state_and_resume_action PASSED [ 50%]
    tests/test_runner_stop_level3.py::StoppedDispositionRecordTests::test_reconcile_disposition_intercepts_the_deliberate_stop_in_both_drivers PASSED [ 62%]
    tests/test_runner_stop_level3.py::StoppedDispositionRecordTests::test_the_stopped_status_is_an_already_known_coherent_status PASSED [ 75%]
    tests/test_runner_stop_level3.py::KnownDispositionInTheLedgerTests::test_a_genuinely_failed_turn_with_no_stop_still_reports_failed_safely PASSED [ 87%]
    tests/test_runner_stop_level3.py::KnownDispositionInTheLedgerTests::test_the_interrupted_item_is_known_and_not_failed_safely PASSED [100%]

    ======================= 8 passed, 38 deselected in 2.17s =======================
    ```

    THE ACTUAL LEDGER after a real level-3 stop. The disposition is `interrupted`, and CRITICALLY it is NOT `failed-safely` and NOT `partial`, which is what the un-intercepted fallback produces:

    ```text
    === driver exit code: 1
    === item statuses: {
      "pa0001": "interrupted",
      "pa0002": "queued"
    }
    ```

    The `stopped` record carried on that item, with KNOWN certainty and the last completed operation NAMED (not just indexed):

    ```json
    {
      "certainty": "known",
      "events_observed": 5,
      "failure": false,
      "git_state": "?? .aw/records/runs/",
      "last_completed_event": "tool_use:read",
      "last_completed_event_index": 5,
      "level": 3,
      "level_name": "now",
      "requester": "test-operator",
      "resume_action": "re-run this item in recovery mode; it was interrupted at an observed safe checkpoint after the operation named above, so re-read the plan and the repository state before continuing (no previously observed operation was cut mid-flight, but work the agent began after its last emitted event is unobserved and may be uncommitted)",
      "stopped_deliberately": true
    }
    ```

    The `events.jsonl` record, on the ESTABLISHED channel, as a NON-failure (spec R21):

    ```text
    {"at": "...", "event": "run-created", "queue": ["pa0001", "pa0002"], "run_id": "run-level3-oc-0"}
    {"action": "execute", "at": "...", "attempt": 1, "event": "ipd-started", "id6": "pa0001"}
    {"at": "...", "certainty": "known", "deliberate": true, "event": "deliberate-stop-at-checkpoint",
     "failure": false, "id6": "pa0001", "last_completed_event": "tool_use:read",
     "last_completed_event_index": 5, "level": 3, "level_name": "now", "requester": "test-operator"}
    ```

    ZERO `unknown_outcome` anywhere in the run directory (that certainty is level 4's, owned by Phase 4):

    ```text
    === grep unknown_outcome in the whole run dir:
    matches: NONE
    ```

    NO success marking (spec R22): the status is `interrupted`, which `test_the_stopped_status_is_an_already_known_coherent_status` asserts is in `runner_shutdown.KNOWN_ITEM_STATUSES` (so the ledger stays coherent per R3, and `requeue_interrupted` already retries it) and NOT in either driver's `SUCCESS_STATES`. Correspondingly the run exits 1, not 0: level 3 admits its turn did not finish and only excuses items it never STARTED.

    THE CONTROL, end to end - a genuine failure with NO stop requested still reconciles to `failed-safely`:

    ```text
    tests/test_runner_stop_level3.py::KnownDispositionInTheLedgerTests::test_a_genuinely_failed_turn_with_no_stop_still_reports_failed_safely PASSED
    ```

    which asserts `statuses["kb0001"] == "failed-safely"`, that the item carries no `stopped` key, that no `deliberate-stop-at-checkpoint` event exists, and that the run exits nonzero. A unit-level control covers both drivers (`test_a_genuine_failure_still_reconciles_to_failed_safely`), and `test_an_empty_or_falsy_stopped_record_does_not_trigger_the_branch` proves the branch cannot be tripped by a falsy/garbage `stopped` value (`None`, `{}`, `{"stopped_deliberately": False}`, `"yes"`, `1` all still yield `failed-safely`).

    MUTATION-VERIFIED. Replacing the interception guard with `if False:` reproduced EXACTLY the misreporting the plan predicted, at both the unit and the ledger level:

    ```text
    E  AssertionError: 'failed-safely' != 'interrupted'
    E   : agent_workflows.oc_runipd: a deliberate stop must not reconcile to 'failed-safely'

    E  AssertionError: 'failed-safely' unexpectedly found in ('failed-safely', 'partial') :
    E  a DELIBERATE stop was recorded as a failure/partial:
    E  {'ka0001': 'failed-safely', 'ka0002': 'queued'}
    ```

    So the `failed-safely` conflation is real, is what would have happened without E-03, and is genuinely caught here. The mutation was reverted and the suite re-run green before finalizing.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted pytest output with a deliberately silent fake child showing the driver recorded the budget-breach/escalation-required marker and RETURNED (bounded), using a SHORT INJECTED deadline (sub-second) so the test proves bounded behavior rather than passing by waiting out a real budget; the pasted elapsed time must be shown against that injected deadline. Plus confirmation that no escalation ACTION was taken here (Phase 5's job), and that detection works with the child SILENT (i.e. not implemented as a check that only runs when the next line arrives, which a blocking `for line in process.stdout` would never reach).
  - Observed evidence: with a SUB-SECOND injected deadline (0.25s vs the real 600s budget) and a fully SILENT child, the breach was recorded out-of-band and the run finished in 4.69s; `escalation_required: true` with `escalation_performed: false` and the durable level still 3, so no escalation action was taken. Detail below.

    `python3 -m pytest tests/test_runner_stop_level3.py -m '' -p no:randomly -o addopts="" -v -k "Deadline or BudgetBreach"`:

    ```text
    collected 46 items / 39 deselected / 7 selected

    tests/test_runner_stop_level3.py::DeadlineArithmeticTests::test_an_unparseable_deadline_reads_as_already_breached PASSED [ 14%]
    tests/test_runner_stop_level3.py::DeadlineArithmeticTests::test_remaining_time_tracks_the_records_own_deadline PASSED [ 28%]
    tests/test_runner_stop_level3.py::DeadlineArithmeticTests::test_the_breach_event_requires_escalation_but_records_none_performed PASSED [ 42%]
    tests/test_runner_stop_level3.py::DeadlineArithmeticTests::test_the_breach_watch_is_bounded_and_fires_without_any_further_input PASSED [ 57%]
    tests/test_runner_stop_level3.py::DeadlineArithmeticTests::test_the_breach_watch_stops_quietly_when_the_child_exits_first PASSED [ 71%]
    tests/test_runner_stop_level3.py::BudgetBreachDetectionTests::test_a_silent_child_yields_a_recorded_breach_within_a_bounded_time PASSED [ 85%]
    tests/test_runner_stop_level3.py::BudgetBreachDetectionTests::test_no_breach_is_recorded_when_a_checkpoint_is_reached_in_time PASSED [100%]

    ======================= 7 passed, 39 deselected in 7.42s =======================
    ```

    THE SHORT INJECTED DEADLINE AND THE MEASURED ELAPSED TIME, from a real driver run over a child that goes silent (probe over the same fixtures). The budget is SUB-SECOND and written into the durable record by the child, so the test cannot pass by waiting out the real level-3 budget:

    ```text
    INJECTED deadline budget: 0.25s (sub-second, so waiting out the real 600s level-3 budget is impossible)
    real level-3 budget would be: 600.0 s
    TOTAL driver elapsed: 4.69s
    ```

    4.69s against a 600s real budget, and the 4.69s is dominated by the child's own scripted 4s of silence, not by the driver waiting. So the wait is bounded by the injected deadline, not by the level's real budget.

    DETECTION WITH THE CHILD FULLY SILENT. The child emits two non-checkpoint lines and then NOTHING for 4s. A detector implemented as "check after the next line arrives" could never fire, because the blocking `for line in process.stdout` would still be waiting. The breach was recorded anyway, from the out-of-band watch thread:

    ```json
    {
      "at": "2026-08-30T08:14:16+00:00",
      "budget_seconds": 0.25,
      "deadline": "2026-08-30T08:14:16.455856+00:00",
      "deliberate": true,
      "escalation_performed": false,
      "escalation_required": true,
      "escalation_to_level": 4,
      "event": "stop-budget-breached",
      "failure": false,
      "id6": "qa0001",
      "last_completed_event_index": null,
      "level": 3,
      "level_name": "now",
      "observed_events": 2,
      "reason": "no safe checkpoint observed before the wind-down deadline",
      "requester": "test-operator"
    }
    ```

    `last_completed_event_index: null` is the honest record that NO checkpoint was ever reached, and `observed_events: 2` matches the two non-checkpoint lines.

    NO ESCALATION ACTION WAS TAKEN HERE (spec A7 puts enforcement in Phase 5). Three independent observations:

    ```text
    durable request level after the breach: 3 (must still be 3: Phase 5 owns escalation)
    === checkpoint-stop events (must be none: no checkpoint was reachable): NONE
    ```

    plus the event's own `"escalation_required": true` with `"escalation_performed": false`, so the history cannot be misread as claiming this phase escalated. The unit test `test_the_breach_event_requires_escalation_but_records_none_performed` pins that pair.

    The operator-facing line, which likewise says recorded-not-performed:

    ```text
    stop wind-down budget breached (level 3, 0.25s, deadline 2026-08-30T08:14:16.455856+00:00):
    no safe checkpoint observed; escalation REQUIRED (recorded, not performed here)
    ```

    The NEGATIVE control (`test_no_breach_is_recorded_when_a_checkpoint_is_reached_in_time`) proves the breach path does not fire on the ordinary level-3 stop, so a breach marker means a real breach.

    MUTATION-VERIFIED. Disabling the deadline comparison in the watch thread (`if False:`) failed both the unit and the end-to-end breach tests, the latter with `0 != 1 : no bounded-wait breach was recorded (elapsed 4.43s)`, confirming the assertion is not vacuous. Reverted and re-run green (46 passed) before finalizing.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract (inherited from orchestrator `zpbx7o`):

- Open questions: none blocking FOR THIS CHILD (spec OQ-01/OQ-03 are RESOLVED in c4gd2h; OQ-01 here is resolved). The orchestrator's OQ-02 (spec A10 / Windows) gates `71vjbn` only.
- Scope fence: touch ONLY this plan's declared `Scope-Paths`. Widening requires a new plan. Specifically: the `reconcile_disposition` change is limited to ADDING a deliberate-stop branch ahead of the existing fallback - do NOT alter the existing outcome/`executed`/`failed-safely` semantics for non-stop runs (a control test pins this), do NOT add a second reaper or bypass `clean_shutdown` (spec R5), and do NOT introduce an agent prompt or handshake change (spec OQ-01 rejected it).
- Honesty rule (hard MUST): paste the ACTUAL runner output into each `V-*` Observed evidence. Never claim a test passed that was not run.
- Commits: path-scoped only; never `git add -A`/`-a`; never push; never tag or release.
- Lifecycle: `aw ipd begin <this> --actor <agent/model>` BEFORE executing (fail-closed), then `aw ipd finalize` after validation passes. Never hand-move to `executed/`.
- If any validation fails, STOP and report rather than marking the plan executed.
