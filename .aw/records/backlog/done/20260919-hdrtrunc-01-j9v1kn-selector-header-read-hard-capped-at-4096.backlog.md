- Id: j9v1kn
- Status: done
- Blocks-Release: next
- Set: hdrtrunc
- Priority: high
- Work-Kind: bug
- Summary: selectors._read_header hard-capped its read at 4096 bytes, so a '- Set:'/'- Id:'/'- Status:' bullet past that offset was invisible: 69 plans silently dropped from setid resolution, wedging orchestrator 7ewc74 forever

## Workflow history
- 2026-09-19 created (aw backlog): Found while investigating why 7ewc74 could not retire despite all three children being executed on disk. Fixed in the same change: _read_header now reads to the end of the metadata block (structural bound), with three regression pins and a mutation check.
