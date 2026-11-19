- Id: 2i04so
- Status: graduated
- Graduated-To: 2i04so
- Set: 2i04so
- Work-Kind: bug
- Priority: high
- Summary: Wrap check_engine.check_types in artifact_meta.scan_once and ephemeral_if_uninitialized
- Short-Description: Wrap check_engine.check_types in artifact_meta.scan_once and ephemeral_if_uninitialized
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-19 graduated (aw backlog): graduated by run run-20261119T154308Z-4175911: 28k5h5
- 2026-11-18 created (aw backlog): Wrap check_engine.check_types in artifact_meta.scan_once and ephemeral_if_uninitialized

Discovered while running aw check all --agent during metastore Order 143 (dbq57g): check_engine.check_types runs per-type and cross-tree checks sequentially without an outer artifact_meta.scan_once() and artifact_meta.ephemeral_if_uninitialized() context. When .aw/state/index.db is absent (fresh worktree or deleted cache), every inner _meta_records_with_fields, _meta_state_map, and _meta_state_for_path call rebuilds a fresh in-memory SQLite database over the full corpus, making aw check all --agent take ~8 minutes instead of ~20 seconds.
