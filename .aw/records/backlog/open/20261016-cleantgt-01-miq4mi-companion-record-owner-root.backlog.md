- Id: miq4mi
- Status: open
- Set: cleantgt
- Priority: low
- Work-Kind: followup
- Summary: record-file-to-root walkers for records under a companion records backend

## Workflow history
- 2026-10-16 created (aw backlog): record-file-to-root walkers for records under a companion records backend

Plan ki6t17 (backlog 4uw2a6) reverse-maps record files under AW_HOME/projects/<id>/records to their owning repository root. A record under a COMPANION records root (records_backend: companion, records at <companion_dir>/records) has the same shape of problem: climbing from the record does not reach the target repository. Not measured; 4uw2a6 names AW_HOME only. Measure whether a walker misroutes there (e.g. aw specs note <companion spec>, aw ipd lint --phase pre-execution on a dependent companion plan) and, if so, extend project_context.record_owner_root to companion roots.
