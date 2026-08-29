# IPD: Phase 2: levels 1 and 2 (stop-after-call, stop-after-set) at between-turn checkpoints

- Date: 2026-08-29
- Kind: child
- Blocks-Release: next
- From-Backlog: kjzlgw
- Concern: Spec c4gd2h levels 1 and 2 are the two BETWEEN-TURN stop levels: STOP-AFTER-CALL lets the in-flight IPD's agent turn finish (write outcome JSON, checkpoint ledger) then declines to dequeue the next item; STOP-AFTER-SET finishes the rest of THIS set's queue then stops before any next set. Both are the cheapest levels to implement correctly because neither interrupts a running turn, so neither can produce an indeterminate outcome (spec R20: no `unknown_outcome` items). They must exist before the turn-interrupting levels so the queue-control path is proven independently of turn interruption.
- Scope: Implement levels 1 and 2 in BOTH drivers: consult the Phase-1 poll at the between-item checkpoint, and when a level 1 or 2 request is present, stop dequeuing at the correct boundary (next item for level 1; next SET for level 2) and end in the Phase-0 `clean_shutdown`. Record the deliberate stop in the ledger as a non-failure. Does NOT interrupt a running turn (Phases 3-4), install signal handlers, or add the CLI verb (Phase 5).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_stop.py, tests/test_runner_stop_levels12.py
- Item-Dependencies: executed:gq6m2u
- Status: reviewed
- Set: runstop
- Order: 3
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: 1qxuke

