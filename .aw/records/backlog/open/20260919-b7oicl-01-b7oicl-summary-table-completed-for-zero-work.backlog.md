- Id: b7oicl
- Status: open
- Blocks-Release: next
- Set: b7oicl
- Priority: medium
- Work-Kind: bug
- Summary: The exit summary table reads COMPLETED at 100% for a run that performed zero work

## Workflow history
- 2026-09-19 created (aw backlog): Found while executing runnoop Order 03 (bsc457); OQ-02 directed reporting over a cross-fence edit.

Measured 2026-09-19 while executing runnoop Order 03 (`bsc457`). Rendering the real
`render_stream.render_run_summary_table` with ONE `reviewed`/zero-attempt item yields:

    Outcome: COMPLETED   Duration: 0s   Spend: $0.00
    Progress: 1/1  [##########] 100% (1 reviewed)

for a run that dispatched NOTHING. The verdict comes from a status tuple containing `reviewed`, and
no diagnostic line is emitted because the diagnostics block keys on a five-status allowlist that
`reviewed` is not a member of.

`bsc457` now prints a closing DISPOSITION SUMMARY that states the honest answer
('NO WORK WAS PERFORMED: this run matched N artifact(s) and acted on NONE of them'), so the two
surfaces VISIBLY DISAGREE on the same screen: the table says COMPLETED at 100%, the summary below it
says nothing was done. The summary is the correct one.

REPORTED RATHER THAN FIXED, deliberately and per `bsc457`'s OQ-02 resolution: that expression lives
in `render_stream.py`, which `bsc457`'s scope fence forbids editing, and the function belongs to
`orchprobe` `r2i1b1` (now `- Status: executed`). OQ-02 directed that a visible disagreement be
reported as a finding naming that owner rather than quietly reconciled across the fence.

FIX: decide what `Outcome:` should say for a run whose queue is entirely never-dispatched. The
disposition vocabulary to key on already exists as
`run_selection_policy.derive_item_disposition`/`summarize_dispositions`, so the table can consume
the same judgement the summary uses rather than re-deriving a verdict from queue statuses.
