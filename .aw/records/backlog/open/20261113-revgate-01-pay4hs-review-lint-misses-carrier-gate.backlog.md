- Id: pay4hs
- Status: open
- Blocks-Release: next
- Set: revgate
- Priority: high
- Work-Kind: bug
- Summary: plan-review's own lint (--phase review-finalize) passes an uncarried open question that the review-lane integration gate then refuses, so the review is wasted as fail-merge

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-14 created (aw backlog): plan-review's own lint (--phase review-finalize) passes an uncarried open question that the review-lane integration gate then refuses, so the review is wasted as fail-merge

## Observed

run-20261114T011656Z-594596: reviews of 1vfqdu (OQ-08) and ya4ee4 (OQ-05) each left a non-blocking question `open` with no `- Carrier:`. `runner_shared.check_review_lane_artifacts` refused integration with check.ipd-uncarried-obligation (cause artifact-conformance), which `classify_integration_refusal` treats as terminal on the first attempt.

## Cause

The reviewer's self-check cannot see the rule. `ipd_lint._CARRIER_CHECKPOINTS = frozenset(("pre-transition",))`, so `aw ipd lint --phase review-finalize` (the command plan-review.md:88 tells the reviewer to run) skips `_merge_durable_carrier`. Measured on the pre-fix 1vfqdu plan: the review-finalize lint reported clean (`outcome: clean, findings: 0`), while the gate refused the same file.

## Fix direction

1. Make the reviewer's check match the gate: either add `review-finalize` to `_CARRIER_CHECKPOINTS`, or have the review turn run the same `check_review_lane_artifacts` predicate before it commits. Measure corpus impact first; a whole-corpus probe did not finish within 10 minutes.
2. Make an artifact-conformance refusal on a review turn earn ONE bounded correction turn carrying the gate's text (the execute path already does this for finalize refusals), instead of going terminal.
3. Add a line to plan-review step s5-questions.md: an open or deferred question needs `- Carrier: <id6>`, `- Carrier-Evidence:`, or `- Carrier-Declined:` (file one with `aw backlog new`).

## Remediated instance

a6s7na was filed as the carrier, and the three reviews landed on main (0081e86e3, 41c20de58).
