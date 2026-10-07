- Id: 10w6ww
- Status: done
- Graduated-To: 10w6ww
- Blocks-Release: next
- Set: 10w6ww
- Priority: medium
- Work-Kind: bug
- Summary: Outer backlog close predicate ignores spec carriers when IPD carrier exists

## Workflow history
- 2026-10-07 done (aw backlog): closed by aw agy run: IPD 5eygjt executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261002-10w6ww-01-5eygjt-make-the-outer-backlog-close-predicate-judge-spec-carriers-i.ipd.md); evidence .aw/records/plans/executed/20261002-10w6ww-01-5eygjt-make-the-outer-backlog-close-predicate-judge-spec-carriers-i.ipd.md
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T221821Z-1985969: 5eygjt
- 2026-10-01 created (aw backlog): Outer backlog close predicate ignores spec carriers when IPD carrier exists

F-09: runner_shared.evaluate_backlog_close ignores spec carriers entirely when any IPD carrier exists, because 'if ipds:' returns before 'others' is examined. An item with an executed IPD carrier plus an approved spec carrier returns close=True from the outer predicate; the outer evidence citation fires SATISFIED in the inner gate and masks the unexecuted spec carrier.
