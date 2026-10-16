- Id: dbr23q
- Status: done
- Blocks-Release: next
- Set: rereview
- Priority: high
- Work-Kind: bug
- Summary: aw oc/agy review refuses to re-review a reviewed or approved plan, contradicting spec 25kzda 2.6; there is no first-class re-review verb

## Workflow history
- 2026-10-16 done (aw backlog): closed by aw agy run: IPD ygngc2 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261015-rereview-02-ygngc2-flag-a-reviewed-or-approved-plan-whose-review-may-be-stale-a.ipd.md); evidence .aw/records/plans/executed/20261015-rereview-02-ygngc2-flag-a-reviewed-or-approved-plan-whose-review-may-be-stale-a.ipd.md
- 2026-10-15 graduated (aw set): graduated to rereview Set: ggsdrl (explicit confirmed re-review) and ygngc2 (advisory staleness flag)
- 2026-10-15 created (aw backlog): aw oc/agy review refuses to re-review a reviewed or approved plan, contradicting spec 25kzda 2.6; there is no first-class re-review verb

Measured 2026-10-15: after a maintainer answered jmogmv OQ-01 (an answer that inverted the plan), 'aw oc run --action review jmogmv' and 'aw oc review jmogmv' both refused: '--action review is illegal ... (status reviewed -> action execute)'. Spec 25kzda 2.6 and its legality table row 'reviewed, --action review: Re-review; keep reviewed; append a review receipt' require this to work; runner_shared.enforce_requested_action rejects any item whose derived action != the requested one. The only workaround is a manual 'aw ipd set to-review <id6>' demotion plus commit, which is untooled ceremony and was itself blocked by a stale index.lock. Need: a first-class re-review for reviewed (and approved, withdrawing approval explicitly) plans, from the runner and from 'aw ipd' / plan-review.
