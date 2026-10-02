- Id: 9vfxhn
- Status: open
- Set: 9vfxhn
- Priority: low
- Work-Kind: chore
- Summary: Triage and resolve the 22 dangling test citations attributable to non-trim deletion commits

## Workflow history
- 2026-10-01 created (aw backlog): Triage and resolve the 22 dangling test citations attributable to non-trim deletion commits

The lost_guard_census scanner found 19 to 22 dangling test-path citations across the live tree that are attributable to neither 19313eed nor 80db6750c. These represent separate historical deletion events that left stale citations in live code/documentation. Each citation site should be investigated, repointed to surviving tests, or cleaned up.
