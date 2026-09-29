- Id: fcodik
- Status: graduated
- Graduated-To: fcodik
- Blocks-Release: next
- Set: fcodik
- Priority: low
- Work-Kind: bug
- Summary: write_report raises TypeError on a malformed queue entry, and it is the FIRST exit-path statement so it loses the closing report outright

## Workflow history
- 2026-09-29 set (aw backlog): graduated by run run-20260929T021205Z-3914774: 0kh97v
- 2026-09-28 created (aw backlog): Filed while authoring plan w7e3e3 (from backlog 5rebcb) as the durable carrier for that plan's deferred row. MEASURED at HEAD 07580297: oc_runipd.write_report(run_dir, {'repo':'/repo','run_id':'run-xyz','set_sessions':{},'queue':['not-a-mapping']}) raises TypeError: string indices must be integers, not 'str'. The crash point is the shared runner_shared.write_report body's counting loop, which subscripts item['status'] directly rather than reading it with .get; both hosts' write_report are thin wrappers over it. WHY IT MATTERS MOST OF THE THREE: it is the FIRST statement in both hosts' run_queue exit tails (this, then render_run_summary_table, then render_disposition_summary, then render_continuation_hint, then exit_code_statuses), which makes it the true blocker for the motive backlog 5rebcb was filed on ('a state.json an older driver wrote, or one a partial write corrupted, would crash the footer and lose the closing report for work that actually completed'). Plan w7e3e3 guards item_reached_success and deliberately does NOT claim to restore that report, because this site still crashes first. Work-Kind bug because the durable execution-report.md and the closing output for completed work are lost on the exit path. NOTE THE DIFFERENT EXCEPTION: TypeError from a subscript, not the AttributeError from a .get that the other three sites raise, so a fix modelled on them will not cover this one. WHY NOT FIXED IN w7e3e3: it is a different expression raising a different exception, and fixing it requires deciding what an unreadable entry should be COUNTED AS in a persisted report, which is a reporting-contract decision rather than a predicate guard. FIX DIRECTION (not decided): make the counting loop tolerant fail-closed, and decide whether a malformed entry is counted under its own bucket or omitted with a stated caveat in the report.