## Workflow history
- 2026-08-29 /plan-review (OpenCode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-301..PR-306. Two BLOCKERs, both verified by running the real code rather than reading it. (1) The plan demanded "exit 0" four times (spec A1/A4), but `run_queue` ends `return 0 if all(item["status"] in SUCCESS_STATES ...) else 1` (`oc_runipd.py:2653`, `SUCCESS_STATES` at :90) and a deliberate stop intentionally leaves items `queued`; evaluated directly, `['executed','queued','queued']` returns 1, so no E-item made the plan's own acceptance criteria reachable. Added E-05/V-05 owning an honest deliberate-stop exit path, with V-05 requiring the queue to STILL show `queued` next to the 0 so the exit cannot be bought by laundering statuses (spec R22). (2) E-02 treated "the rest of THIS set" as self-evident, but the runtime dequeue is DEPENDENCY-ordered, not set-ordered (`:2500-2505` scans the whole queue), so sets interleave: demonstrated against the real `dependency_status` that with set A's next item blocked, the driver's next pick is a set-B item, meaning the in-flight set jumps A -> B while A still has queued work. E-02 now captures the current `setid` at request-observation time and leaves other-set items queued even when runnable, with the interleaved case pinned in its expected outcome and recorded as resolved OQ-02. Also pinned the ledger substrate concretely (`events.jsonl` via `append_jsonl`, NOT `run_ledger_store.py`, which neither driver imports), corrected the R4 invariant assertion to match `2ouj70`'s observe-and-report semantics (unchanged tree, not clean tree), switched full-suite evidence to `make test-all` since a bare `pytest -q` deselects the `slow` subprocess class these tests belong to, and replaced the false "Under-scope: none".
- 2026-08-29 reviewed (aw set): status set to reviewed
- 2026-08-29 to-review (aw set): Authored review-ready from spec c4gd2h (graduation of backlog kjzlgw).

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.

## Goal

Implement the two between-turn stop levels (STOP-AFTER-CALL and STOP-AFTER-SET) so a run can wind down at a queue boundary with no interrupted turn and therefore no indeterminate outcome (spec R20, A1, A4), each ending in the Phase-0 clean shutdown.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: level 1 (STOP-AFTER-CALL)

- [ ] E-01 In BOTH drivers, branch on a level-1 request observed at the between-item checkpoint: allow the in-flight turn to finish normally (its outcome JSON written, ledger checkpointed), then do NOT dequeue the next item, run `runner_shutdown.clean_shutdown(...)`, and exit 0. Do not touch the turn itself. This REQUIRES the exit-code change in E-05: the existing `run_queue` return is `0 if all(item["status"] in SUCCESS_STATES ...) else 1` (`oc_runipd.py:2653`), and a level-1 stop deliberately leaves items `queued`, which is NOT a success state, so the unmodified code returns 1 and spec A1's "exits 0" cannot hold.
  - Depends on: E-05
  - Expected outcome: with a 3-item queue and a level-1 request written during item 1, exactly item 1 completes, items 2-3 never start, exit code 0, and all four Phase-0 invariants hold.
  - Execution state: pending

### Task group 2: level 2 (STOP-AFTER-SET)

- [ ] E-02 In BOTH drivers, branch on a level-2 request: continue dequeuing items whose `setid` matches the CURRENT set (the driver already tracks `item['setid']`, see `oc_runipd.py:1722-1727`), then stop before the first item of any OTHER set, run `clean_shutdown`, exit 0. DEFINE "the current set" precisely as the `setid` of the item that was in flight when the level-2 request was OBSERVED, captured once and held for the rest of the wind-down. This matters because the runtime dequeue is DEPENDENCY-ordered, not set-ordered: `run_queue` picks the first `queued` item whose dependencies are satisfied, scanning the entire queue (`oc_runipd.py:2500-2505`), so sets can INTERLEAVE (proven in Findings) and a naive "stop when `setid` changes" rule would stop at the wrong place or resume the original set later. During a level-2 wind-down, an item of any other set is treated as out-of-scope and left `queued`, even if it is the only runnable item; in that case the wind-down ends immediately rather than running it.
  - Depends on: E-01, E-05
  - Expected outcome: with a queue of set A (2 items) then set B (2 items) and a level-2 request during A's first item, both A items complete, neither B item starts, exit 0, invariants hold. Additionally, with A's second item BLOCKED on an unmet dependency and a B item runnable, the driver does NOT run the B item: it ends the wind-down with A's blocked item left `queued`.
  - Execution state: pending
- [ ] E-03 Handle the final-set boundary explicitly (OQ-01): a level-2 request while on the last set completes that set and exits 0 with nothing skipped, still running `clean_shutdown` so the invariant is uniform (spec R5/R6).
  - Depends on: E-02
  - Expected outcome: a level-2 request during the only set completes all its items, exits 0, records the deliberate stop, and satisfies the invariants; no special-case path bypasses `clean_shutdown`.
  - Execution state: pending

### Task group 3: ledger honesty

- [ ] E-04 Record the deliberate stop in the run ledger as a NON-FAILURE carrying the level that caused it (spec R21), distinguishable from a crash, and assert no item is marked `unknown_outcome` for levels 1-2 (spec R20) since no turn was interrupted. Concretely: append a new `events.jsonl` event (the established append-only ledger channel, written via `append_jsonl(run_dir / "events.jsonl", ...)`, e.g. `oc_runipd.py:1325`, `:2442`, `:2457`) naming the event as a deliberate stop plus its level and requester, and leave un-run items in their existing `queued` state rather than inventing a new per-item status. Do NOT introduce a new ledger file or use `run_ledger_store.py` here: the drivers do not import it today (verified: no reference in either driver), so adopting it would be a new substrate, not the established one.
  - Depends on: E-01, E-02
  - Expected outcome: after a level 1 or 2 stop the ledger parses, `events.jsonl` contains a deliberate-stop event naming the level, zero items are `unknown_outcome`, un-run items remain `queued`, and no completed item is reported as failed.
  - Execution state: pending

### Task group 4: the exit-code contract a deliberate stop needs

- [ ] E-05 Make a DELIBERATE stop exit 0 without lying about the queue. Today `run_queue` ends with `return 0 if all(item["status"] in SUCCESS_STATES for item in state["queue"]) else 1` (`oc_runipd.py:2653`; `SUCCESS_STATES = {"executed", "reviewed", "approved"}` at :90), so a level-1/2 stop that intentionally leaves items `queued` returns 1. Verified by direct evaluation: a queue of `['executed','queued','queued']` yields 1. Spec A1 and A4 both require exit 0, so add an explicit deliberate-stop exit path that returns 0 when the run ended because of an observed stop request AND every item that actually RAN reached a success state. It MUST NOT return 0 when an item genuinely failed, and it MUST NOT mark un-run items as successful to satisfy the existing predicate (that would be the greenwash spec R22 forbids). Land the same contract in `agy_runipd.py`.
  - Depends on: none
  - Expected outcome: a level-1/2 stop with all run items successful exits 0 while its un-run items are still `queued`; a stop whose last run item FAILED exits nonzero; no item's status is rewritten to manufacture the 0.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Phase 0 (`2ouj70`) provides `runner_shutdown.clean_shutdown(...)`; Phase 1 (`gq6m2u`) provides `runner_stop.poll_stop(run_dir)` at the between-item checkpoint (`run_queue`'s dequeue loop, `oc_runipd.py:2494-2500`). This child ONLY adds the branch that acts on levels 1-2; it must not add a third mechanism.
