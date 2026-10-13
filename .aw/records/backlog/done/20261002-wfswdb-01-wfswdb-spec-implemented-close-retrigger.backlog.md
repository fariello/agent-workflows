- Id: wfswdb
- Status: done
- Graduated-To: wfswdb
- Set: wfswdb
- Priority: low
- Work-Kind: followup
- Summary: After a mixed plan+spec backlog item's close is refused because its spec carrier is unimplemented, nothing re-evaluates the close when the spec later reaches implemented, so the item stays graduated until a hand close

## Workflow history
- 2026-10-13 done (aw backlog): closed by aw agy run: IPD isnqja executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261012-wfswdb-01-isnqja-surface-a-graduated-backlog-item-that-becomes-closable-when.ipd.md); evidence .aw/records/plans/executed/20261012-wfswdb-01-isnqja-surface-a-graduated-backlog-item-that-becomes-closable-when.ipd.md
- 2026-10-12 graduated (aw backlog): graduated by run run-20261012T005606Z-2321569: isnqja
- 2026-10-02 created (aw backlog): After a mixed plan+spec backlog item's close is refused because its spec carrier is unimplemented, nothing re-evaluates the close when the spec later reaches implemented, so the item stays graduated until a hand close

Surfaced by plan-review of 5eygjt (10w6ww), finding F-10, 2026-10-02. runner_shared.process_backlog_close runs only when a PLAN carrier executes; aw specs set ... implemented does not re-evaluate any From-Backlog item. Once 5eygjt makes the outer predicate refuse a mixed item whose spec is not implemented, such an item can only close by hand (HANDOFF, --evidence, or de-gate). Decide whether aw specs set implemented should re-evaluate (and offer or perform) the item close, or whether the attention view should surface a graduated item whose carriers are all terminal. Not a correctness defect: the refusal is recorded (backlog-item-left-open event, render_unclosed_report) and matches the inner gate.
