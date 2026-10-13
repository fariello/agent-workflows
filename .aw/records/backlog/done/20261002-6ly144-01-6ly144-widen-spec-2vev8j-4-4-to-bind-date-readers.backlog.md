- Id: 6ly144
- Status: done
- Graduated-To: 6ly144
- Set: 6ly144
- Priority: low
- Work-Kind: followup
- Summary: Decide whether spec 2vev8j Section 4.4 should bind date READERS, not only writers, by stating that a stored value and the today it is compared against must share a clock

## Workflow history
- 2026-10-13 done (aw backlog): closed by aw agy run: IPD hinpcf executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261012-6ly144-01-hinpcf-widen-spec-2vev8j-section-4-4-to-bind-date-readers-to-the-cl.ipd.md); evidence .aw/records/plans/executed/20261012-6ly144-01-hinpcf-widen-spec-2vev8j-section-4-4-to-bind-date-readers-to-the-cl.ipd.md
- 2026-10-12 graduated (aw backlog): graduated by run run-20261012T005650Z-2322198: hinpcf
- 2026-10-02 created (aw backlog): Raised as OQ-02 of plan 840y6i (Set doe2fo), which fixes two readers comparing a UTC-stamped value against a local date.today(). 4.4 binds 'every writer' and calls local time 'a RENDER-TIME concern only', so a reader is arguably outside its letter; but plan 840y6i MEASURED ten live artifacts in the real corpus carrying two contradictory staleness verdicts at the same instant, which is the render contradicting itself across two readers of one record. The fix needs no amendment (it is justified by the measurement), so this is a CONTRACT-WORDING question for the maintainer, not a defect. The useful version of the sentence would also make the two deliberately-LOCAL readers (plans_archive._age_days, research_archive._age_days, whose stored operands are LOCAL per DECISIONS.md D55) follow from the contract rather than from one plan's prose. Amending an approved, human-attested spec changes the contract every plan in this cluster is reviewed against, which is why plan 840y6i deferred rather than wrote it. Plan 840y6i's E-04 census (every date call with its other operand's clock) is the input a maintainer would want before ruling.
