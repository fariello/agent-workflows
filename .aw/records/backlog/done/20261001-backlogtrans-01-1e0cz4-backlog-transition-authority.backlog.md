- Id: 1e0cz4
- Status: done
- Graduated-To: backlogtrans
- Set: backlogtrans
- Priority: low
- Work-Kind: chore
- Summary: Decide whether any backlog status transition needs an authority attestation, the backlog counterpart of TRANSITION_AUTHORITY

## Workflow history
- 2026-10-08 done (aw backlog): closed by aw agy run: IPD tm8k2n executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261002-backlogtrans-02-tm8k2n-decide-whether-any-backlog-status-transition-needs-an-author.ipd.md); evidence .aw/records/plans/executed/20261002-backlogtrans-02-tm8k2n-decide-whether-any-backlog-status-transition-needs-an-author.ipd.md
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T222151Z-2118435: tm8k2n
- 2026-10-01 note (aw backlog): Split out of plan cc2m29 (Set backlogtrans), which answers 'is this edge legal' and deliberately NOT 'may THIS actor perform it'. Specs keep the two questions in two separate structures (attention_contract.SPEC_TRANSITIONS for legality, attention_contract.TRANSITION_AUTHORITY for authority, the latter carrying by_human/human_token/evidence/review_record per transition). Backlog has NEITHER today; cc2m29 adds only the legality half. THIS IS A DESIGN DECISION, NOT A WIRING FIX: it needs a maintainer ruling on whether any backlog move deserves a --by-human attestation. The plausible candidate is ->done, since closing a release-blocking item already has its own fail-closed predicate (check_engine.evaluate_blocking_close) that an authority table would have to compose with rather than duplicate. Low priority: no measured harm, and the legality gate is the part that closes an actual hole.
- 2026-10-01 created (aw backlog): Decide whether any backlog status transition needs an authority attestation, the backlog counterpart of TRANSITION_AUTHORITY
