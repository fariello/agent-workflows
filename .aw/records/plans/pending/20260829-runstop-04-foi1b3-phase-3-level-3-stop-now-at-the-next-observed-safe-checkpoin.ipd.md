# IPD: Phase 3: level 3 stop-now at the next observed safe checkpoint with KNOWN disposition

- Date: 2026-08-29
- Kind: child
- Blocks-Release: next
- From-Backlog: kjzlgw
- Concern: Spec c4gd2h level 3 (STOP-NOW) stops the CURRENT agent turn at its next SAFE checkpoint rather than letting it finish, and because it stopped at a DEFINED point the interrupted item's disposition is KNOWN (recorded stopped/incomplete, never `unknown_outcome`). This is the level that makes SIGTERM meaningful instead of fatal. Spec OQ-01 is RESOLVED: no agent cooperation is needed, because the driver already consumes the child's structured event stream line-by-line (`oc_runipd.py:1765-1786`, `--format json`) and the session JSONL carries discrete `step_start`/`tool_use` records, so the driver can define a safe checkpoint unilaterally.
- Scope: Implement level 3 in BOTH drivers: define a SAFE CHECKPOINT as the instant after a completed tool/step event and before the next is dispatched (observable from the existing stream loop, spec R10), stop the turn there, record the interrupted item with KNOWN certainty, and end in the Phase-0 `clean_shutdown`. Does NOT implement the immediate interrupt or `unknown_outcome` (Phase 4), signal handlers, or the CLI verb (Phase 5).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_stop.py, tests/test_runner_stop_level3.py
- Item-Dependencies: executed:1qxuke
- Status: reviewed
- Set: runstop
- Order: 4
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: foi1b3

