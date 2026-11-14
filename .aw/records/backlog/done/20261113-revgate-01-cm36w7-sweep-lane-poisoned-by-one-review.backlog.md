- Id: cm36w7
- Status: done
- Close-Evidence: .aw/records/walkthroughs/20261114-revgate-01-pay4hs-review-gate-fixes.walkthrough.md
- Blocks-Release: next
- Set: revgate
- Priority: high
- Work-Kind: bug
- Summary: One refused review poisons the shared review-sweep lane: every later review in that run fails fail-merge with the first review's reason

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-14 done (aw set): status set to done
- 2026-11-14 created (aw backlog): One refused review poisons the shared review-sweep lane: every later review in that run fails fail-merge with the first review's reason

## Observed

run-20261114T011656Z-594596: n5sxxk's own plan passed the gate (`check_review_lane_artifacts` returned OK for it alone), but its integration was refused with 1vfqdu's OQ-08 message. ya4ee4 then failed the same way. All three lived on aw/lane/review-sweep-run-20261114T011656Z-594596.

## Cause

Every review in a run shares one sweep lane (`acquire_review_sweep_lane`). The integration gate checks every file the lane changed against main, so after 1vfqdu's refused commit stays on the lane, each later integration re-checks that same bad file and refuses. The lane also can no longer refresh (`refresh_sweep_lane` is ff-only, and the lane has diverged), so later reviews read a stale main.

## Fix direction

When a review's integration is refused, isolate that review's commit (park it on its own preserved branch) and reset or re-cut the sweep lane to main before the next review starts. That way one bad review costs one item, not the rest of the run. Alternatively, have the gate scope its check to the files the current review changed.
