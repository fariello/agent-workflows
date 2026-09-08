- Id: yf9fj9
- Status: done
- Set: depreview
- Priority: high
- Work-Kind: bug
- Summary: the review relaxation on an executed: dependency is unreachable because it compares a directory name against states that have no directory

## Workflow history
- 2026-09-08 done (aw set): Closed by plan 03ie04, now executed at bc9b3f43 (lane merged in bf57a569). The review relaxation reads the - Status: field instead of the directory; verified by re-running the four items that were dependency-blocked in run-20260908T024107Z (51vw4y, ybkmzp, rl67b0, 3v7wo6), all of which now dispatch as queued. Suite on main: 1 failed, 5683 passed, the single failure pre-existing and unrelated (test_plan_readiness, live plan 32ij2j).
- 2026-09-07 graduated (aw set): Graduated to plan 03ie04 (depreview-01): read the dependency target's Status field instead of its directory so the existing review relaxation becomes reachable.
- 2026-09-06 created (aw backlog): the review relaxation on an executed: dependency is unreachable because it compares a directory name against states that have no directory

/tmp/opencode/dep1.md