- The driver processes a QUEUE of work items and tracks each item's `setid` (visible in the run prompt construction and title, e.g. `aw-{action_label}-{run_id}-{item['setid']}-{item['id6']}`, `oc_runipd.py:1722-1727`), so a set is identifiable from data the driver already has. But `setid` alone does NOT make "the rest of THIS set" well-defined at runtime: the dequeue is dependency-ordered and sets can interleave (see Findings), so the current set must be captured at request time.
- The run's exit contract lives at `oc_runipd.py:2653` (`SUCCESS_STATES` at :90). It treats any non-success status, including `queued`, as failure, so a deliberate stop needs an explicit exit path (E-05).
- The established ledger channel is the append-only `events.jsonl` written through `append_jsonl(...)` (`oc_runipd.py:1325`, `:2442`, `:2457`), with `state.json` holding per-item status via `save_state`. `agent_workflows/run_ledger_store.py` exists but neither driver imports it, so it is NOT the established substrate here and must not be adopted by this child.
- Validation-command trap: default `addopts` (`pyproject.toml:122`) is `-m 'not slow'`, so a bare `python -m pytest -q` silently deselects `slow` subprocess tests. This child's tests spawn a real driver over a fake child, so full-suite evidence must come from `make test-all`.
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

VERIFIED (2026-08-29): "the rest of THIS set" is NOT a contiguous queue suffix, because the dequeue is DEPENDENCY-ordered, not set-ordered. `run_queue` selects the first `queued` item whose dependencies are satisfied by scanning the WHOLE queue (`oc_runipd.py:2500-2505`), even though `initialize_run` BUILDS the queue set-contiguously (`expand_selectors` walks sets in manifest order, :987-994). Demonstrated against the real `dependency_status`: with the queue `A/a1 (executed), A/a2 (blocked on an unmet dep), B/b1 (ready)`, the driver's next dequeue is `B/b1` - the in-flight set jumps A -> B while set A still holds a queued item. Consequences E-02 must handle rather than discover: (a) "the current set" must be CAPTURED at request-observation time, not re-derived from whatever item happens to run next; (b) a "stop when `setid` changes" rule is wrong in both directions (it can stop early on an interleave, or resume set A after B and never stop); (c) during a level-2 wind-down a runnable item of another set must be LEFT queued rather than run, which means level 2 can legitimately end with runnable work outstanding.

VERIFIED (2026-08-29): exit 0 is not free. `run_queue` ends `return 0 if all(item["status"] in SUCCESS_STATES for item in state["queue"]) else 1` (:2653), with `SUCCESS_STATES = {"executed","reviewed","approved"}` (:90). A deliberate stop intentionally leaves items `queued`, which is not a success state, so the unmodified predicate returns **1** (evaluated directly on `['executed','queued','queued']`). Spec A1 and A4 both demand exit 0, so this child MUST change the exit contract (E-05). The tempting shortcut - marking un-run items as some success-ish status so the existing predicate yields 0 - is exactly the fabricated-disposition failure spec R22 forbids, which is why V-05 requires the queue to still show `queued` alongside the 0.

## Proposed changes (ordered, validatable)

1. A deliberate-stop exit path so an intentional stop returns 0 without rewriting any item's status (the current predicate returns 1 whenever items remain `queued`).
2. Level 1 branch: on a level-1 request observed at the between-item checkpoint, let the current turn finish, do not dequeue the next item, run `clean_shutdown`, exit 0.
3. Level 2 branch: same, but the boundary is the captured in-flight `setid`; items of any other set are left `queued` even when runnable, since the dependency-ordered dequeue can interleave sets.
4. Ledger recording of the deliberate stop as a non-failure `events.jsonl` event naming the level, with un-run items left `queued`.
5. New `tests/test_runner_stop_levels12.py` asserting which items ran, the interleaved-set case, both exit-code directions, that no `unknown_outcome` exists, and that the Phase-0 invariants hold.

## Deferred / out of scope (with reason)

- Interrupting a running turn (levels 3 and 4): Phases 3 (`foi1b3`) and 4 (`m0z0ti`).
- Signal handlers and `aw oc/agy run stop`: Phase 5 (`71vjbn`). Tests here request a level by writing the Phase-1 record directly.
- Escalation when a level 1/2 wind-down exceeds its budget: the budget is recorded in Phase 1 and enforced in Phase 5 alongside the trigger UX (spec A7), because escalation is a cross-level concern.
- Driver unification (backlog `dhuape`).

## Scope check

- Over-scope: none. No turn interruption, no signals, no CLI. E-05 (the exit contract) is not over-scope: spec A1/A4 both require exit 0 and the current predicate returns 1 for any deliberate stop, so without it this child cannot meet its own acceptance criteria.
- Under-scope: as originally written, YES, in two ways now fixed. (1) The exit-0 requirement appeared four times with no E-item changing the exit predicate that makes it impossible; E-05/V-05 now own it. (2) "The rest of THIS set" was treated as self-evident when the dependency-ordered dequeue lets sets interleave, leaving the level-2 boundary ambiguous; E-02 now defines it as the captured in-flight `setid` and pins the interleaved case. Level 1 boundary, level 2 boundary, R20, R21, the last-set case, and the exit contract each now have an E-item and a 1:1 V-item.

