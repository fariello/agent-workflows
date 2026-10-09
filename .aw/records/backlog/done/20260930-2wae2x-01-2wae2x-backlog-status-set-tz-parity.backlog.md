- Id: 2wae2x
- Status: done
- Close-Evidence: .aw/records/plans/executed/20261001-7qvs1c-01-5ivkdh-unify-every-artifact-history-date-onto-the-utc-clock-ruled-b.ipd.md
- Blocks-Release: next
- Set: 2wae2x
- Priority: medium
- Work-Kind: bug
- Summary: Fix timezone discrepancy between backlog.run_set and status_set dates in workflow history

## Workflow history
- 2026-10-09 done (aw set): Satisfied: unified history dates onto UTC clock shipped in executed plan 5ivkdh
- 2026-09-30 created (aw backlog): Fix timezone discrepancy between backlog.run_set and status_set dates in workflow history

backlog.run_set formats history dates using local date (datetime.date.today()) while status_set uses UTC (datetime.datetime.now(timezone.utc)). Across timezone boundaries (e.g. UTC midnight), this produces divergent dates and breaks test_release_exempt_setter_roundtrip_and_parity.
