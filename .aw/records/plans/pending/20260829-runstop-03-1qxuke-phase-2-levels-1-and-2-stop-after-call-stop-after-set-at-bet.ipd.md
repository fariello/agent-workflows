# IPD: Phase 2: levels 1 and 2 (stop-after-call, stop-after-set) at between-turn checkpoints

- Date: 2026-08-29
- Kind: child
- Blocks-Release: next
- From-Backlog: kjzlgw
- Concern: Spec c4gd2h levels 1 and 2 are the two BETWEEN-TURN stop levels: STOP-AFTER-CALL lets the in-flight IPD's agent turn finish (write outcome JSON, checkpoint ledger) then declines to dequeue the next item; STOP-AFTER-SET finishes the rest of THIS set's queue then stops before any next set. Both are the cheapest levels to implement correctly because neither interrupts a running turn, so neither can produce an indeterminate outcome (spec R20: no `unknown_outcome` items). They must exist before the turn-interrupting levels so the queue-control path is proven independently of turn interruption.
- Scope: Implement levels 1 and 2 in BOTH drivers: consult the Phase-1 poll at the between-item checkpoint, and when a level 1 or 2 request is present, stop dequeuing at the correct boundary (next item for level 1; next SET for level 2) and end in the Phase-0 `clean_shutdown`. Record the deliberate stop in the ledger as a non-failure. Does NOT interrupt a running turn (Phases 3-4), install signal handlers, or add the CLI verb (Phase 5).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_stop.py, tests/test_runner_stop_levels12.py
- Item-Dependencies: executed:gq6m2u
- Status: to-review
- Set: runstop
- Order: 3
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: 1qxuke

## Workflow history
- 2026-08-29 to-review (aw set): Authored review-ready from spec c4gd2h (graduation of backlog kjzlgw).

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.

## Goal

Implement the two between-turn stop levels (STOP-AFTER-CALL and STOP-AFTER-SET) so a run can wind down at a queue boundary with no interrupted turn and therefore no indeterminate outcome (spec R20, A1, A4), each ending in the Phase-0 clean shutdown.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: level 1 (STOP-AFTER-CALL)

- [ ] E-01 In BOTH drivers, branch on a level-1 request observed at the between-item checkpoint: allow the in-flight turn to finish normally (its outcome JSON written, ledger checkpointed), then do NOT dequeue the next item, run `runner_shutdown.clean_shutdown(...)`, and exit 0. Do not touch the turn itself.
  - Depends on: none
  - Expected outcome: with a 3-item queue and a level-1 request written during item 1, exactly item 1 completes, items 2-3 never start, exit code 0, and all four Phase-0 invariants hold.
  - Execution state: pending

### Task group 2: level 2 (STOP-AFTER-SET)

- [ ] E-02 In BOTH drivers, branch on a level-2 request: continue dequeuing items whose `setid` matches the CURRENT set (the driver already tracks `item['setid']`, see `oc_runipd.py:1722-1727`), then stop before the first item of any next set, run `clean_shutdown`, exit 0.
  - Depends on: E-01
  - Expected outcome: with a queue of set A (2 items) then set B (2 items) and a level-2 request during A's first item, both A items complete, neither B item starts, exit 0, invariants hold.
  - Execution state: pending
- [ ] E-03 Handle the final-set boundary explicitly (OQ-01): a level-2 request while on the last set completes that set and exits 0 with nothing skipped, still running `clean_shutdown` so the invariant is uniform (spec R5/R6).
  - Depends on: E-02
  - Expected outcome: a level-2 request during the only set completes all its items, exits 0, records the deliberate stop, and satisfies the invariants; no special-case path bypasses `clean_shutdown`.
  - Execution state: pending

### Task group 3: ledger honesty

- [ ] E-04 Record the deliberate stop in the run ledger as a NON-FAILURE carrying the level that caused it (spec R21), distinguishable from a crash, and assert no item is marked `unknown_outcome` for levels 1-2 (spec R20) since no turn was interrupted.
  - Depends on: E-01, E-02
  - Expected outcome: after a level 1 or 2 stop the ledger parses, shows a deliberate-stop record naming the level, contains zero `unknown_outcome` items, and no completed item is reported as failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Phase 0 (`2ouj70`) provides `runner_shutdown.clean_shutdown(...)`; Phase 1 (`gq6m2u`) provides `runner_stop.poll_stop(run_dir)` at the between-item checkpoint. This child ONLY adds the branch that acts on levels 1-2; it must not add a third mechanism.
