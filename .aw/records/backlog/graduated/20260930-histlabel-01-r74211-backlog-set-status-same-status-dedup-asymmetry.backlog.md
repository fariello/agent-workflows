- Id: r74211
- Status: graduated
- Graduated-To: histdedup
- Set: histlabel
- Priority: low
- Work-Kind: chore
- Summary: aw backlog set --status appends a duplicate same-status history record; the positional spelling deduplicates it

## Workflow history
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T221834Z-1991716: evbx9s
- 2026-09-30 created (aw backlog): Measured while authoring plan jbipfa from backlog awqzuh; the sibling defect of awqzuh's label asymmetry, on the same two code paths.

Measured 2026-09-30 at HEAD `4b7f2582` while authoring plan `jbipfa` from backlog `awqzuh`, by driving each spelling TWICE over identical fixtures in temporary repositories.

THE OBSERVATION. Two identical same-status calls produce a different number of records depending on which spelling was used:

    aw backlog set <path> --status open --message "metadata only"   (twice)  ->  TWO identical records
    aw backlog set open <id6> --message "metadata only"             (twice)  ->  ONE record

Measured output of the `--status` spelling after the second call:

    ## Workflow history
    - 2026-09-30 set (aw backlog): metadata only
    - 2026-09-30 set (aw backlog): metadata only
    - 2026-09-01 created (tester): initial

Measured output of the positional spelling after the second call:

    ## Workflow history
    - 2026-09-30 same-status (aw set): metadata only
    - 2026-09-01 created (tester): initial

WHY. `status_set.apply_status_change` consults `same_status_message_is_duplicate` before writing, and that
predicate exists precisely for this: its docstring records the measured three-identical-records run (plan
`1i300e` E-03, finding F-9) that motivated it, and explains that it deliberately compares only the NEWEST
record and deliberately ignores the actor. `backlog.run_set` consults nothing: it calls
`backlog._reattach_history` unconditionally, so every same-status call appends another record.

THE PREDICATE ALREADY EXISTS AND IS ALREADY SHARED. `specs.run_set` imports
`status_set.same_status_message_is_duplicate` directly, so `backlog.run_set` calling it would be the THIRD
consumer of one definition rather than a new mechanism. That is what makes this a small fix in principle.

WHY IT WAS NOT FIXED IN `jbipfa`, which is the plan that measured it. That plan changes what a record SAYS
(the label token). This changes whether a record is WRITTEN AT ALL, which is a different blast radius and
deserves its own review: a dedup predicate wired into a path that never had one can silently swallow a
record a user expected, and the failure is invisible (nothing is written, nothing warns). `jbipfa` fenced it
out and filed it here instead of widening its own scope.

RELATION TO `awqzuh`. Same two code paths, same root cause shape (the `--status` spelling reimplements
part of what the positional spelling does, and does less), but an independent defect: fixing the label does
not fix the dedup, and fixing the dedup does not fix the label. `awqzuh` is the label half.

SUGGESTED FIX, with its risk. Have `backlog.run_set` consult `status_set.same_status_message_is_duplicate`
before calling `_reattach_history`, skipping the history write (but NOT the metadata write or the file move)
when the record would merely repeat the newest one. THE RISK: `run_set` also writes the sidecar
(`record_history.append_advisory`) unconditionally, so a skipped inline record must not silently skip or
silently keep the sidecar line without a decision being made about it. Also note `apply_status_change`
has a `_write_history_anyway` branch (an explicit `--message` or an untooled transition) that a naive port
would lose. Whoever takes this should drive BOTH spellings twice in a test and compare the whole file.
