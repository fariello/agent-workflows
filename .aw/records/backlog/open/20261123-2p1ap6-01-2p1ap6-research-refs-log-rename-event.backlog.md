- Id: 2p1ap6
- Status: open
- Set: 2p1ap6
- Work-Kind: bug
- Priority: high
- Summary: aw research mv and aw research set-assign on a log-format research record write no rename event: they move the file and edit in-file metadata on the legacy path
- Short-Description: aw research mv and aw research set-assign on a log-format research record write no rename event: they move the file and edit in-file metadata on the legacy path
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-23 created (aw backlog): aw research mv and aw research set-assign on a log-format research record write no rename event: they move the file and edit in-file metadata on the legacy path

Found while executing IPD v45j1n (2026-11-23). Repro: a tmp git repo with metadata_schema 2, meta.create of research rs12ab at research/20261109-demo-01-rs12ab-sample.research.md, then cli.main(['group','research','rs12ab','--set','newset','--apply']). It exits 0, renames the file and prints 'set metadata set/order/kind in <file>', but meta/rs12ab.jsonl still holds only the create event, so the log path and Set no longer match the file. Research routes to research_refs.run_mv / run_set_assign, outside v45j1n's scope (artifact_rename generic engine and plans_archive). Spec 4sd62s 4.2 PATH HISTORY says aw research mv writes verb rename and aw research set-assign writes verb group. Dormant on main today (no record has a log); must be fixed before the cutover (cxxmyv).
