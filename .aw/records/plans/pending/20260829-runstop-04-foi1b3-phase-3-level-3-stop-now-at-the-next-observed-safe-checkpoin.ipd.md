# IPD: Phase 3: level 3 stop-now at the next observed safe checkpoint with KNOWN disposition

- Date: 2026-08-29
- Kind: child
- Blocks-Release: next
- From-Backlog: kjzlgw
- Concern: Spec c4gd2h level 3 (STOP-NOW) stops the CURRENT agent turn at its next SAFE checkpoint rather than letting it finish, and because it stopped at a DEFINED point the interrupted item's disposition is KNOWN (recorded stopped/incomplete, never `unknown_outcome`). This is the level that makes SIGTERM meaningful instead of fatal. Spec OQ-01 is RESOLVED: no agent cooperation is needed, because the driver already consumes the child's structured event stream line-by-line (`oc_runipd.py:1765-1786`, `--format json`) and the session JSONL carries discrete `step_start`/`tool_use` records, so the driver can define a safe checkpoint unilaterally.
- Scope: Implement level 3 in BOTH drivers: define a SAFE CHECKPOINT as the instant after a completed tool/step event and before the next is dispatched (observable from the existing stream loop, spec R10), stop the turn there, record the interrupted item with KNOWN certainty, and end in the Phase-0 `clean_shutdown`. Does NOT implement the immediate interrupt or `unknown_outcome` (Phase 4), signal handlers, or the CLI verb (Phase 5).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_stop.py, tests/test_runner_stop_level3.py
- Item-Dependencies: executed:1qxuke
- Status: to-review
- Set: runstop
- Order: 4
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: foi1b3

## Workflow history
- 2026-08-29 to-review (aw set): Authored review-ready from spec c4gd2h (graduation of backlog kjzlgw).

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.

## Goal

Implement level 3 (STOP-NOW): interrupt the current agent turn at the next OBSERVED safe checkpoint derived from the child's own event stream, so the interrupted item's disposition is KNOWN rather than indeterminate (spec R10, R18, A3), with no agent cooperation and no prompt/protocol change.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the observable safe checkpoint

- [ ] E-01 In BOTH drivers, define and implement the SAFE CHECKPOINT as the instant AFTER a completed tool/step event and BEFORE the next is dispatched, derived from the existing per-line event loop (`oc_runipd.py:1770-1786`; event type already available via `render_event`, :1780). No new parser, no agent cooperation, no time-based condition (spec R10).
  - Depends on: none
  - Expected outcome: a helper reports "at a safe checkpoint" only immediately after a complete event line is consumed; a test feeding a partial/interleaved line shows it does NOT report a checkpoint mid-event.
  - Execution state: pending
- [ ] E-02 On a level-3 request observed by the Phase-1 poll at the per-line point (beside `heartbeat.touch()`/`watchdog.touch()`, :1774-1775), stop the current turn AT the next safe checkpoint (do not let it finish), then route to `runner_shutdown.clean_shutdown(...)` rather than performing local teardown (spec R5). Model the supervision shape on the existing `StallWatchdog` (:1769).
  - Depends on: E-01
  - Expected outcome: with a fake child emitting 5 scripted events and a level-3 request after event 2, the turn stops after event 2 or 3 (never mid-event), the child is reaped, and the four Phase-0 invariants hold.
  - Execution state: pending

### Task group 2: KNOWN disposition

- [ ] E-03 Record the interrupted item per spec R18 with KNOWN certainty: the level that interrupted it, the last completed operation observed, the observed git state, and what a resume must do first. It MUST NOT be recorded `unknown_outcome` (that is level 4 only) and MUST NOT be recorded executed/complete/successful (spec R22).
  - Depends on: E-02
  - Expected outcome: the ledger shows the interrupted item as stopped/incomplete with KNOWN certainty and the last completed event index/name; zero `unknown_outcome` entries exist after a level-3 stop.
  - Execution state: pending

### Task group 3: bounded wait

- [ ] E-04 Detect and RECORD a wind-down budget breach (spec R11, OQ-01) when no further event arrives after a level-3 request so no checkpoint is reachable, using the deadline recorded by Phase 1. Record the breach as an escalation-required signal; do NOT perform the escalation here (Phase 5 owns it, spec A7).
  - Depends on: E-02
  - Expected outcome: with a fake child that goes silent after a level-3 request, the driver records a budget-breach/escalation-required marker before the deadline elapses plus a bounded margin, and does not wait indefinitely; the marker is the single signal Phase 5 will act on.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Spec OQ-01 RESOLVED, with the mechanism already present: `oc_runipd.py:1765-1786` spawns the child with `--format json` and iterates `for line in process.stdout`, and the captured session JSONL for a real run contains `{"type":"step_start",...}` and `{"type":"tool_use",...}` records (verified against `.aw/records/runs/run-20260829T053827Z-2084502/sessions/01-jolfpj-attempt-1.jsonl`). A safe checkpoint is therefore observable by the driver alone.
- `StallWatchdog` (`oc_runipd.py:1769`, touched per line at :1775) is the in-repo PRECEDENT for the driver acting on stream observation; model level 3 on that shape rather than inventing a new supervisor.
- Phase 1 (`gq6m2u`) already polls at the per-line point beside `heartbeat.touch()`/`watchdog.touch()` (:1774-1775), which is exactly where a level-3 request must be noticed.
- Phase 0 (`2ouj70`) owns the reaper and the invariants; level 3 must END in `clean_shutdown`, not perform its own teardown (spec R5).
- `render_event(line, pal, tracker=tracker)` (:1780) already parses each event line, so event TYPE is available without adding a second parser.

