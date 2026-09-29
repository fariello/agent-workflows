- Id: s438xd
- Status: graduated
- Graduated-To: s438xd
- Blocks-Release: next
- Set: s438xd
- Priority: low
- Work-Kind: bug
- Summary: render_run_summary_table crashes on a malformed queue entry, losing the closing report before the footer is reached

## Workflow history
- 2026-09-29 set (aw backlog): graduated by run run-20260929T021205Z-3914774: 165lkb
- 2026-09-28 created (aw backlog): Filed while authoring plan w7e3e3 (from backlog 5rebcb) as the durable carrier for that plan's deferred row. MEASURED at HEAD 07580297: render_stream.render_run_summary_table({'repo':'/repo','run_id':'run-xyz','set_sessions':{},'queue':['not-a-mapping']}, None) raises AttributeError: 'str' object has no attribute 'get'. WHY IT MATTERS: this is the SECOND statement in both hosts' run_queue exit tails (write_report, then this, then render_disposition_summary, then render_continuation_hint, then exit_code_statuses), so it crashes BEFORE the footer. That ordering is why fixing item_reached_success alone (5rebcb, plan w7e3e3) does NOT restore the closing report for a run whose state.json holds a malformed entry: the report is already lost here. Work-Kind bug because a user-perceptible outcome (the closing report for work that actually completed) is lost on the exit path. WHY NOT FIXED IN w7e3e3: render_stream.py is outside that plan's fence; its crash is in its OWN .get reads rather than in the shared predicate w7e3e3 guards, and widening would turn a one-line predicate guard into a cross-module tolerance pass. RELATED BUT DISTINCT: open item b7oicl concerns this same function's COMPLETED-at-100-percent verdict for a never-dispatched queue and cites derive_item_disposition as the vocabulary to consume; it describes a wrong verdict, not a crash, and names no malformed-entry case. FIX DIRECTION (not decided): guard the per-entry reads fail-closed, as runner_shared.no_turn_was_attempted already does (a non-mapping entry returns False because an unreadable entry cannot be shown to have run), and decide what such an entry should RENDER as rather than silently dropping the row.
