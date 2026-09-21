- Id: 0z1b2s
- Status: open
- Set: 0z1b2s
- Priority: low
- Work-Kind: followup
- Summary: Decide whether to backfill the Readiness field on pending plans that lack one

## Workflow history
- 2026-09-21 created (aw backlog): Deferred by plan qhy3i3 (rdyrecheck-01) and filed so the obligation has a durable carrier rather than vanishing when that plan reaches executed (aw ipd lint advisory check.ipd-uncarried-obligation). Re-measured at HEAD 5421fc10: of 85 pending plans, 79 carry a - Readiness: field and 6 do not. Absence is a LEGITIMATE state, not a defect: plan_readiness.approval_refusals falls back to the prose verdict in the newest review record when the field is absent, and refuses outright only when the field is present but out-of-vocab. So nothing is broken today. The open question is whether the field should be backfilled for uniformity, and the new aw ipd recheck-readiness verb deliberately REFUSES an absent field (it re-evaluates a recorded readiness, it does not mint one, because minting would assert a review that never happened), so the verb cannot be used for a backfill and any backfill needs its own authority and evidence rule. Decision belongs to the maintainer.
