- Id: axayfn
- Status: open
- Blocks-Release: next
- Set: idcapture
- Priority: medium
- Work-Kind: bug
- Summary: Three identity readers outside plan 76w6mq's fence are still unbounded to the metadata region

## Workflow history
- 2026-09-21 created (aw backlog): Three identity readers outside plan 76w6mq's fence are still unbounded to the metadata region

MEASURED 2026-09-21 while executing plan 76w6mq, which bounded identity extraction to the metadata region (selectors.metadata_region) for selectors._read_id/_read_status/_read_setid, the two public runner-facing readers, and check_engine's _ID_LINE_RE/_SET_LINE_RE identity+setid readers. THREE readers of the same shape remain unbounded, so the same quoted-metadata defect is still latent in them.

1. check_engine._ITEM_ID_RE (agent_workflows/check_engine.py:2687), matching '^- Id:' with [ \\t]* tolerance, is applied to whole file bodies at ~10 call sites (lines 1897, 2089, 2861, 3128, 3305, 3718, 3772, 3815, 3821 and the spec scan reached from runner_shared). MEASURED IT IS LIVE-DIVERGENT: over the 1614 tracked records under .aw/records/, an unbounded _ITEM_ID_RE read differs from a region-bounded read on exactly 2 files, both the research docs that quote '- Id: uyeko5' (it returns uyeko5; bounded returns None). NO CURRENT SYMPTOM, and that is why it was NOT fixed inside 76w6mq's fence: every one of those call sites iterates plans, backlog or specs, never research, so no live call reaches an affected file today. It is a latent trap for the next caller that points _ITEM_ID_RE at a research or prompt record.

2. runner_shared.discover_specs (agent_workflows/runner_shared.py:5507) pairs a region-BOUNDED status read (selectors.read_front_matter_status, bounded by 76w6mq) with an UNBOUNDED id6 read (check_engine._ITEM_ID_RE) on the same text, so one record's two fields are now read under two different boundary rules. Measured over the live spec corpus: 0 specs diverge today, so this is latent, not broken.

3. status_set._ID_RE (agent_workflows/status_set.py:133) is the reader artifact_core.repository_id6s already documents as the known survivor: 'THE SPECIFIC UNBOUNDED READER BEHIND THIS SET IS status_set._ID_RE, and it is OUTSIDE 76w6mq's declared scope'. It was previously filed as backlog q1ov25; this item records the other two beside it so the remaining set is countable in one place rather than spread across code comments. Check whether q1ov25 should absorb this or stay separate.

WHY IT MATTERS: the whole point of 76w6mq is that identity comes from where an artifact DECLARES it. A reader left unbounded can still read a QUOTATION as a declaration, and the failure mode is not cosmetic: unbounded reads manufactured an id6 collision that made a real plan unaddressable by every status verb, with the refusal explicitly saying it was not overridable by --force.

RECOMMENDED FIX: route all three through selectors.metadata_region, the single shared helper 76w6mq introduced, rather than adding a local region parser (a second parser is precisely how the reader drift documented at selectors.read_front_matter_id happened before). Expect zero behavior change on today's corpus for (1) and (2), which is what makes them cheap and safe to close; (3) deliberately over-collects for MINTING and must stay a superset there, so bounding it needs artifact_core.repository_id6s' contract read first.
