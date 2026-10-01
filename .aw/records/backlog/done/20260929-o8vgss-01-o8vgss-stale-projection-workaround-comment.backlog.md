- Id: o8vgss
- Status: done
- Set: o8vgss
- Priority: low
- Work-Kind: chore
- Summary: the --fields projection workaround comment in run_analytics_cli._emit_query_agent asserts a defect that gygujf already fixed, so it misdescribes live behavior

## Workflow history
- 2026-10-01 done (aw set): Fixed by plan mcdvx0: the stale crash workaround comment was updated to reflect live behavior resting on next preservation rather than the counts rationale, which F-03 measured false
- 2026-09-29 created (aw backlog): Carrier filed while authoring plan wqiofa (backlog un6ppd). run_analytics_cli._emit_query_agent carries a multi-paragraph comment stating that 'AgentRenderer.render_summary(..., context=ctx) with ctx.fields set RAISES ValueError: Invalid aw.agent/v1 record: Summary record missing required field total', because filter_record_fields preserved only _MANDATORY_FIELDS while validate_agent_record additionally required total/emitted/omitted. MEASURED AT HEAD 95d1d114 THAT IS NO LONGER TRUE: render_summary with ctx.fields=['cmd'] returns a valid line carrying total/emitted/omitted. The fix landed in commit 5adf3774 'preserve per-kind required fields under --fields projection (gygujf)', which widened _PRESERVED_FIELDS to include applied/total/emitted/omitted. So the comment now tells a reader a live defect exists where none does, and its stated workaround (render the summary WITHOUT the field projection) is no longer necessary, though it remains harmless and arguably still correct on its own separate ground that projecting a summary's counts away would defeat the emitted+omitted==total invariant. Comment-only cleanup; excluded from wqiofa because that file is outside its Scope-Paths.
