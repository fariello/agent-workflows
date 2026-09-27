- Id: ibk7bt
- Status: graduated
- Graduated-To: uniwait
- Blocks-Release: next
- Set: uniwait
- Priority: high
- Work-Kind: bug
- Summary: Five code-only waits (finalize lock, integration lock, deferral ladder, aw writer lock, setter commit race) use five different ad-hoc timings; a busy peer fails items or leaves changes uncommitted

## Workflow history
- 2026-09-27 graduated (aw set): Graduated 2026-09-27 into to-review plan 9bq5o4 (Set uniwait).
- 2026-09-27 created (aw backlog): Five code-only waits (finalize lock, integration lock, deferral ladder, aw writer lock, setter commit race) use five different ad-hoc timings; a busy peer fails items or leaves changes uncommitted

Measured 2026-09-27: 7icz68, 4eecvh, 8y13kn, cnzrxb and 3rsdbj ended fail-gate because the finalize writer lock was held by a peer run; the aw writer lock waits 5s then commits unserialized; a setter that loses the commit race (ISO_RACED) leaves its file change uncommitted (seen twice this session). Maintainer ruling 2026-09-27: all five check every 10s, report every 60s, fail after 30 minutes; the hook re-stage retry stays one immediate redo; the agent retry budget keeps separate counters per failure kind.
