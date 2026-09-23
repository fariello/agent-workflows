- Id: b6i85r
- Status: done
- Blocks-Release: next
- Set: b6i85r
- Priority: high
- Work-Kind: bug
- Summary: aw specs note reports 'appended a history record' but DELETES every pre-existing Workflow history entry

## Workflow history
- 2026-09-23 done (aw set): Already FIXED by executed plan vhbvwz (setterguard Order 02, commit fbf85068), which reversed the slimming in specs._append_history and backlog._reattach_history so both PREPEND and PRESERVE prior rounds. Verified live at HEAD 22cf67d9 by probing specs._append_history on a 3-round fixture: 4 rounds out, all 3 priors intact. The maintainer's 2026-09-10 ruling (vhbvwz OQ-01) made inline history the DURABLE home for specs and backlog items, matching plans, so this item's fix-option (a) (re-track the gitignored sidecar) is settled against. Closed via the SATISFIED path. What SURVIVED this family is tracked by IPD 7jqev2 (histresid): the migration slimmer, the oldest-first legacy reader, and the missing specs dedup.
- 2026-09-19 created (aw backlog): aw specs note reports 'appended a history record' but DELETES every pre-existing Workflow history entry

REPRODUCED 2026-09-19 in an isolated scratch repo containing one spec whose '## Workflow history' held two entries dated 2026-09-01 and 2026-09-02. Running:

    aw specs note <spec> --message 'a third note'

exits 0 and prints 'aw specs note: appended a history record to <spec>'. The section afterwards contains ONLY the new line; BOTH pre-existing entries were destroyed (2 of 2). The verb's own success message asserts the opposite of what it did, which is why the damage is silent.

MEASURED IN THE LIVE TREE TOO, which is how it was found. Using the verb as instructed while executing orchprobe-03 (m7gvuz) destroyed real maintainer history in two approved specs before it was caught and hand-restored from git:

  * 77tr3o lost its 2026-09-06 entry recording the MAINTAINER'S OQ-1/OQ-2 RULINGS (shape (b), the rejected linter route and why, and the accepted cost). That is a decision record, not bookkeeping: the rejected option and the reason for rejecting it are exactly the part a future reader needs, and the spec's own Section 5 says so.
  * 25kzda lost THREE entries (two 2026-09-14 amendments recording --allow-dirty-base and the two integration flags, and a 2026-09-13 amendment recording 5.3a telemetry).

WHY THIS IS HIGH AND RELEASE-GATING. AGENTS.md instructs agents to record spec amendments with this verb ('aw specs set'/'note'/'check' OWN spec status and history), so following the documented contract is what causes the loss, and the loss is of ATTESTED HUMAN DECISIONS. An agent that does not diff afterwards will not notice, and the next reader cannot tell a spec that was never amended from one whose amendment record was eaten. Every use of the verb since it acquired this behavior is suspect.

WHAT TO CHECK WHEN FIXING: whether the writer rebuilds the section from a single new record instead of reading-then-appending; whether 'aw specs set --status ... --message' shares that writer (it appends a history record too, so it may carry the same defect); and whether any spec in the tree is already missing history that git history still shows. A regression test should assert that N pre-existing entries plus one note yields N+1 entries, and that the ORDER is stable.
