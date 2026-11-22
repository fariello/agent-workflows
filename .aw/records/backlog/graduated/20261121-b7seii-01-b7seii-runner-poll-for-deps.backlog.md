- Id: b7seii
- Status: graduated
- Graduated-To: b7seii
- Set: b7seii
- Work-Kind: feature
- Priority: medium
- Summary: Add --poll-for-deps duration flag to aw agy run and aw oc run so dependent runs wait until external prerequisites execute
- Short-Description: Add --poll-for-deps duration flag to aw agy run and aw oc run so dependent runs wait until external prerequisites execute

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 graduated (aw set): Graduated to child plan z7uxhf (set b7seii)
- 2026-11-22 created (aw backlog): Add --poll-for-deps duration flag to aw agy run and aw oc run so dependent runs wait until external prerequisites execute

Add a shared --poll-for-deps DURATION option (accepting positive values with s, m, h, or d suffixes such as 30s, 5m, 30m, 1h, 1d) to both aw agy run and aw oc run. Before creating any durable run directory or freezing base_head, initialize_run_core polls at the configured interval when all unmet external dependencies are still actionable (for example approved, reviewed, to-review, draft, open, graduated, or implementing), sleeping in short Ctrl-C-interruptible slices and re-reading fresh repository state on each tick. Permanently unsatisfiable dependencies (superseded, not-executed, parked, absent, or internal cycles) still refuse immediately with RUN-DEPENDENCY-UNSATISFIABLE.
