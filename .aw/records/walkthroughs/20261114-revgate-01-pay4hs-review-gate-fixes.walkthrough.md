# Walkthrough: review-lane gate fixes (pay4hs, cm36w7)

- Date: 2026-11-14
- Set: revgate
- Commits: eba40955c (fixes), 13d3c03a8 (related runner output wording)

## pay4hs

`ipd_lint._CARRIER_CHECKPOINTS` now includes `review-finalize`, so a reviewer's
`aw ipd lint --phase review-finalize` reports `check.ipd-uncarried-obligation`, the same rule
`runner_shared.check_review_lane_artifacts` refuses a review merge on. Measured before widening:
0 of 209 pending plans fail at review-finalize. `plan-review/steps/s5-questions.md` tells the
reviewer to carry every open or deferred question.

Test: `tests/test_durable_carrier_shared_predicate.py::test_review_finalize_reports_what_the_review_merge_gate_refuses`
fails without the change and passes with it.

## cm36w7

On a TERMINAL review integration refusal, `runner_shared.park_refused_review_off_sweep_lane`
moves the review's commits to `aw/parked/<run_id>/<id6>` and resets the shared sweep lane to the
attempt's `review_lane_tip_before`. A deferred refusal stays on the lane for the ladder to retry.

Test: `tests/test_review_sweep_lane_refusal_isolation.py` (both hosts, real git): the refused
review is parked, the lane is reset and clean, and the next review integrates to main without the
refused commit. It fails without the change and passes with it.

## Validation

Core suite on main after merge:

```
2085 passed, 11 warnings in 49.75s
```
