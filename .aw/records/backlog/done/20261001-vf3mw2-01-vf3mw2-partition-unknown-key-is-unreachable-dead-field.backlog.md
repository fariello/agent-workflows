- Id: vf3mw2
- Status: done
- Graduated-To: vf3mw2
- Set: vf3mw2
- Priority: low
- Work-Kind: chore
- Summary: aw partition emits an unconditionally empty 'unknown' key on both machine surfaces, because partition.collect has one return statement returning [] for it and raises ValueError on an unknown selector instead, so the field can never carry anything and no caller can learn from it

## Workflow history
- 2026-10-03 done (aw backlog): closed by aw agy run: IPD 0hz005 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261002-vf3mw2-01-0hz005-remove-partition-s-unreachable-unknown-key-from-both-machine.ipd.md); evidence .aw/records/plans/executed/20261002-vf3mw2-01-0hz005-remove-partition-s-unreachable-unknown-key-from-both-machine.ipd.md
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T221834Z-1991716: 0hz005
- 2026-10-01 created (aw backlog): Filed while authoring plan z7ci8k (backlog enygec). The carrier item enygec claimed partition echoed user-supplied ids into 'unknown'; measured at HEAD that is FALSE, the key is always []. Removing it is a surface-contract change (a consumer may read the key's presence), not a sanitization fix, so z7ci8k deliberately leaves it and hands it off here.
