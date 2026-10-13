- Id: no88yi
- Status: done
- Graduated-To: no88yi
- Blocks-Release: next
- Set: no88yi
- Priority: low
- Work-Kind: bug
- Summary: aw find --limit inert in human mode

## Workflow history
- 2026-10-13 done (aw backlog): closed by aw agy run: IPD i00j2o executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261012-no88yi-01-i00j2o-make-aw-find-limit-bound-the-human-row-listing-and-say-how-m.ipd.md); evidence .aw/records/plans/executed/20261012-no88yi-01-i00j2o-make-aw-find-limit-bound-the-human-row-listing-and-say-how-m.ipd.md
- 2026-10-12 graduated (aw backlog): graduated by run run-20261012T005617Z-2321742: i00j2o
- 2026-10-07 created (aw backlog): aw find --limit inert in human mode

aw find accepts --limit (registered in the shared noun-verb loop), but in human output mode it is silently ignored and prints all matched rows without truncation. Measured at aw find plans --limit 3, which printed all 1329 plans. IPD okiso1 scoped and implemented --limit for the --agent stream only. Handed off from moegsl deferred row 3 / F-04.
