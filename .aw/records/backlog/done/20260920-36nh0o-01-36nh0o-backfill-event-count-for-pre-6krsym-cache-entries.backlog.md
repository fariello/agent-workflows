- Id: 36nh0o
- Status: done
- Graduated-To: eventcountbf
- Set: 36nh0o
- Priority: low
- Work-Kind: followup
- Summary: Re-analyze cached runs so the newly-computed event_count metric is populated for runs analyzed before metgap 6krsym

## Workflow history
- 2026-09-30 set (aw backlog): closed by aw oc run: IPD vnt9it executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260928-eventcountbf-01-vnt9it-make-an-analytics-cache-entry-rebuild-when-the-producer-s-me.ipd.md); evidence .aw/records/plans/executed/20260928-eventcountbf-01-vnt9it-make-an-analytics-cache-entry-rebuild-when-the-producer-s-me.ipd.md
- 2026-09-28 set (aw backlog): graduated by run run-20260928T235632Z-1358353: vnt9it
- 2026-09-20 created (aw backlog): metgap 6krsym made event_count a computed metric (it was advertised and never produced). A cache entry written before that change carries no event_count key, so the metric reads as missing for every historical run until its entry is rebuilt. aw runs analyze --rebuild already does this and needs no code change; whether and when to spend the rebuild is the operator's call, which is why this is a carrier rather than work inside that plan. Deferred row 4 of 20260917-metgap-01-6krsym.
