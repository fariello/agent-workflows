- Id: b6i85r
- Status: open
- Blocks-Release: next
- Set: b6i85r
- Priority: high
- Work-Kind: bug
- Summary: aw specs note reports 'appended a history record' but DELETES every pre-existing Workflow history entry

## Workflow history
- 2026-09-19 created (aw backlog): aw specs note reports 'appended a history record' but DELETES every pre-existing Workflow history entry

REPRODUCED 2026-09-19 in an isolated scratch repo containing one spec whose '## Workflow history' held two entries dated 2026-09-01 and 2026-09-02. Running:

    aw specs note <spec> --message 'a third note'

exits 0 and prints 'aw specs note: appended a history record to <spec>'. The section afterwards contains ONLY the new line; BOTH pre-existing entries were destroyed (2 of 2). The verb's own success message asserts the opposite of what it did, which is why the damage is silent.

MEASURED IN THE LIVE TREE TOO, which is how it was found. Using the verb as instructed while executing orchprobe-03 (m7gvuz) destroyed real maintainer history in two approved specs before it was caught and hand-restored from git:

  * 77tr3o lost its 2026-09-06 entry recording the MAINTAINER'S OQ-1/OQ-2 RULINGS (shape (b), the rejected linter route and why, and the accepted cost). That is a decision record, not bookkeeping: the rejected option and the reason for rejecting it are exactly the part a future reader needs, and the spec's own Section 5 says so.
  * 25kzda lost THREE entries (two 2026-09-14 amendments recording --allow-dirty-base and the two integration flags, and a 2026-09-13 amendment recording 5.3a telemetry).

WHY THIS IS HIGH AND RELEASE-GATING. AGENTS.md instructs agents to record spec amendments with this verb ('aw specs set'/'note'/'check' OWN spec status and history), so following the documented contract is what causes the loss, and the loss is of ATTESTED HUMAN DECISIONS. An agent that does not diff afterwards will not notice, and the next reader cannot tell a spec that was never amended from one whose amendment record was eaten. Every use of the verb since it acquired this behavior is suspect.

WHAT TO CHECK WHEN FIXING: whether the writer rebuilds the section from a single new record instead of reading-then-appending; whether 'aw specs set --status ... --message' shares that writer (it appends a history record too, so it may carry the same defect); and whether any spec in the tree is already missing history that git history still shows. A regression test should assert that N pre-existing entries plus one note yields N+1 entries, and that the ORDER is stable.
