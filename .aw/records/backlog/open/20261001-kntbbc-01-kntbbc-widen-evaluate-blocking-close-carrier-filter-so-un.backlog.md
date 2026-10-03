- Id: kntbbc
- Status: open
- Set: kntbbc
- Priority: low
- Work-Kind: chore
- Summary: Widen evaluate_blocking_close carrier filter so ungated sibling carriers block close

## Workflow history
- 2026-10-01 created (aw backlog): Widen evaluate_blocking_close carrier filter so ungated sibling carriers block close

2o5wka OQ-02: evaluate_blocking_close filters by same gate while runner_shared.evaluate_backlog_close filters by kind (IPD), so an ungated sibling carrier is dropped by evaluate_blocking_close. Deferred in 2o5wka OQ-02 and jf3j4q deferred row 3.
