- Id: 1f9m2j
- Status: blocked
- Set: runviewdisc
- Priority: medium
- Work-Kind: bug
- Summary: the aw runs discrepancy table reports resolved-since-the-run items as defects, because it compares a frozen historical record against present-day truth
- Gate-Kind: artifact
- Gate-Ref: rnl3b7

## Workflow history
- 2026-09-05 set (aw backlog): BLOCKED on rnl3b7 after a design attempt was ABANDONED as unsound (2026-09-05, maintainer ruling: do not fix this if the fix must fabricate an OK the data does not support). THE FLAW: the proposed classifier would have inferred 'resolved' from lifecycle DIRECTION alone (run says integration-blocked, artifact says executed in executed/ -> benign). That inference is not grounded in anything run_viewer can observe. Verified it reads exactly two things: actual_file.parent.name (run_viewer.py:438) and a '- Status:' regex (:444-445), with ZERO references to finalize journals, receipts, git history, or commits anywhere in the module (grep count 0). So a legitimately finalized-and-integrated plan and a hand-edited '- Status: executed' plus git mv are BYTE-IDENTICAL to the audit. Classifying the pair as 'resolved' would print a green OK for the exact bypass the ipd-executed-transition-gate hook exists to catch, which is strictly worse than the current false positives. Note the direct irony: rnl3b7 criticizes that hook for being unable to distinguish a legitimate merge from a hand-edit, and this fix would have made the same undecidable call and answered it optimistically. WHAT A GROUNDED FIX NEEDS (any one): the in-tree 'lifecycle(<id6>): finalize' commit read from git history; or the finalize transaction journal, which is gitignored and therefore unavailable across trees (the same blocker rnl3b7 names); or a durable in-record note that integration happened after the run. Until the viewer can READ such evidence, 'resolved' is a guess and the four rows should stay as-is: noisy but TRUTHFUL, since the run record and disk genuinely do differ and the viewer cannot say why. The scaffolded plan l6ukz1 was deleted rather than left as a misleading pending artifact.

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
