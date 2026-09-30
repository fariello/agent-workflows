- Id: 64a03w
- Status: open
- Set: runviewdisc
- Priority: low
- Work-Kind: followup
- Summary: Decide whether substantially-complete should share complete's audit tolerance, or stay asymmetric

## Workflow history
- 2026-09-30 created (aw backlog): Filed from IPD p5yaqw (F-07) as the durable carrier for its deferred substantially-complete row.

Measured at HEAD 928be376 while authoring IPD `p5yaqw` (its F-07).

`runner_shared.canonical_terminal_status('substantially-complete')` returns `fail-gate`, NOT `complete`. So in `artifact_audit._status_disagrees`:

```text
_status_disagrees('substantially-complete', 'executed')  ->  True   (flagged)
_status_disagrees('complete',               'executed')  ->  False  (tolerated)
```

An item recorded `substantially-complete` whose plan legitimately reached `executed/` reading `- Status: executed` is therefore reported as a discrepancy, while a `complete` item in the identical shape is not.

WHETHER THAT IS A DEFECT IS GENUINELY UNDECIDED, which is why this is a followup and not a bug. `substantially-complete` is NOT in `runner_shared.SUCCESS_STATES` (`['approved','executed','reviewed']`) nor in `artifact_audit._RUN_SUCCESS_STATUSES` (`frozenset({'executed'})`), so refusing it the success arm's tolerance may be exactly right: the run did not assert success. Deciding needs a measurement nobody has made, namely whether that status ever accompanies a legitimate forward finalization in practice, or whether it always means the work stopped short.

DO NOT FIX THIS BY ADDING THE STATUS TO A TOLERANCE LIST WITHOUT THAT MEASUREMENT. Tolerating it requires admitting `executed` among the accepted declared values for its arm, which every plan in this area has explicitly refused as suppressing the one row that most needs an operator's eyes (see `vdabn5`'s docstring reasoning and `p5yaqw` OQ-02).

PRIOR ART: `vdabn5` F-4 deferred this once already, but its measurement is now STALE: it recorded `substantially-complete` as normalizing to `complete` and therefore flagging on BOTH axes. At HEAD it normalizes to `fail-gate` and `expected_dir_for_status` returns `pending`, so only the status axis flags. Re-measure before acting.
