# Review findings: plan epsti7

- Subject-Id: epsti7
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (BLOCKER, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `7c09f7e2c`, which already carries the `0jooqz` review's edit to this plan's E-02 (consume `attempt["questions_verdict"]`). The plan was byte-identical to the lane input. `aw ipd lint --phase author --agent`: `clean`. Child plan.

Verified:
- `runner_shutdown.KNOWN_ITEM_STATUSES`, `runner_shared.IN_FLIGHT_QUEUE_STATUSES`, `TERMINAL_STATES`, `EXECUTION_SUCCESS_STATES` and the `*_REPORTING_SUCCESS_STATES` sets exist; none contains `awaiting-human`.
- `lifecycle_style` already maps `("awaiting-human", WAITING_INPUT)` in both status tables; `runner_shared.map_driver_status_to_run_state` has no entry for it.
- `cascade_dependency_blocked` acts only when `st in TERMINAL_STATES and st not in required`, so a non-terminal prerequisite is already left alone.
- Drain arm (`oc_runipd.run_queue`, `runnable is None`): `classify_drain_block` returns TRANSIENT for a non-terminal prerequisite and `record_transient_dependency_wait` leaves the item `queued` with `TRANSIENT_DEPENDENCY_WAIT_HINT`; agy has the same arm.
- `aggregated_run_items` clause 6 makes a `queued` item under `stopped=False` a `CONTRIBUTION_FAILURE`; `run_evidence._CLASSIFICATION_PRIORITY` ranks `AGGREGATE_NEEDS_INPUT` above `AGGREGATE_ITEM_FAILURE`.
- Reviews share one sweep lane (`acquire_review_sweep_lane`, `deferred_review_lane_handle` "there is exactly ONE sweep lane per run"); `attempt["review_lane_tip_before"]` is recorded before each review turn; the review branch of `execute_item_core` calls `commit_review_lane_output` and then `integrate_review_lane_branch` unless the disposition is `fail-gate`.
- `lane_containment.record_lane_preserved` writes the `preserved_*` fields through `record_preserved_lane_state`; `RETENTION_*` codes exist, none for awaiting-human.
- Spec `6kwd2e` R3.1-R3.6, R6.1, R7.3, A3-A8, A13, A15, A32, A38, A39 read as cited.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | Correctness / domain invariant (R3.3) | `runner_shared.deferred_review_lane_handle` docstring "there is exactly ONE sweep lane per run"; `execute_item_core` review branch `integrate_review_lane_branch(repo, _handle, _item["id6"])` | E-02 applied per-item lane preservation "to execute and review turns alike". A review has no per-item lane: preserving the sweep lane would stall every later review, and leaving the parked review's commits on it would merge them to main with the next review's integration, breaking R3.3 ("a parked item's work can never merge to main"). | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-02 limited to execute. New E-06: commit own paths, branch `aw/parked/<run_id>/<id6>`, reset the sweep lane to `review_lane_tip_before`, record `preserved_*`, refuse to park if the tip is not a descendant. Demonstrated (D-2). `j0ufrj` E-03 now restores from that branch. V-06 demands the git evidence. |
| PR-002 | HIGH | IN-SCOPE | Correctness (exit code, R7.3/A8/A38) | `runner_shared.aggregated_run_items` clause 6 "Everything else contributes plain failure" for `queued` under `stopped=False` | After the drain leaves a parked item's dependents `queued` (TRANSIENT), they aggregate as failures; exit 3 would only win via the parked item's `needs_input`, and the dependents' rendered hint says "resume the run", not "answer". E-04 named no mechanism. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 now names the path: `waits_on_awaiting_human` predicate, parked-specific hint, `benign_skip` for such dependents, `needs_input` for parked items, a summary line; tested with an extra independent `fail-gate` still exiting 3. |
| PR-003 | MEDIUM | IN-SCOPE | Correctness (park placement) | plan E-02 "after the outcome is read and BEFORE the proposal branch"; spec R2.2 `gates_verdict` | The park did not say it must precede verification, finalize and integration, nor what a non-gating question does; parking every question would hold back work the worker said was not gated. | all Low | FIXED | E-02 parks only on `gates_verdict: true`, before verify/finalize/integration/teardown; non-gating questions are recorded and scored as today; tested. |
| PR-004 | MEDIUM | IN-SCOPE | Accuracy / E-03 vs spec A7 | `cascade_dependency_blocked` `if st in TERMINAL_STATES and st not in required`; spec A7 "a reason naming the upstream question" | E-03 described a change the cascade already does by construction, and named no field carrying the upstream question. | all Low | FIXED | E-03 now pins existing behavior in a test and adds `awaiting_upstream` with question texts, transitively (A-C-D fixture). |
| PR-005 | MEDIUM | UNDER-SCOPE | Completeness of status vocabulary | `runner_shared.map_driver_status_to_run_state` table (no `awaiting-human`); `lifecycle_style` `("awaiting-human", WAITING_INPUT)` | A new status absent from the run-state map is reported `ST-UNMAPPED-SOURCE`; E-01 also asked to add a glyph that already exists. Resume (`requeue_interrupted`) must not re-queue it. | all Low | FIXED | E-01 adds the map entry, confirms the existing style, and asserts resume leaves it parked; V-01 updated. |
| PR-006 | LOW | IN-SCOPE | Traceability | orchestrator Cross-IPD map "A15 (host parity) is asserted on both hosts by `epsti7`"; plan E-05 omitted A15; spec A38 names "the answer file path" | E-05 did not list A15, and A38's answer-file path belongs to Order 08's `answers.md`. | all Low | FIXED | E-05 lists A15 with a parity assertion and states A38's path is asserted by `jshwxb`; Deferred section names it. |

`aw ipd sync --apply` assigned E-06/V-06. `aw ipd lint --phase review-finalize --agent`: `clean` (one info, `IPD-Z602` on E-06's numbered sub-steps; kept as one item because the five steps are one atomic park transaction and splitting them would leave a half-parked lane between items). Sibling `j0ufrj` (to-review) E-03 edited; author-phase lint `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should a non-gating question park the item? | No; record it, score as today. | Park on any question (REJECTED: holds work the worker said is not gated). | spec R2.2 "whether it gates the verdict"; `0jooqz` E-01 `gates_verdict`. | yes |
| D-2 | How to park a review on the shared sweep lane? | Move its commits to `aw/parked/<run_id>/<id6>`, reset the sweep lane to `review_lane_tip_before`. | Preserve the sweep lane (REJECTED: stalls all later reviews); leave commits (REJECTED: next integration merges them); per-review lanes (REJECTED: reverses `ajxr5d` OQ-02's one-lane ruling). | DEMONSTRATED in a scratch repo in this lane (`.aw/state/parkdemo`, removed after): sweep clean after park; parked branch held `review3 partial` + `review3 leftover (driver)`; a later `--no-ff` merge brought `review2 deferred` and `review4` to main; "OK: parked work absent from main". | yes |
| D-3 | How do dependents of a parked item affect the exit code? | `benign_skip` when they wait only on parked items. | Leave as failure (REJECTED: misreports R7.3); give dependents their own parked status (REJECTED by OQ-01). | `aggregated_run_items` clauses; `_CLASSIFICATION_PRIORITY`. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
