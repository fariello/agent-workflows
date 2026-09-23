- Id: zmo0ao
- Status: open
- Blocks-Release: next
- Set: zmo0ao
- Priority: high
- Work-Kind: bug
- Summary: a hand-integrated lane leaves its plan approved in pending/, so the runner re-dispatches an already-merged plan and spends an agent turn on an empty diff

## Workflow history
- 2026-09-22 created (aw backlog): Found while executing li44r9: its lift, backlog and evidence commits plus the integrate commit are all ancestors of HEAD, yet the plan sat approved in pending/ and was queued at position 02, costing a turn that produced no code. Distinct from lb5dzj, which covers the already-executed status rather than a stale approved one.

/tmp/opencode/li44r9-finding-body.md
