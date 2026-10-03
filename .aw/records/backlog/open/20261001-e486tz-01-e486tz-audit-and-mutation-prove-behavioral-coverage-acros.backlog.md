- Id: e486tz
- Status: open
- Set: e486tz
- Priority: low
- Work-Kind: chore
- Summary: Audit and mutation-prove behavioral coverage across the 207 trim-deleted test files uncited in comments

## Workflow history
- 2026-10-01 created (aw backlog): Audit and mutation-prove behavioral coverage across the 207 trim-deleted test files uncited in comments

Commit 19313eed deleted 298 test files, of which 91 are cited in live comments/docs and 207 are cited nowhere (holding 3,554 removed test functions, or 59.3% of the removed population). The lost_guard_census scanner reaches only the cited sample (40.7%). This item tracks auditing the remaining 207 uncited deleted files to derive asserted properties and mutation-prove surviving coverage.
