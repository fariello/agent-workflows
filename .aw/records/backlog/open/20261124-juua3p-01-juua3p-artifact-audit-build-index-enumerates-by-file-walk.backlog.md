- Id: juua3p
- Status: open
- Set: juua3p
- Work-Kind: followup
- Priority: low
- Summary: artifact_audit.build_index enumerates by file walk plus per-file header reads (about 2s per call, 3547 paths on this repo) instead of reading the artifact_meta SQLite cache that spec 4sd62s 4.5 names as the replacement for the deleted _INDEX_CACHE
- Short-Description: artifact_audit.build_index enumerates by file walk plus per-file header reads (about 2s per call, 3547 paths on this repo) instead of reading the artifact_meta SQLite cache that spec 4sd62s 4.5 names as the replacement for the deleted _INDEX_CACHE

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Notes

- Measured 2026-11-24 in the h3jp4e lane: a cold `build_index` call costs about 3.0s both before and after h3jp4e (3549 paths). Only a repeated in-process call changed, from 0.018s (memo hit) to about 2.3s. The run viewer builds the index once per command and passes it as `artifact_index=`, so no user command measured here pays the repeat cost.
- Constraint on any fix: the `artifact_meta` `artifacts` table keys on `id6` (`id6 TEXT PRIMARY KEY`), so it cannot represent two files declaring the same id6. `build_index.by_declared_id` must keep such collisions visible (the phantom-collision tests in `tests/test_artifact_audit_identity_staleness.py`). A cache-backed `build_index` therefore needs a collision-preserving source and cannot use `artifact_meta.query` alone.

## Workflow history
- 2026-11-24 created (aw backlog): artifact_audit.build_index enumerates by file walk plus per-file header reads (about 2s per call, 3547 paths on this repo) instead of reading the artifact_meta SQLite cache that spec 4sd62s 4.5 names as the replacement for the deleted _INDEX_CACHE
