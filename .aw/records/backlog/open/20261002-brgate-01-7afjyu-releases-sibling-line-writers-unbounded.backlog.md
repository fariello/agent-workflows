- Id: 7afjyu
- Status: open
- Blocks-Release: next
- Set: brgate
- Priority: low
- Work-Kind: bug
- Summary: Six sibling metadata line writers in releases strip their field over the WHOLE text, so setting Priority/Work-Kind/From-Backlog/From-Spec/Item-Dependencies/Graduated-To can delete a matching body line; measured exposure 2026-10-02

## Workflow history
- 2026-10-02 created (aw backlog): Six sibling metadata line writers in releases strip their field over the WHOLE text, so setting Priority/Work-Kind/From-Backlog/From-Spec/Item-Dependencies/Graduated-To can delete a matching body line; measured exposure 2026-10-02

Found reviewing plan b92m14 (E-07 bounds set_blocks_release_line's strip to selectors.metadata_region; this item is the same fix for _PRIORITY_LINE_RE, _WORK_KIND_LINE_RE, _FROM_BACKLOG_LINE_RE, _FROM_SPEC_LINE_RE, _ITEM_DEPENDENCIES_LINE_RE and _GRADUATED_TO_LINE_RE in agent_workflows/releases.py). Follow b92m14 E-07 as the pattern. Graduated-To has a multi-valued grammar; see the comment above _ITEM_GRADUATED_TO_RE. Measured 2026-10-02 over .aw/records/**/*.md, records with a line matching each strip pattern located after metadata_region: Priority 7, Work-Kind 7, From-Backlog 0, From-Spec 0, Item-Dependencies 4, Graduated-To 3. Live counts; re-measure before acting.
