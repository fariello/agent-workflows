- Id: 1f9m2j
- Status: open
- Set: runviewdisc
- Priority: medium
- Work-Kind: bug
- Summary: the aw runs discrepancy table reports resolved-since-the-run items as defects, because it compares a frozen historical record against present-day truth

## Workflow history
- 2026-09-05 created (aw backlog): the aw runs discrepancy table reports resolved-since-the-run items as defects, because it compares a frozen historical record against present-day truth

THE DEFECT. `run_viewer.render` (the "Artifact & Status Discrepancies" table, title at
`agent_workflows/run_viewer.py:1346`) compares each queue item's FROZEN run-record status against
the artifact's PRESENT-DAY location and status, and labels every difference a discrepancy in red. But
a run record is immutable history: it is gitignored box-local state (`.aw/.gitignore:14`,
`records/runs/`) whose statuses were true at the moment the run ended. Reality legitimately moves on
afterward, and when it does the table reports the CORRECT new state as a defect.

MEASURED. After the four lanes stranded by `run-20260905T050043Z-639569` were recovered and merged
on 2026-09-05, the table showed:

    20260904-revsweep-01-76gsmv    pending/ vs executed/   integration-blocked vs executed
    20260904-revsweep-03-eyh1fu    pending/ vs executed/   integration-blocked vs executed
    20260831-resumedupe-01-txc9l1  pending/ vs executed/   integration-blocked vs executed
    20260903-runflags-01-uyeko5    pending/ vs executed/   integration-blocked vs executed

All four rows are FALSE ALARMS. The run record correctly says those items were
`integration-blocked` at 11:47Z; the artifacts correctly say `executed` now, because they were
integrated afterward. Nothing is wrong, yet the table demands attention for four items and gives the
operator no way to tell these apart from a genuine mismatch. Editing EITHER side to silence it would
falsify a record.

WHY THIS IS WORTH FIXING RATHER THAN LEARNING TO IGNORE. The same table DID surface a real problem in
the same output: `eulhzt` showed main's plan copy at 5/8 E-items while its lane copy was finalized
at 8/8, which is how a fifth stranded lane was found and recovered. So the table has real diagnostic
value, and false rows directly erode it. A four-row false-positive block trains an operator to skim
past exactly the rows that matter.

THE FIX. Distinguish PROGRESS from MISMATCH. A row where the artifact has advanced along the
legitimate lifecycle since the run ended (for example run-status `integration-blocked` /
`substantially-complete` / `interrupted` -> artifact `executed` in `executed/`) is RESOLVED
SINCE THE RUN, not a discrepancy: report it in a non-alarming style, or in a separate section, or
suppress it behind a flag. Reserve the red discrepancy styling for a difference that indicates
something actually wrong, e.g. the run recorded `executed` but the artifact is NOT in
`executed/` (evidence the finalize did not stick), or the artifact is missing entirely.

Suggested shape: classify each row as `resolved` / `regressed` / `missing` / `unchanged`
rather than the current boolean `location_mismatch` / `status_mismatch`
(`run_viewer.py:1300-1343`). The lifecycle direction is already knowable from the status vocabulary,
so this needs no new data, only a comparison that knows which way is forward.

DO NOT fix this by mutating run records to match current reality. The record's value IS that it
freezes what was true, and a run's own state file is the evidence base for resume, reconciliation, and
cost accounting.

ALSO WORTH CHECKING while in here: the `i6015i` row in the same table read
`interrupted` vs `approved` and was ALSO not a defect, but for a third reason - the item was
interrupted mid-turn having performed 0 of 10 E-items, so `approved` is the honest current status and
there is nothing to reconcile. A useful classifier should place that row in a different bucket again
("never completed; re-run needed") rather than lumping it with either the false-positive or the
genuine-mismatch cases.
