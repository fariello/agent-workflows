- Id: 3z91mq
- Status: graduated
- Graduated-To: 3z91mq
- Blocks-Release: next
- Set: 3z91mq
- Priority: low
- Work-Kind: bug
- Summary: derive_item_disposition and the disposition summary crash on a malformed queue entry, losing the per-artifact lines and the closing verdict

## Workflow history
- 2026-09-29 set (aw backlog): graduated by run run-20260929T021205Z-3914774: cup9r7
- 2026-09-28 created (aw backlog): Filed while authoring plan w7e3e3 (from backlog 5rebcb) as the durable carrier for that plan's deferred row. MEASURED at HEAD 07580297: run_selection_policy.summarize_dispositions(['not-a-mapping'], None), .render_disposition_summary(['not-a-mapping']) and .render_queue_dispositions(['not-a-mapping']) each raise AttributeError: 'str' object has no attribute 'get'. The crash point is derive_item_disposition's first statement, 'get = entry.get', which binds the bound method with no isinstance guard; every one of the three public renderers reaches it. WHY IT MATTERS: render_disposition_summary is the THIRD statement in both hosts' run_queue exit tails (write_report, render_run_summary_table, this, render_continuation_hint, exit_code_statuses), so it too crashes BEFORE the footer, and it is the surface that prints the honest 'NO WORK WAS PERFORMED' verdict. Work-Kind bug because the closing verdict for work that actually completed is lost on the exit path. WHY NOT FIXED IN w7e3e3: run_selection_policy.py is outside that plan's fence, and that module is deliberately import-pure (two stdlib imports), so its tolerance contract is a decision about this module rather than a consequence of guarding the shared predicate. RELATED BUT DISTINCT: open items b7oicl (wrong COMPLETED verdict) and mjrac4 (the two divergent unsatisfied_dependencies shapes) both touch these same functions; neither describes a crash or a non-mapping entry. FIX DIRECTION (not decided): guard derive_item_disposition fail-closed so one guard serves all three renderers, matching runner_shared.no_turn_was_attempted's documented policy, and decide whether an unreadable entry renders its own disposition code or is counted separately.
