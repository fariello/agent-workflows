- Id: j6llj1
- Status: done
- Set: awphysical-resume
- Priority: medium
- Work-Kind: bug
- Summary: migration inventory sweeps .aw/state/runtime/ (locks + tx journal), creating a self-referential stale-input trap that blocks resume after an interrupted/rolled-back migration

## Workflow history
- 2026-08-16 created (aw backlog): migration inventory sweeps .aw/state/runtime/ (locks + tx journal), creating a self-referential stale-input trap that blocks resume after an interrupted/rolled-back migration
- 2026-08-17 set (aw backlog): Fixed: migration inventory now classifies an existing .aw/state/ tree as disposition 'skip' and excludes it from the migration map (build_migration_map), so a re-apply after a dry-run or rollback no longer trips the 'Source file changed since inventory' stale-input gate. Also removes the .aw/system/system double-nesting from re-migrating a partial .aw. Implemented in tools/awphysical/aw_layout_inventory.py + regression test (commit 5c91499); proven by the real Order-11 move-cutover running clean.

Order 11 rehearsal (resume path). A clean FIRST apply works and is safe (verified: byte-identical system+records, source retained, rollback preserves legacy+in-place adapters). But resume/re-apply after an interrupted or rolled-back migration fails because the inventory re-scans .aw as the partial-aw root and includes .aw/state/runtime/ (migration_writer.lock, migration_transaction.json). The resume then mutates those same files (acquires lock / updates journal), tripping the 'Source file changed since inventory' guard, and the tx ends 'locked'. Root cause: transient runtime state under .aw/state/runtime/ is per-run scratch and must NOT be inventoried as migratable source (spec: state_runtime is never tracked/durable). Fix: exclude .aw/state/runtime/ (at least locks/ and transactions/) from aw_layout_inventory scanning of the partial-aw root. Distinct from the partial-aw:system classifier fix (10efb98) which cleared the first resume blocker. Needs a regression test that a partial .aw/ with runtime lock+journal resumes cleanly.