## Workflow history
- 2026-08-29 /plan-review (OpenCode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-401..PR-407. Confirmed the spec OQ-01 evidence is REAL by parsing the cited session file (135 `tool_use`, every one carrying `part.state.status == "completed"`, plus 122 `step_start`, 122 `step_finish`, 85 `text`), so completion is an observed field and `step_finish` is the cleaner boundary. Then found two BLOCKERs. (1) Nothing owned the disposition path: a level-3 stop leaves NO outcome JSON (the runbook has the agent write it at turn end), the plan is not in `executed/`, and the terminated child exits nonzero, so `reconcile_disposition` falls through to `return ("partial" if exit_code == 0 else "failed-safely")` (`oc_runipd.py:1848`) and records a DELIBERATE operator stop as `failed-safely` - the exact crash-versus-intent conflation spec R21 forbids and a verdict R22 forbids. E-03 now owns intercepting it, and V-03 FAILS on a pasted `failed-safely`/`partial` and additionally requires a control case proving genuine failures still reconcile normally. (2) E-01 pinned checkpoint detection to `render_event`, which is invoked ONLY under `output_mode == "clean"` (:1780-1781), so the whole feature would silently never fire under `raw`/`quiet`; E-01 now requires mode-independent parsing and V-01 requires all three modes. Also corrected the honesty of the mechanism: the child is a one-shot `opencode run` with no stop channel and the cited `StallWatchdog` precedent calls `terminate_process` (:159-169), so level 3 is termination at an observed boundary and shares its mechanism with level 4, differing only in timing - "KNOWN" means no previously observed operation was cut mid-flight, not that the agent finished tidily. Recorded the oc-vs-agy event-schema asymmetry (`tool_use`/`state.status` vs `step_update`/`DONE`) for CID-3, noted that a blocking `for line in process.stdout` cannot notice a deadline so E-04 needs the out-of-band watchdog shape, required a short injected deadline so V-04 cannot pass by waiting out a real budget, fixed the off-by-one poll citation (:1774-1775 -> :1775-1776), aligned the R4 assertion with `2ouj70`'s observe-and-report semantics, and switched full-suite evidence to `make test-all`.
- 2026-08-29 reviewed (aw set): status set to reviewed
- 2026-08-29 to-review (aw set): Authored review-ready from spec c4gd2h (graduation of backlog kjzlgw).

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.

## Goal

Implement level 3 (STOP-NOW): interrupt the current agent turn at the next OBSERVED safe checkpoint derived from the child's own event stream, so the interrupted item's disposition is KNOWN rather than indeterminate (spec R10, R18, A3), with no agent cooperation and no prompt/protocol change.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the observable safe checkpoint

- [ ] E-01 In BOTH drivers, define and implement the SAFE CHECKPOINT as the instant AFTER a COMPLETED tool/step event and BEFORE the next is dispatched, derived from the existing per-line event loop (`oc_runipd.py:1772-1783`). Verified against the cited real session JSONL: a `tool_use` event carries `part.state.status`, and all 135 `tool_use` records in that file have `status == "completed"`, so "completed" is an OBSERVED field, not an inference; the file also holds 122 `step_start` and 122 `step_finish` records, so `step_finish` is the cleaner completion signal than `step_start`. Prefer `step_finish` / `tool_use` with `state.status == "completed"`, and treat any other status as NOT a checkpoint. IMPORTANT correction: the checkpoint detection MUST NOT be built on `render_event`, which is invoked ONLY in `clean` output mode (`oc_runipd.py:1780-1781`); in `raw` and `quiet` modes no event is parsed at all, so a `render_event`-based checkpoint would silently never fire in those modes. Parse the event type in the per-line loop independently of `output_mode` (a minimal `json.loads` + type/status read, reusing `render_stream`'s field names, not its rendering). For `agy_runipd.py` the equivalent completion signal is `step_update` with `state == "DONE"` (`agy_runipd.py:217`, :226), not the oc field names; do not assume one schema across both drivers. No agent cooperation, no time-based condition (spec R10).
  - Depends on: none
  - Expected outcome: a helper reports "at a safe checkpoint" only immediately after a COMPLETED event line is consumed, in ALL THREE output modes (`clean`, `raw`, `quiet`); a test feeding a partial/interleaved line, and one feeding a non-completed status, show it does NOT report a checkpoint; and the agy path is driven by `step_update`/`DONE` rather than the oc field names.
  - Execution state: pending
- [ ] E-02 On a level-3 request observed by the Phase-1 poll at the per-line point (beside `heartbeat.touch()`/`watchdog.touch()`, `oc_runipd.py:1775-1776`; `agy_runipd.py:1844-1845`), stop the current turn at the next safe checkpoint, then route to `runner_shutdown.clean_shutdown(...)` rather than performing local teardown (spec R5). BE HONEST ABOUT THE MECHANISM: the child is a ONE-SHOT `opencode run ...` subprocess (`oc_runipd.py:1694`, argv built :1694-1740) with NO cooperative stop channel - there is no "please wind down" input the driver can send it. So "stopping the turn at a checkpoint" is implemented as TERMINATING the child (via Phase 0's `clean_shutdown`, which owns the reaper) at a moment chosen by observation. The cited precedent does exactly this: `StallWatchdog._run` calls `terminate_process(self.process)` when it fires (`oc_runipd.py:159-169`). Therefore level 3 and level 4 use the SAME kill mechanism and differ ONLY in WHEN it is issued (level 3 waits for an observed completed-event boundary; level 4 does not wait). Record that plainly in the code comment so no reader believes the child is being asked to cooperate. Any interruption of a tool the driver cannot see inside remains impossible; the checkpoint guarantees only that no PREVIOUSLY OBSERVED operation was cut mid-flight.
  - Depends on: E-01
  - Expected outcome: with a fake child emitting 5 scripted events and a level-3 request after event 2, the turn stops after the next COMPLETED event (never mid-event), the child and its group are reaped through `clean_shutdown`, and the four Phase-0 invariants hold; the code comment states that the mechanism is termination-at-an-observed-boundary, not agent cooperation.
  - Execution state: pending

### Task group 2: KNOWN disposition

- [ ] E-03 Record the interrupted item per spec R18 with KNOWN certainty: the level that interrupted it, the last completed operation observed, the observed git state, and what a resume must do first. It MUST NOT be recorded `unknown_outcome` (that is level 4 only) and MUST NOT be recorded executed/complete/successful (spec R22). This REQUIRES intercepting the existing disposition path, which today would MISREPORT the stop: a level-3 stop leaves no outcome JSON (the runbook has the agent write `outcomes/<NN>-<id6>.json` at turn END, so a mid-turn stop never produces it), the plan is not in `executed/`, and the terminated child exits nonzero - so `reconcile_disposition` (`oc_runipd.py:1813-1848`) falls through to its final `return ("partial" if exit_code == 0 else "failed-safely")` at :1848 and labels a DELIBERATE operator stop as `failed-safely`. That is precisely the crash-versus-intent conflation spec R21 forbids and the fabricated verdict R22 forbids. So this E-item must add a deliberate-stop branch to `reconcile_disposition` (both drivers) that runs BEFORE the outcome/exit-code fallback and yields a stopped/incomplete disposition carrying level + KNOWN certainty, rather than letting the existing fallback assign a failure.
  - Depends on: E-02
  - Expected outcome: the ledger shows the interrupted item as stopped/incomplete with KNOWN certainty and the last completed event index/name; it is NOT `failed-safely` and NOT `partial`; zero `unknown_outcome` entries exist after a level-3 stop; and a genuine failure (no stop requested) still reconciles to `failed-safely` as before.
  - Execution state: pending

### Task group 3: bounded wait

- [ ] E-04 Detect and RECORD a wind-down budget breach (spec R11, OQ-01) when no further event arrives after a level-3 request so no checkpoint is reachable, using the deadline recorded by Phase 1. Record the breach as an escalation-required signal; do NOT perform the escalation here (Phase 5 owns it, spec A7). Note the deliberate R10 boundary, so no reader thinks this contradicts it: R10 forbids defining the SAFE CHECKPOINT by elapsed time, and this deadline does not do that - it defines only the GIVE-UP point after which no checkpoint will be awaited. Both facts must be stated in the code comment, since a later reader could otherwise "simplify" the checkpoint into a timeout. Blocking-read caveat: the per-line loop `for line in process.stdout` BLOCKS when a child goes silent, so a deadline cannot be noticed from inside that iteration; the breach detector therefore needs the out-of-band supervisor shape `StallWatchdog` already uses (a daemon thread observing the process, `oc_runipd.py:159-169`), not a check placed after the next line arrives.
  - Depends on: E-02
  - Expected outcome: with a fake child that goes silent after a level-3 request, the driver records a budget-breach/escalation-required marker within a bounded time of the Phase-1 deadline and does not wait indefinitely, PROVEN with a short injected deadline (sub-second) so the test cannot pass by waiting out a real multi-minute budget; the marker is the single signal Phase 5 will act on; no escalation action is taken here.
  - Execution state: pending

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

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted pytest output showing the checkpoint helper reports a checkpoint ONLY after a COMPLETED event line, and does NOT report one for (a) a partial/interleaved line and (b) an event whose status is not completed. Must be shown for ALL THREE output modes (`clean`, `raw`, `quiet`), since `render_event` runs only in `clean` and a `render_event`-based implementation would silently never fire in the other two. Must also show the agy path driven by `step_update`/`state == "DONE"` rather than the oc field names. Plus an assertion that no `time.sleep`/deadline defines the condition (spec R10).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output for spec A3 showing the event index at which the turn stopped (proving it stopped after a completed event, not mid-event), the process-table observation that the child AND its process group were reaped via `clean_shutdown`, and the remaining three Phase-0 invariants (lock re-acquirable, ledger parses, and `git status --porcelain` UNCHANGED by cleanup per `2ouj70`'s observe-and-report R4 semantics - not "clean"). Plus evidence the stop went through `clean_shutdown` rather than a local `terminate_process` call (spec R5).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted ledger contents after a level-3 stop showing the interrupted item with KNOWN certainty and its last completed operation, zero `unknown_outcome` entries, and no executed/complete/success marking (spec R22). CRITICALLY, the pasted disposition must NOT be `failed-safely` or `partial`: that is what the un-intercepted `reconcile_disposition` fallback (`oc_runipd.py:1848`) produces, so evidence showing either value means E-03's interception is missing and this item FAILS. Must also paste a CONTROL case: a genuine failure with no stop requested still reconciles to `failed-safely`, proving the new branch did not swallow real failures. A prose claim of "recorded correctly" fails this item.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted pytest output with a deliberately silent fake child showing the driver recorded the budget-breach/escalation-required marker and RETURNED (bounded), using a SHORT INJECTED deadline (sub-second) so the test proves bounded behavior rather than passing by waiting out a real budget; the pasted elapsed time must be shown against that injected deadline. Plus confirmation that no escalation ACTION was taken here (Phase 5's job), and that detection works with the child SILENT (i.e. not implemented as a check that only runs when the next line arrives, which a blocking `for line in process.stdout` would never reach).
  - Observed evidence:
  - Result: pending

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