## Required tests / validation

- `python -m pytest tests/test_runner_stop_levels12.py -q -m ''` passes (pass `-m ''` so `slow`-marked subprocess tests in this file are not silently deselected).
- Spec acceptance A1 (level 1) and A4 (level 2, out-of-band request) are demonstrated with a fake child, asserting the exact set of items that ran, read from the ledger/outcome artifacts rather than a mock call count.
- The INTERLEAVED-set case is tested explicitly: set A's next item blocked on an unmet dependency while another set's item is runnable, asserting the level-2 wind-down does not run the other set's item.
- The exit contract is tested in both directions: exit 0 for a clean deliberate stop with items still `queued`, and nonzero when a run item genuinely failed.
- Every level 1/2 test also asserts the Phase-0 invariants (no orphan via process table, lock re-acquirable, ledger parses, and for R4 that `git status --porcelain` is UNCHANGED by cleanup per `2ouj70`'s observe-and-report semantics, not that the tree is clean).
- No test uses a wall-clock sleep to define a boundary.
- `make test-all` (`python -m pytest tests/ -m ''`) remains green: the FULL suite, since a bare `python -m pytest -q` deselects `-m 'not slow'` per `pyproject.toml:122`.

## Spec / documentation sync

- No user-facing doc change yet; Phase 5 documents the trigger surface. Levels are not reachable by a user until Phase 5 wires signals and the `stop` verb, which is why this child's tests request the level by writing the Phase-1 record directly.
- Record in the driver code comment which spec level each branch implements (level 1 = R20/A1, level 2 = R20/A4).

## Open questions

### OQ-01: On a level-2 request during the FINAL set, is exit 0 with nothing skipped the correct behavior?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: yes. Spec level 2 stops "before any next set"; when no next set exists the boundary is the natural end of the run, so it is indistinguishable from normal completion EXCEPT that the ledger records the deliberate stop (spec R21). `clean_shutdown` still runs so the invariant holds uniformly (R5/R6). Resolved from the spec; a V-item pins it because it is the case most likely to be special-cased wrongly.

### OQ-02: During a level-2 wind-down, should a runnable item of ANOTHER set be left queued (chosen) or run?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: LEAVE IT QUEUED. This question only exists because the dequeue is dependency-ordered, so sets interleave (proven in Findings: with set A's next item blocked, the driver's next pick is a set-B item). Spec level 2 is defined as "the rest of THIS set's queue finishes; stops before any next set", so running another set's item during a level-2 wind-down would directly violate the level's contract and surprise an operator who asked to stop after the current set. The cost is that a level-2 stop can end with runnable work outstanding, which is correct: the operator asked to wind down, not to drain the queue. Resolved from the spec's own definition plus the verified dequeue behavior, not deferred. E-02 implements it and its expected outcome pins the interleaved case.

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
  - Required evidence: pasted `events.jsonl` contents after a level 1 and a level 2 stop showing the deliberate-stop event with its level and requester, zero `unknown_outcome` entries (spec R20), un-run items still `queued`, and no false failure marking. A prose claim that the ledger "is coherent" fails this item, as does introducing a new ledger file or substrate.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted pytest output showing (a) the process exit code is 0 after a level-1 and a level-2 stop WHILE the pasted `state.json` queue still shows un-run items as `queued` (proving the 0 was not bought by rewriting statuses), and (b) a stop whose last run item failed exits NONZERO. Both halves are required: evidence of only the exit 0 case would not distinguish the honest path from status-laundering (spec R22).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract (inherited from orchestrator `zpbx7o`):

- Open questions: none blocking FOR THIS CHILD (spec OQ-01/OQ-03 are RESOLVED in c4gd2h; OQ-01 here is resolved). The orchestrator's OQ-02 (spec A10 / Windows) gates `71vjbn` only.
- Scope fence: touch ONLY this plan's declared `Scope-Paths`. Widening requires a new plan. Specifically: do NOT rewrite any item's status to make the exit code 0 (spec R22), do NOT adopt `run_ledger_store.py` as a new ledger substrate (neither driver uses it), and do NOT change the dependency-ordered dequeue itself - level 2 constrains which items it will run, it does not reorder the queue.
- Honesty rule (hard MUST): paste the ACTUAL runner output into each `V-*` Observed evidence. Never claim a test passed that was not run.
- Commits: path-scoped only; never `git add -A`/`-a`; never push; never tag or release.
- Lifecycle: `aw ipd begin <this> --actor <agent/model>` BEFORE executing (fail-closed), then `aw ipd finalize` after validation passes. Never hand-move to `executed/`.
- If any validation fails, STOP and report rather than marking the plan executed.
