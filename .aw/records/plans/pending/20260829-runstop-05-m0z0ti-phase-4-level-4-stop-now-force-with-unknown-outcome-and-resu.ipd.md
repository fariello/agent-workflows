# IPD: Phase 4: level 4 stop-now-force with unknown_outcome and resume refusal

- Date: 2026-08-29
- Kind: child
- Blocks-Release: next
- From-Backlog: kjzlgw
- Concern: Spec c4gd2h level 4 (STOP-NOW-FORCE) interrupts the current agent turn IMMEDIATELY rather than at a checkpoint, so the item's outcome may be INDETERMINATE and MUST be recorded `unknown_outcome` needing reconciliation before resume (spec R18-R19, R21-R22). This is the level that must never lie: because the driver does not know where the turn was cut, recording anything other than indeterminate would be a fabricated result. It is also the level a later run must REFUSE to blindly resume. Spec is explicit that the ONLY difference from level 3 is outcome CERTAINTY, not cleanliness: level 4 runs the identical Phase-0 cleanup.
- Scope: Implement level 4 in BOTH drivers: interrupt the turn immediately (reusing Phase 0's existing process-group escalation, never a bare kill), record the item `unknown_outcome` with the observed git state, end in the Phase-0 `clean_shutdown`, and make a subsequent run REFUSE to blindly resume such an item (reconcile or require explicit operator action) reusing the research ud28vy reconciliation model. Does NOT add signal handlers or the CLI verb (Phase 5), and does NOT redesign crash recovery (consumed, not re-specified).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_stop.py, tests/test_runner_stop_level4.py, tests/test_oc_runipd.py
- Item-Dependencies: executed:foi1b3
- Status: approved
- Set: runstop
- Order: 5
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: m0z0ti
- Approval: 2026-08-29, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-29 approved (aw set): status set to approved
- 2026-08-29 /plan-review (OpenCode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-501..PR-507. This child carried the orchestrator's pre-existing fact 1 and cited NONE of it (verified: zero references to `requeue_interrupted`/`reconcile_interrupted`/`run_queue`), so three obligations were unimplementable as written. (1) BLOCKER, R19: the refusal was described as a gate for "a new run", but `initialize_run` mints a fresh run_id/run_dir and builds a FRESH queue (:1214-1218), so a new run has no memory of the prior item and nothing to refuse; meanwhile `run_queue` unconditionally calls `reconcile_interrupted` then `requeue_interrupted` on every start/resume (:2481-2483) and the latter flips every `interrupted` item back to `queued` with no operator gate (:2448-2464). E-04 now targets `resume`, wires the refusal INTO `requeue_interrupted`, covers `--retry-incomplete` as the second requeue route, and V-04 fails on helper-only evidence. (2) BLOCKER, R18/R19: no E-item chose a status representation, and both naive options are broken - a new `unknown_outcome` status is absent from `TERMINAL_STATES` (:71-85) and invisible to `reconcile_interrupted` (which only inspects `running`, :2411), `requeue_interrupted` (only `interrupted`, :2451) and the dequeue (only `queued`, :2497), making the item INERT; reusing `interrupted` gets it silently requeued. E-02 now mandates an explicit `certainty: "indeterminate"` flag alongside a status the machinery handles. (3) BLOCKER, R22: nothing owned the pre-existing laundering vector where `reconcile_interrupted` sets `status = "executed"` purely from `plan_bucket(path) == "executed"` (:2422-2432) - for a force-cut turn that records a success the driver never established, which is precisely what this level exists to prevent. Added E-05/V-05 to gate it, with a control case so a legitimate promotion is not simply disabled. Also added `tests/test_oc_runipd.py` to Scope-Paths (E-04 must consciously update the two tests pinning today's auto-requeue at :421-427 and :1043, per CID-4), noted that a level-4 cut usually leaves no outcome JSON so its absence must not be read as information, aligned the R4 assertion with `2ouj70`'s observe-and-report semantics, required the reap be observed through `clean_shutdown`, and switched full-suite evidence to `make test-all`.
- 2026-08-29 reviewed (aw set): status set to reviewed
- 2026-08-29 to-review (aw set): Authored review-ready from spec c4gd2h (graduation of backlog kjzlgw).

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.

## Goal

Implement level 4 (STOP-NOW-FORCE): interrupt the turn immediately, record the interrupted item honestly as `unknown_outcome` with its observed git state, run the identical Phase-0 clean shutdown, and make a later run refuse to blindly resume it (spec R18-R19, R21-R22, A2, A6).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the immediate interrupt

- [ ] E-01 In BOTH drivers, on a level-4 request interrupt the current turn IMMEDIATELY (not at a checkpoint) by delegating to Phase 0's existing process-group escalation (`terminate_process`, oc_runipd.py:1632-1670), then route to `runner_shutdown.clean_shutdown(...)`. Do NOT issue a bare `kill` and do NOT add a second reaper (spec R5; spec level 4 is "interrupt + the reconciliation routine").
  - Depends on: none
  - Expected outcome: with a fake child mid-event and a level-4 request, the turn is cut without waiting for a checkpoint, the child and its group are reaped, and all four Phase-0 invariants hold identically to a level-3 stop.
  - Execution state: pending

### Task group 2: honest indeterminate recording

- [ ] E-02 Record the interrupted item as `unknown_outcome` using Phase 3's record shape with certainty=indeterminate (spec R18): the level that interrupted it, the OBSERVED git state captured at stop time, and the reconciliation a resume must perform first. Never record a last-completed-operation the driver did not observe. DECIDE AND STATE the status representation explicitly, because both naive options are broken (verified): (i) inventing a new per-item `status: "unknown_outcome"` makes the item INERT - `reconcile_interrupted` only touches items whose status is `running` (`oc_runipd.py:2411-2412`), `requeue_interrupted` only requeues `interrupted` (:2451), and the dequeue only selects `queued` (:2497), so nothing would ever reconcile, refuse, or report it, and it is not in `TERMINAL_STATES` (:71-85) either; (ii) reusing `status: "interrupted"` alone hands it to `requeue_interrupted`, which silently re-queues it with no gate, violating R19. Therefore represent indeterminacy as an EXPLICIT FLAG on the item (e.g. `certainty: "indeterminate"` plus the stop level) carried ALONGSIDE a status the existing machinery already understands, and make the E-04 gate branch on that flag. Record the choice and its reason in the code so a later reader does not "normalize" the flag away.
  - Depends on: E-01
  - Expected outcome: the ledger shows the item flagged indeterminate with captured git state and a stated reconciliation requirement; no fabricated last-operation field is present; the item is neither inert (it is visible to reconcile/refuse/report) nor silently requeued; and a test asserts the chosen status is one the existing state machine already handles.
  - Execution state: pending
- [ ] E-03 Enforce spec R22 on this path: assert no item is recorded executed, complete, or successful after a level-4 stop, and record the stop as DELIBERATE (spec R21) so history shows operator intent rather than implying a crash.
  - Depends on: E-02
  - Expected outcome: after a level-4 stop the ledger contains a deliberate-stop record naming level 4, and zero items marked executed/complete/successful; a crash and a level-4 stop are distinguishable in the ledger.
  - Execution state: pending

### Task group 4: close the existing fabricated-success vector

- [ ] E-05 Gate the EXISTING directory-based promotion so an indeterminate item cannot be laundered into a success. `reconcile_interrupted` currently sets `item["status"] = "executed"` whenever `plan_bucket(path) == "executed"` (`oc_runipd.py:2422-2432`), inferring success from the plan's DIRECTORY alone without consulting the outcome artifact or any stop record. For a level-4 cut this is a live R22 violation: if the agent had already moved the plan to `executed/` but was interrupted before its work was complete or verified, the driver records `executed` - a success the driver never established. Make that promotion refuse to fire for an item flagged indeterminate, reporting the conflict (plan in `executed/` but the turn was force-cut) and requiring reconciliation instead. Do NOT change the promotion for ordinary (non-indeterminate) interrupted items; a control test pins that.
  - Depends on: E-02
  - Expected outcome: with the plan moved to `executed/` AND the item flagged indeterminate, `reconcile_interrupted` does NOT mark it `executed`; it reports the conflict and leaves the item requiring reconciliation. An ordinary interrupted item whose plan is in `executed/` is still promoted exactly as today.
  - Execution state: pending

### Task group 3: resume refusal

- [ ] E-04 In BOTH drivers, make a RESUME refuse to blindly re-run an indeterminate item (spec R19), reusing the research `ud28vy` reconciliation model rather than defining a new one. The refusal MUST name the item, its indeterminate state, and the reconciliation action required, so it is actionable rather than an opaque error. TWO CORRECTIONS to the original wording, both verified: (a) the trigger is `resume`, NOT "a new run" - `initialize_run` mints a fresh `run_id`/`run_dir` and refuses if it exists (`oc_runipd.py:1214-1218`), building a FRESH queue from the manifest, so a new run holds no memory of a prior run's item and there is nothing there to refuse; the path that re-touches the same queue is `aw oc run resume` (`main` :2957-2962), which is exactly where the existing auto-requeue lives. (b) The refusal must be wired INTO that existing path, not added beside it: `run_queue` unconditionally calls `reconcile_interrupted(...)` then `requeue_interrupted(...)` on EVERY start/resume (`oc_runipd.py:2481-2483`), and `requeue_interrupted` flips every `interrupted` item straight back to `queued` with `recovery_next = True` and NO operator gate (:2448-2464). So `requeue_interrupted` itself must skip-and-report the indeterminate item; a separate gate added elsewhere would be bypassed by the call that already ran. Also handle `--retry-incomplete`, whose status set (:2484-2497) would otherwise requeue the item by a second route. Update the two existing tests that pin today's auto-requeue behavior (`tests/test_oc_runipd.py:421-427`, `:1043`) consciously rather than deleting them (orchestrator CID-4).
  - Depends on: E-02
  - Expected outcome: `resume` (and `resume --retry-incomplete`) over a queue holding the indeterminate item exits nonzero WITHOUT executing it, printing the item id, its state, and the required reconciliation; the refusal is observed to come from the real `requeue_interrupted`/`run_queue` path rather than a parallel gate; no other queued item is silently skipped or executed out of order; and the two pre-existing auto-requeue tests are updated with a note, not removed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Phase 0 (`2ouj70`) owns the reaper: `terminate_process` already escalates SIGINT -> SIGTERM -> SIGKILL over the process GROUP (`oc_runipd.py:1632-1670`, `_SIGINT_GRACE_SECONDS=5.0`/`_SIGTERM_GRACE_SECONDS=2.0` at :1627-1628). Level 4 REUSES this; spec R5 forbids a second reaper and the spec explicitly says level 4 is "interrupt + the reconciliation routine. NOT a raw kill."
- Research `ud28vy` (`.aw/records/research/20260827-activework-00-ud28vy-active-work-lifecycle-and-toolset-redirect.findings.md`) owns the reconciliation model and the `unknown_outcome` concept; this child CONSUMES it (spec non-goal + GUIDING_PRINCIPLES P8 single source of truth) rather than defining a parallel mechanism.
- Phase 3 (`foi1b3`) already records an interrupted item with KNOWN certainty; level 4 must use the SAME record shape with certainty=indeterminate, not a second schema. Phase 3 (as reviewed) also intercepts `reconcile_disposition` so a deliberate stop is not labelled `failed-safely`; level 4 rides that same interception with indeterminate certainty rather than adding another branch.
- Phase 3 also records a budget-breach/escalation-required marker when no checkpoint is reachable; level 4 is the escalation TARGET of that marker (the action itself is wired in Phase 5, spec A7).
- The driver prompt already mandates a per-item outcome JSON with an explicit `disposition` field including `failed-safely`, so an indeterminate disposition has an established home in an existing artifact rather than needing a new file. BUT note the outcome file is written by the agent at turn END, so a level-4 cut usually leaves NO outcome file at all (or a half-written one) - its absence must not be read as information, and `load_json` failure must not crash the reconcile path.
- The pre-existing recovery machinery is the thing this child must MODIFY, not sit beside: `run_queue` -> `reconcile_interrupted` -> `requeue_interrupted` (`oc_runipd.py:2481-2483`), with the agy counterparts at `agy_runipd.py:2479`, `:2525`, `:2551-2552`. See the verified table in Findings; this is orchestrator pre-existing fact 1 and CID-4.
- Two existing tests pin today's auto-requeue behavior and must be consciously updated, not deleted: `tests/test_oc_runipd.py:421-427` (`requeue_interrupted` returns the item and sets `recovery_next`) and `:1043`.
- `unknown_outcome` is a spec/research TERM (owned by spec c4gd2h section 0.0, modelled on research `ud28vy`), not an existing driver status: `TERMINAL_STATES` (`oc_runipd.py:71-85`) does not contain it. Introducing it as a per-item status would therefore add a state the machinery does not handle.
- Validation-command trap: default `addopts` (`pyproject.toml:122`) is `-m 'not slow'`, so a bare `python -m pytest -q` deselects `slow` subprocess tests; use `make test-all` for full-suite evidence.

## Findings

Why level 4 must record indeterminacy rather than a guess:

| What the driver knows after an immediate interrupt | Consequence |
|---|---|
| the turn was cut at an unobserved point | last completed operation is NOT knowable |
| the tree may hold a partial edit | git state must be captured, not assumed |
| the outcome artifact may be absent or half-written | its presence proves nothing |

Therefore spec R22 (never record executed/complete/successful) and R19 (refuse a blind resume) are the load-bearing requirements, and both are testable by OBSERVATION rather than by inspecting intent.

VERIFIED (2026-08-29): the existing state machine actively fights all three of this child's obligations, and the original draft cited none of it.

| Existing behavior | Where | Consequence for level 4 |
|---|---|---|
| `run_queue` unconditionally calls `reconcile_interrupted` then `requeue_interrupted` on EVERY start/resume | `oc_runipd.py:2481-2483` | any R19 gate added BESIDE this path is bypassed by the call that already ran |
| `requeue_interrupted` flips every `interrupted` item to `queued` + `recovery_next`, no operator gate | :2448-2464 | reusing status `interrupted` means the indeterminate item is silently re-run, violating R19 |
| `reconcile_interrupted` only inspects items with status `running` | :2411-2412 | a NEW status like `unknown_outcome` is never reconciled |
| `requeue_interrupted` only requeues `interrupted`; dequeue only selects `queued`; `TERMINAL_STATES` (:71-85) has no `unknown_outcome` | :2451, :2497, :71 | a new status makes the item INERT: never reconciled, never refused, never reported, never run |
| `reconcile_interrupted` sets `status = "executed"` whenever `plan_bucket(path) == "executed"` | :2422-2432 | if the agent moved the plan to `executed/` before being force-cut, the driver records a SUCCESS it never established: a live R22 violation |
| `--retry-incomplete` requeues a broad status set | :2484-2497 | a second route that would re-run the item even if the first is gated |

So the honest representation is an explicit `certainty: "indeterminate"` FLAG carried alongside a status the machinery already understands (E-02), the refusal must be wired INTO `requeue_interrupted` itself (E-04), and the directory-based promotion must be gated for flagged items (E-05, new).

VERIFIED (2026-08-29): E-04's original trigger was wrong. It said "starting a new run over a queue containing an `unknown_outcome` item", but `initialize_run` mints a fresh `run_id`, creates a fresh `run_dir`, refuses if it already exists, and builds a FRESH queue from the manifest (`oc_runipd.py:1214-1218`). Per-item status lives in that run's own `state.json`, so a NEW run carries no memory of a prior run's item and there is nothing to refuse. The path that re-touches the same queue is `resume` (`main` :2957-2962). Spec A6 says "start a new run over the same queue", which in this driver's model IS resume; the plan now says so explicitly rather than describing an operation that cannot observe the condition.

The resume-refusal has a subtle failure mode worth pinning: refusing must not be indistinguishable from a hard error. An operator needs to know WHY the resume was refused and what to do, so the refusal must name the item, its `unknown_outcome` state, and the reconciliation action. A V-item asserts the message content, not merely the nonzero exit.

Symmetry claim to verify (orchestrator CID-3): level 4 must exist in both drivers with identical semantics, since an operator switching hosts must not get a different guarantee.

## Proposed changes (ordered, validatable)

1. Immediate-interrupt path reusing Phase 0's process-group escalation, ending in `clean_shutdown`.
2. Record the interrupted item with an explicit `certainty: "indeterminate"` flag plus observed git state, carried alongside a status the existing state machine already handles (Phase 3's record shape, indeterminate certainty).
3. Wire the resume refusal INTO the existing `requeue_interrupted` (both drivers) so the unconditional auto-requeue skips and reports the flagged item, covering `--retry-incomplete` too, and consciously update the two tests that pin today's behavior.
4. Gate `reconcile_interrupted`'s directory-based promotion so a flagged item cannot be laundered into `executed`, leaving ordinary promotion intact.
5. New `tests/test_runner_stop_level4.py` proving indeterminacy is recorded, cleanliness holds, resume is refused through the real entry point, the laundering case is blocked, and the control cases still pass.

## Deferred / out of scope (with reason)

- Signal handlers (repeated SIGINT escalating to level 4) and `aw oc/agy run stop --now-force`: Phase 5 (`71vjbn`); tests here request level 4 by writing the Phase-1 record directly.
- ENFORCING escalation from a Phase-3 budget breach into level 4: Phase 5 (spec A7). This child provides the level-4 behavior that escalation targets.
- Crash-recovery redesign and the reconciliation ALGORITHM: research `ud28vy` owns it; this child calls it.
- Automatic reconciliation without operator action: spec OQ-04 is non-blocking and leans operator-gated; this child implements the REFUSAL (R19) and leaves auto-reconcile out.

## Scope check

- Over-scope: none. No signals, no CLI, no reconciliation ALGORITHM redesign. E-04's edit to `requeue_interrupted` and E-05's gate on `reconcile_interrupted` are in-scope corrections of the existing path, not a redesign: without them R19 and R22 are unmet by construction, because the existing calls run first and unconditionally.
- Under-scope: as originally written, YES, in three ways now fixed. (1) The resume refusal was described as a new gate for "a new run", but the existing `run_queue` -> `requeue_interrupted` path already auto-requeues unconditionally and a new run has a fresh queue, so the gate had to move INTO that path and key off `resume` (E-04). (2) No E-item chose a status representation, and both naive choices are broken (a new status makes the item inert; reusing `interrupted` gets it silently requeued), so R18/R19 were unimplementable as written (E-02). (3) Nothing owned the pre-existing fabricated-success vector where `reconcile_interrupted` promotes an item to `executed` from the plan's directory alone, which is exactly the R22 violation this level exists to prevent (E-05, new). The immediate interrupt, the honest indeterminate record (R18, R22), the deliberate-vs-crash distinction (R21), the resume refusal (R19), and the promotion gate each now have an E-item and a 1:1 V-item.

## Required tests / validation

- `python -m pytest tests/test_runner_stop_level4.py -q -m ''` passes (pass `-m ''` so `slow`-marked subprocess tests in this file are not silently deselected).
- Spec acceptance A2 (the interrupt path ends at level 4 with an indeterminate record) and A6 (a RESUME refuses to blindly re-run it) are demonstrated with a fake child, A6 driven through the real `run_queue`/`requeue_interrupted` entry rather than a helper.
- Both requeue routes are covered: plain `resume` and `resume --retry-incomplete`.
- Every level-4 test also asserts the four Phase-0 invariants, proving cleanliness is IDENTICAL to level 3 (spec: the only difference is certainty), with R4 asserted as "tree unchanged by cleanup" per `2ouj70`'s reviewed observe-and-report semantics rather than "tree clean".
- A test proves no item is ever recorded executed/complete/successful after a level-4 stop (spec R22), INCLUDING the laundering case where the plan already sits in `executed/`.
- Control tests prove the fixes did not break ordinary recovery: an ordinary interrupted item is still requeued, and an ordinary interrupted item whose plan is in `executed/` is still promoted.
- A test proves a missing or half-written outcome JSON does not crash the reconcile path and is not read as information.
- `make test-all` (`python -m pytest tests/ -m ''`) remains green: the FULL suite, since a bare `python -m pytest -q` deselects `-m 'not slow'` per `pyproject.toml:122`.

## Spec / documentation sync

- Record in the driver comment that level 4's cleanliness is identical to level 3 and only certainty differs, citing spec c4gd2h, so a future reader does not "optimize" level 4 into a bare kill.
- Note in the code that the reconciliation routine is research `ud28vy`'s and must not be reimplemented here.
- Record next to the `requeue_interrupted` and `reconcile_interrupted` gates WHY they exist: the unconditional auto-requeue would otherwise silently re-run an indeterminate item (spec R19), and the directory-based promotion would otherwise record a success the driver never established (spec R22). Without that note the gates look like redundant special cases and are likely to be "cleaned up".
- Record the chosen status representation and why a bare new `unknown_outcome` status was rejected (it is absent from `TERMINAL_STATES` and invisible to reconcile/requeue/dequeue, making the item inert).
- No user-facing doc change yet; Phase 5 documents the trigger surface.

## Open questions

### OQ-01: Should a level-4 stop attempt reconciliation immediately, or only record `unknown_outcome` and defer?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: only RECORD and defer. Spec R19 requires refusing a blind resume, not auto-healing, and spec OQ-04 (non-blocking) leans operator-gated with automatic reconciliation allowed only when git state is provably clean. Attempting reconciliation inside the stop path would also run reconciliation while the tree is least trustworthy, and GUIDING_PRINCIPLES P10 (safety, reversibility) favors recording over acting. Resolved from the spec; auto-reconcile stays out of scope.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted pytest output showing the turn was cut mid-event (the event index proving no checkpoint was awaited), the process-table observation that no descendant survives, and the remaining three Phase-0 invariants (lock re-acquirable, ledger parses, and `git status --porcelain` UNCHANGED by cleanup per `2ouj70`'s observe-and-report R4 semantics - not "clean"). Cleanliness must be shown EQUAL to the level-3 case, and the reap must be observed to go through `clean_shutdown` rather than a local `terminate_process` call (spec R5).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted ledger contents after a level-4 stop showing `unknown_outcome`, the captured git state, and the stated reconciliation requirement; plus an assertion that no last-completed-operation value was invented. A prose claim of "recorded as unknown" fails this item.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output asserting zero executed/complete/successful markings after a level-4 stop (spec R22), plus pasted ledger records for a level-4 stop AND a simulated crash side by side showing they are distinguishable (spec R21).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted output of `resume` AND of `resume --retry-incomplete` over a queue holding the indeterminate item, each showing the nonzero exit, the item id and state in the message, and the named reconciliation action (spec A6); plus evidence the item was NOT executed and no other item ran out of order. The refusal MUST be demonstrated through the real `run_queue`/`requeue_interrupted` entry (orchestrator CID-4), not by calling a refusal helper directly - evidence that only exercises a helper FAILS this item, since the existing unconditional requeue would bypass it. Also paste the diff/note showing the two pre-existing auto-requeue tests (`tests/test_oc_runipd.py:421-427`, `:1043`) were consciously updated rather than deleted.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted pytest output for the laundering case - plan moved into `executed/` while the item is flagged indeterminate - showing `reconcile_interrupted` does NOT set `status = "executed"` and instead reports the conflict; PLUS a pasted CONTROL case showing an ordinary interrupted item whose plan is in `executed/` is still promoted as today. Both halves are required: without the control, the fix could have simply disabled a legitimate promotion.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract (inherited from orchestrator `zpbx7o`):

- Open questions: none blocking FOR THIS CHILD (spec OQ-01/OQ-03 are RESOLVED in c4gd2h; OQ-01 here is resolved). The orchestrator's OQ-02 (spec A10 / Windows) gates `71vjbn` only.
- Scope fence: touch ONLY this plan's declared `Scope-Paths`, plus the two pre-existing tests E-04 must consciously update (`tests/test_oc_runipd.py`). Widening requires a new plan. Specifically: modify `requeue_interrupted` and `reconcile_interrupted` ONLY to add the indeterminate-item gates - do NOT change ordinary interrupted-item recovery (control tests pin both), do NOT reimplement the reconciliation ALGORITHM (research `ud28vy` owns it), and do NOT introduce `unknown_outcome` as a new per-item status in `TERMINAL_STATES`.
- Honesty rule (hard MUST): paste the ACTUAL runner output into each `V-*` Observed evidence. Never claim a test passed that was not run.
- Commits: path-scoped only; never `git add -A`/`-a`; never push; never tag or release.
- Lifecycle: `aw ipd begin <this> --actor <agent/model>` BEFORE executing (fail-closed), then `aw ipd finalize` after validation passes. Never hand-move to `executed/`.
- If any validation fails, STOP and report rather than marking the plan executed.
