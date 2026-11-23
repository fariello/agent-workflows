- Id: xi6xeq
- Status: open
- Set: xi6xeq
- Work-Kind: bug
- Priority: high
- Summary: aw rename plans and aw group plans crash with AttributeError ('dict' object has no attribute 'text') in plans_refs.apply_renames on a log-format plan, and write no rename event
- Short-Description: aw rename plans and aw group plans crash with AttributeError ('dict' object has no attribute 'text') in plans_refs.apply_renames on a log-format plan, and write no rename event
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-23 created (aw backlog): aw rename plans and aw group plans crash with AttributeError ('dict' object has no attribute 'text') in plans_refs.apply_renames on a log-format plan, and write no rename event

Found while executing IPD v45j1n (2026-11-23). Repro: a tmp git repo with .aw/config/project.json metadata_schema 2, meta.create of an ipd ab12cd at plans/pending/20261109-demo-01-ab12cd-sample.ipd.md, then cli.main(['rename','plans','ab12cd','--slug','renamed','--apply']) or ['group','plans','ab12cd','--set','newset','--apply']. Both raise AttributeError at plans_refs.apply_renames ('_check_order_lines(preview.text, ...)'): the preview there is a dict on the log branch. Plans route to plans_refs.run_mv / run_set_assign, not to artifact_rename.run_rename_generic / run_group_generic, so v45j1n's rename events do not cover them; spec 4sd62s 4.2 PATH HISTORY requires aw rename and aw group to append a rename event (verb rename/group) for plans too. Dormant on main today (no record has a log), so no user hits it before the cutover; it must be fixed before the cutover (cxxmyv).
