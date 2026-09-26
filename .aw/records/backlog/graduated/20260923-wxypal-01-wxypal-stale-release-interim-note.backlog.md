- Id: wxypal
- Status: graduated
- Graduated-To: staledocs
- Set: wxypal
- Priority: low
- Work-Kind: chore
- Summary: Delete the 2.0.0 release record's stale 'IPD sets that cannot yet carry the field' interim note: both blockers it waits on are done and all four named Sets have executed

## Workflow history
- 2026-09-26 graduated (aw set): Graduated 2026-09-26 into to-review plan Set staledocs (commit 2c7068ca).
- 2026-09-23 created (aw backlog): Found while executing 40it5e (rununify 12) E-04, which was required to report the note rather than edit it (the release record is not in that plan's Scope-Paths). The note states its own deletion condition: 'Once vwios6 lands, migrate this intent to the per-item Blocks-Release field on those IPDs and delete this interim note.' Measured: backlog vwios6 is done and backlog w6mqc0 is done, so both blockers it cites are cleared, and Blocks-Release is now a recognized optional IPD field (ipd_schema.META_BLOCKS_RELEASE) which 40it5e itself carries. The four Sets the note names as intended release blockers (execset, ipdgates, proclint, unifyfileio) have all executed, so there is no longer any intent to migrate either. The note is therefore doubly stale: its stated precondition is met and its subject is gone. Harm is that it documents a TEMPORARY EXCEPTION to the record's own no-prose-list rule that no longer applies, so a reader is told the per-item field cannot be set on a plan, which is false.