- The driver processes a QUEUE of work items and tracks each item's `setid` (visible in the run prompt construction and title, e.g. `aw-{action_label}-{run_id}-{item['setid']}-{item['id6']}`, `oc_runipd.py:1722-1727`), so "the rest of THIS set" is expressible from data the driver already has.
- Per-item outcome JSON is already a required artifact (the driver prompt mandates writing `outcomes/<NN>-<id6>.json`), so level 1's "let the turn finish" boundary coincides with an artifact the driver can verify exists.
- The run ledger already distinguishes dispositions; a deliberate stop must be recorded as a non-failure (spec R21) so history shows operator intent rather than implying breakage.
- `agy_runipd.py` mirrors the queue loop; land symmetrically per orchestrator CID-3.

## Findings

The two levels differ ONLY in which boundary stops the dequeue:

| Level | Boundary | Items completed | `unknown_outcome` produced |
|---|---|---|---|
| 1 STOP-AFTER-CALL | next ITEM | the in-flight turn only | none (spec R20) |
| 2 STOP-AFTER-SET | next SET | the rest of the current set's queue | none (spec R20) |

Because neither level interrupts a turn, the correctness argument is entirely about the DEQUEUE decision, which makes it testable with a fake child that always completes: the assertion is about WHICH items ran, not about how a turn was cut short. That is why these levels come before Phases 3-4.

One subtlety worth pinning: a level 2 request that arrives while the driver is on the LAST item of the final set must behave identically to a normal completion (nothing left to skip), and must still run `clean_shutdown` so the invariant holds uniformly (spec R5/R6). A test must cover that boundary explicitly, since it is the case most likely to be special-cased incorrectly.

## Proposed changes (ordered, validatable)

1. Level 1 branch: on a level-1 request observed at the between-item checkpoint, let the current turn finish, do not dequeue the next item, run `clean_shutdown`, exit 0.
2. Level 2 branch: same but the boundary is the next SET rather than the next item.
3. Ledger recording of the deliberate stop as a non-failure with the level that caused it.
4. New `tests/test_runner_stop_levels12.py` asserting which items ran, that no `unknown_outcome` exists, and that the Phase-0 invariants hold.

## Deferred / out of scope (with reason)

- Interrupting a running turn (levels 3 and 4): Phases 3 (`foi1b3`) and 4 (`m0z0ti`).
- Signal handlers and `aw oc/agy run stop`: Phase 5 (`71vjbn`). Tests here request a level by writing the Phase-1 record directly.
- Escalation when a level 1/2 wind-down exceeds its budget: the budget is recorded in Phase 1 and enforced in Phase 5 alongside the trigger UX (spec A7), because escalation is a cross-level concern.
- Driver unification (backlog `dhuape`).

## Scope check

- Over-scope: none. No turn interruption, no signals, no CLI.
- Under-scope: none. Level 1 boundary, level 2 boundary, the no-`unknown_outcome` guarantee (R20), the deliberate-vs-crash ledger record (R21), and the last-item boundary case each have an E-item and a 1:1 V-item.

## Required tests / validation

- `python -m pytest tests/test_runner_stop_levels12.py -q` passes.
- Spec acceptance A1 (level 1) and A4 (level 2, out-of-band request) are demonstrated with a fake child, asserting the exact set of items that ran.
- Every level 1/2 test also asserts the Phase-0 invariants (no orphan via process table, lock re-acquirable, ledger parses, `git status --porcelain` clean).
- No test uses a wall-clock sleep to define a boundary.
- `python -m pytest -q` remains green.

## Spec / documentation sync

- No user-facing doc change yet; Phase 5 documents the trigger surface. Levels are not reachable by a user until Phase 5 wires signals and the `stop` verb, which is why this child's tests request the level by writing the Phase-1 record directly.
- Record in the driver code comment which spec level each branch implements (level 1 = R20/A1, level 2 = R20/A4).

## Open questions

### OQ-01: On a level-2 request during the FINAL set, is exit 0 with nothing skipped the correct behavior?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: yes. Spec level 2 stops "before any next set"; when no next set exists the boundary is the natural end of the run, so it is indistinguishable from normal completion EXCEPT that the ledger records the deliberate stop (spec R21). `clean_shutdown` still runs so the invariant holds uniformly (R5/R6). Resolved from the spec; a V-item pins it because it is the case most likely to be special-cased wrongly.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted pytest output for spec A1 showing the exact items that ran (item 1 only, from the ledger/outcome files, not from a mock call count), exit code 0, plus the four Phase-0 invariant observations (process table, lock re-acquire, ledger parse, `git status --porcelain`).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output for spec A4 showing both set-A items completed and neither set-B item started (asserted from the ledger/outcome artifacts), exit 0, and the four invariants.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output for the final-set case showing all items completed, exit 0, the deliberate-stop record present, and evidence that `clean_shutdown` still ran (its report or the invariant observations) rather than being skipped by a special case.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted ledger contents after a level 1 and a level 2 stop showing the deliberate-stop record with its level, zero `unknown_outcome` entries (spec R20), and no false failure marking. A prose claim that the ledger "is coherent" fails this item.
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
