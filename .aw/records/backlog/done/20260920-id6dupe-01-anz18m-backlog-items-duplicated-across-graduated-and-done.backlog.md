- Id: anz18m
- Status: done
- Set: id6dupe
- Priority: medium
- Work-Kind: chore
- Summary: Nine backlog items exist in both graduated/ and done/, so each reports a check.id6-collision

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: fixed by b89e3caf: each of the 9 ids has one copy
- 2026-09-20 created (aw backlog): Found while executing IPD 76w6mq. After 76w6mq's reader fix, aw check all still reports 9 check.id6-collision findings; all nine are one backlog item present in BOTH graduated/ and done/ with the same id6 (yw6759, s9p5x5, gjadwm, plbkp5, wx95o4, bplplj, fjs11i, f8m2z2, rxya25). They are unrelated to quoted metadata: each is a genuine two-copies-of-one-item condition, surfaced (not caused) by sk7ggr making the id6 collision pass terminal-inclusive. Deciding which copy is canonical is a maintainer call, and 76w6mq's Scope-Paths touch no backlog record, so it was reported rather than fixed. Repro: python3 -m agent_workflows check all --json and filter rule=check.id6-collision.
