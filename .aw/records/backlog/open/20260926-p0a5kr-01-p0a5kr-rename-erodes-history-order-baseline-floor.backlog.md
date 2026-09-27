- Id: p0a5kr
- Status: open
- Blocks-Release: next
- Set: p0a5kr
- Priority: low
- Work-Kind: bug
- Summary: aw rename of a terminal plan silently erodes test_history_order's 700-path floor because the frozen baseline keys paths and is never rewritten

## Workflow history
- 2026-09-26 created (aw backlog): aw rename of a terminal plan silently erodes test_history_order's 700-path floor because the frozen baseline keys paths and is never rewritten

FOUND 2026-09-26 during /plan-review of plan 5xzld0 (renamescan Order 01), which correctly excludes .json from the widened reference-scan suffixes (its F-6) so that tests/fixtures/derive_plan_status_baseline.json is never rewritten by a rename. That exclusion is necessary but NOT sufficient, and the reasoning stops one step short.

MEASURED AT REVIEW. tests/test_history_order.py::DerivationIsUnchangedTests loads the 777-key baseline, builds the live terminal-plan path list (executed/ + superseded/ + not-executed/), intersects the two, and asserts assertGreaterEqual(len(intersection), 700). The current intersection is 732, so the margin above the floor is 32.

THE COUPLING. The baseline keys repo-relative PATHS of terminal plans. Because it is deliberately not rewritten by a rename, every 'aw rename plans' or 'aw group plans --rename' of a plan in a terminal directory removes one key from the intersection. About 33 such renames breach the floor and redden a test that has nothing to do with renaming, with a failure message ('expected at least 700 paths in common') that points a reader at derive_plan_status rather than at the renames that actually caused it.

WHY IT MATTERS NOW. This coupling predates plan 5xzld0 and that plan does not create it. But 5xzld0 makes renaming routine and safe enough to do often, so it is the change that makes the erosion likely to be reached in practice.

FIX DIRECTION (not decided). Options, in rough order of preference: (a) key the baseline by plan id6 rather than by path, so a rename is invisible to it; (b) have the test compute its floor as a FRACTION of the live terminal population instead of a frozen absolute; (c) regenerate the baseline as part of the rename tooling. (a) is the most durable because id6 is the repo's stable cross-tree handle and survives a rename by construction, which is the same argument the reviews-record naming convention already makes. Whichever is chosen, the failure message should name the real cause.

BLOCKS-RELEASE: carries the gate because it is a bug whose symptom is a red suite on an unrelated change (a live artifact a maintainer waits on and then misdiagnoses).