## Findings

The definition of SAFE must be observable, per spec R10 (no elapsed-time definitions):

| Candidate boundary | Observable? | Verdict |
|---|---|---|
| after a completed `tool_use`/step event, before the next dispatch | yes, from the existing stream loop | CHOSEN |
| mid-tool-call | no (driver cannot see inside the tool) | rejected |
| after N seconds | yes but time-based | rejected by R10 |
| agent-emitted checkpoint marker | requires prompt change + per-agent negotiation | rejected (OQ-01) |

Why KNOWN certainty follows: because the driver stops between discrete events it has already observed, it knows the last completed operation, so the interrupted item's disposition is recorded as stopped/incomplete with that position (spec R18). This is the ONLY difference from Phase 4's level 4 (spec: "the only difference between 3 and 4 is outcome CERTAINTY, not cleanliness").

A bounded-wait obligation exists: if no further event arrives after a level-3 request, the driver cannot reach a checkpoint. The wind-down budget recorded in Phase 1 (spec R11) governs that wait; exceeding it must ESCALATE to level 4 with the escalation recorded, never hang. Escalation ENFORCEMENT is Phase 5 (spec A7), so this child records the deadline breach and defers the escalation action, which a V-item pins.

## Proposed changes (ordered, validatable)

1. Define the safe checkpoint from the existing per-line event stream (no new parser, no agent cooperation).
2. On a level-3 request, stop the turn at that checkpoint in both drivers and route to `clean_shutdown`.
3. Record the interrupted item with KNOWN certainty and its last completed operation (spec R18).
4. Detect and record a budget breach when no checkpoint is reachable, leaving escalation to Phase 5.
5. New `tests/test_runner_stop_level3.py` driving a fake child that emits scripted events.

## Deferred / out of scope (with reason)

- The immediate interrupt, `unknown_outcome`, and resume refusal: Phase 4 (`m0z0ti`).
- Signal handlers and `aw oc/agy run stop`: Phase 5 (`71vjbn`); tests here request level 3 by writing the Phase-1 record.
- ENFORCING escalation on a budget breach: Phase 5 (spec A7). This child records the breach so Phase 5 has one authoritative signal to act on.
- Any change to the agent prompt or a per-agent capability handshake: explicitly rejected by spec OQ-01's resolution.

## Scope check

- Over-scope: none. No immediate interrupt, no signals, no CLI.
- Under-scope: none. The observable checkpoint definition (R10), the stop-at-checkpoint behavior (A3), the KNOWN disposition record (R18), and the budget-breach detection (R11) each have an E-item and a 1:1 V-item.

## Required tests / validation

- `python -m pytest tests/test_runner_stop_level3.py -q` passes.
- Spec acceptance A3 is demonstrated: the turn stops at a checkpoint, the item is recorded stopped/incomplete with KNOWN certainty (explicitly NOT `unknown_outcome`), and the four Phase-0 invariants hold.
- The fake child emits scripted `step_start`/`tool_use` lines so the checkpoint is defined by EVENTS, and a test asserts no wall-clock sleep determines the boundary (spec R10).
- A test proves the stop happens BETWEEN events, not mid-event, by asserting the last observed event is complete.
- `python -m pytest -q` remains green.

## Spec / documentation sync

- Record in the driver comment that the safe-checkpoint definition is spec c4gd2h OQ-01's resolution, citing the event-stream mechanism, so a future reader does not reintroduce an agent-cooperation handshake.
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
  - Required evidence: pasted pytest output showing the checkpoint helper reports a checkpoint ONLY after a complete event line, and does not report one for a partial line; plus an assertion that no `time.sleep`/deadline defines the condition (spec R10), e.g. by driving the whole test on scripted events with a frozen or irrelevant clock.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output for spec A3 showing the event index at which the turn stopped (proving it stopped between events, not mid-event), the process-table observation that the child was reaped, and the remaining three Phase-0 invariants (lock re-acquirable, ledger parses, `git status --porcelain` clean).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted ledger contents after a level-3 stop showing the interrupted item with KNOWN certainty and its last completed operation, zero `unknown_outcome` entries, and no executed/complete/success marking (spec R22). A prose claim of "recorded correctly" fails this item.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted pytest output with a deliberately silent fake child showing the driver recorded the budget-breach/escalation-required marker and RETURNED (bounded), with the elapsed wait shown to be bounded by the Phase-1 deadline rather than indefinite; plus confirmation that no escalation ACTION was taken here (Phase 5's job).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract (inherited from orchestrator `zpbx7o`):

- Open questions: none blocking (spec OQ-01/OQ-03 are RESOLVED in c4gd2h).
- Scope fence: touch ONLY this plan's declared `Scope-Paths`. Widening requires a new plan.
- Honesty rule (hard MUST): paste the ACTUAL runner output into each `V-*` Observed evidence. Never claim a test passed that was not run.
- Commits: path-scoped only; never `git add -A`/`-a`; never push; never tag or release.
- Lifecycle: `aw ipd begin <this> --actor <agent/model>` BEFORE executing (fail-closed), then `aw ipd finalize` after validation passes. Never hand-move to `executed/`.
- If any validation fails, STOP and report rather than marking the plan executed.
