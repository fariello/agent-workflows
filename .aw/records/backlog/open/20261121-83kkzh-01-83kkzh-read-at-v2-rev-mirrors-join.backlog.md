- Id: 83kkzh
- Status: open
- Set: 83kkzh
- Work-Kind: bug
- Priority: medium
- Summary: Join rev_mirrors with rev_log_states in artifact_meta.read_at for v2 log-backed records (spec 4sd62s 4.4 / 4.5a)
- Short-Description: Join rev_mirrors with rev_log_states in artifact_meta.read_at for v2 log-backed records (spec 4sd62s 4.4 / 4.5a)
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 created (aw backlog): Join rev_mirrors with rev_log_states in artifact_meta.read_at for v2 log-backed records (spec 4sd62s 4.4 / 4.5a)

Spec 4sd62s sections 4.4 and 4.5a specify that artifact_meta.read_at joins rev_log_states with rev_mirrors so the returned State contains both the replayed log state and the mirrored status from the .md file at that revision, failing closed on mirror validation errors. Currently the v2 meta/<id6>.jsonl branch in agent_workflows/artifact_meta.py::read_at replays and caches rev_log_states without validating or joining the .md mirror blob at rev in rev_mirrors. Discovered during execution of metastore IPD snh19k.
