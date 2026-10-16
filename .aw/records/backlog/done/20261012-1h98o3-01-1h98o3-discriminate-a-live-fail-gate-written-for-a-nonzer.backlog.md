- Id: 1h98o3
- Status: done
- Graduated-To: 1h98o3
- Set: 1h98o3
- Priority: low
- Work-Kind: followup
- Summary: Discriminate a live fail-gate written for a nonzero-exit turn from one written for a gate refusal in the run summary outcome word

## Workflow history
- 2026-10-16 done (aw backlog): closed by aw agy run: IPD rowilw executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261014-1h98o3-01-rowilw-discriminate-live-fail-gate-items-by-attempt-failure-and-out.ipd.md); evidence .aw/records/plans/executed/20261014-1h98o3-01-rowilw-discriminate-live-fail-gate-items-by-attempt-failure-and-out.ipd.md
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131015Z-4038279: rowilw
- 2026-10-13 created (aw backlog): Discriminate a live fail-gate written for a nonzero-exit turn from one written for a gate refusal in the run summary outcome word

Measured in plan 064awu (Findings F-05): since cyamvi (commit 6b94a4d9d), runner_shared.reconcile_disposition's nonzero-exit fallback and its executed-claim-not-moved branch write fail-gate where they previously wrote failed-safely and substantially-complete. As a result, a crashed or non-landing turn now reads BLOCKED in the run summary outcome word where it previously read FAILED or COMPLETED. Gate refusals awaiting a human also write fail-gate and read naturally as BLOCKED. Discriminating these two producers requires a recorded field (exit code, refusal code) rather than overloading the token.
