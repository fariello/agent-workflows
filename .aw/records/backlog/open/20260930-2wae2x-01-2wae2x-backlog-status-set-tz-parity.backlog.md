- Id: 2wae2x
- Status: open
- Blocks-Release: next
- Set: 2wae2x
- Priority: medium
- Work-Kind: bug
- Summary: Fix timezone discrepancy between backlog.run_set and status_set dates in workflow history

## Workflow history
- 2026-09-30 created (aw backlog): Fix timezone discrepancy between backlog.run_set and status_set dates in workflow history

backlog.run_set formats history dates using local date (datetime.date.today()) while status_set uses UTC (datetime.datetime.now(timezone.utc)). Across timezone boundaries (e.g. UTC midnight), this produces divergent dates and breaks test_release_exempt_setter_roundtrip_and_parity.
