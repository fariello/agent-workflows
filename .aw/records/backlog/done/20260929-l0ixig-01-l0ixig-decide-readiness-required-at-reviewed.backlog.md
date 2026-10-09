- Id: l0ixig
- Status: done
- Graduated-To: rdyreq
- Set: l0ixig
- Priority: low
- Work-Kind: followup
- Summary: Decide whether a reviewed plan must carry a Readiness field (the mirror of IPD-M107)

## Workflow history
- 2026-10-09 done (aw backlog): closed by aw agy run: IPD fhinri executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261001-rdyreq-01-fhinri-require-the-readiness-field-at-reviewed-and-approved-ipd-m11.ipd.md); evidence .aw/records/plans/executed/20261001-rdyreq-01-fhinri-require-the-readiness-field-at-reviewed-and-approved-ipd-m11.ipd.md
- 2026-10-01 set (aw backlog): graduated by run run-20260930T053053Z-3200037: fhinri
- 2026-09-29 created (aw backlog): Deferred by plan fx5op3 (rdyabsent-01) as its OQ-01, and filed so the obligation has a durable carrier rather than vanishing when that plan reaches executed (check.ipd-uncarried-obligation). CONTEXT: fx5op3 decided, against measurement, that the optional - Readiness: field is NOT backfilled onto plans lacking one, because absence is the field correctly reporting that no review has run. Measured at HEAD 7c215fa7 across all 963 tracked .ipd.md files: ZERO plans at Status draft or to-review carry the field, and in the pending lane the split is a perfect partition (59 to-review all absent, 21 reviewed all present). THE OPEN QUESTION is the MIRROR of that: should a reviewed plan be REQUIRED to carry one, enforced by a new lint rule the way IPD-M107 refuses an unattested value? It is not a simple yes. /plan-review DELIBERATELY leaves the field ABSENT on the R6 orchestrator-exhaustion path (plan-review.md: leave - Readiness: ABSENT entirely), so a required-at-reviewed rule needs an exemption for exactly the case where a review failed to conclude; getting that exemption wrong would either fail conforming plans or reopen the hole IPD-M107 closed. fx5op3 pins the partition in the pre-review direction only, so the gap this carries is that a reviewed plan with no field, outside the R6 path, is caught by nothing. Decision belongs to the maintainer.
