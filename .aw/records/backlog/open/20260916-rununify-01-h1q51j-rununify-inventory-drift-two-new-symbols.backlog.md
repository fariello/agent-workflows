- Id: h1q51j
- Status: open
- Set: rununify
- Priority: medium
- Work-Kind: followup
- Summary: Two runner symbols became newly double-defined after the rununify inventory was measured (collect_lane_earned_paths, integrate_review_lane_branch), so the Set's 66-symbol accounting no longer covers HEAD

## Workflow history
- 2026-09-16 created (aw backlog): Filed by rununify 03 (i3d6ml) execution 2026-09-17 as a defect-report finding.

MEASURED AT i3d6ml's EXECUTION HEAD e93ba3de, by the closure method that plan's E-01 prescribes, and reported because E-01's own acceptance criterion demands that any drift be stated BY NAME.

THE NUMBERS. Plan i3d6ml partitioned 66 double-defined symbols: 48 carrying no behavioral disagreement (its groups A through H) plus 18 deferred to children 04 through 11. At execution HEAD the count is 68. The two additions are in NEITHER partition:

  collect_lane_earned_paths      12 oc lines, bodies AGREE, closes over `runner_shared`
  integrate_review_lane_branch   25 oc lines, bodies DIFFER, closes over `runner_shared`

WHY THIS IS NOT URGENT, stated so nobody over-reacts to it. Both close over `runner_shared` ONLY, which is the group-C signature: the real implementation already lives once in the shared module and each runner keeps a binding wrapper. runner_shared defines both (`collect_lane_earned_paths` at its 'native shared run_checked callers' seam, `integrate_review_lane_branch` beside `integrate_lane_branch`). So neither is genuine duplication and neither changes i3d6ml's liftable set; i3d6ml reported them and lifted neither, which is correct.

WHY IT STILL MATTERS. The Set is governed by a fixed inventory, and the drift is DIRECTIONAL: symbols keep being ADDED to both runners while the Set that exists to de-duplicate them waits. The parent plan 5e4sb6's own F5 already records this ('every day this Set waits, the duplication GROWS by design'), and this is a measured instance of it, two symbols in the roughly two weeks since the 2026-09-16 re-measurement. Two consequences worth a decision:

  1. Any child that asserts on a TOTAL (a symbol count, an import count, a 'these are all of them' table) will drift out of date between authoring and execution. i3d6ml's own E-05 avoided this by driving its test from a NAMED TABLE rather than from the count, which is the pattern the remaining children should follow.
  2. The orchestrator's completion criterion is 'one code base containing 100% of the otherwise redundant code' (maintainer directive 2026-09-16). A moving inventory means that target must be RE-MEASURED at the end rather than checked against the 2026-09-03 or 2026-09-16 lists, both of which are now stale.

SUGGESTED WORK. Either (a) add a cheap guard that FAILS when a new top-level symbol becomes double-defined in the two runners, so the drift is visible at the moment it happens rather than at the next audit, or (b) accept the drift explicitly and require every remaining rununify child to re-measure at execution HEAD (which i3d6ml's E-01 already does, and which is why this was caught at all).
