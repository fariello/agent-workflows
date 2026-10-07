- Id: no88yi
- Status: open
- Blocks-Release: next
- Set: no88yi
- Priority: low
- Work-Kind: bug
- Summary: aw find --limit inert in human mode

## Workflow history
- 2026-10-07 created (aw backlog): aw find --limit inert in human mode

aw find accepts --limit (registered in the shared noun-verb loop), but in human output mode it is silently ignored and prints all matched rows without truncation. Measured at aw find plans --limit 3, which printed all 1329 plans. IPD okiso1 scoped and implemented --limit for the --agent stream only. Handed off from moegsl deferred row 3 / F-04.
