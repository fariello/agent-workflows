- Id: 36nh0o
- Status: open
- Set: 36nh0o
- Priority: low
- Work-Kind: followup
- Summary: Re-analyze cached runs so the newly-computed event_count metric is populated for runs analyzed before metgap 6krsym

## Workflow history
- 2026-09-20 created (aw backlog): metgap 6krsym made event_count a computed metric (it was advertised and never produced). A cache entry written before that change carries no event_count key, so the metric reads as missing for every historical run until its entry is rebuilt. aw runs analyze --rebuild already does this and needs no code change; whether and when to spend the rebuild is the operator's call, which is why this is a carrier rather than work inside that plan. Deferred row 4 of 20260917-metgap-01-6krsym.
