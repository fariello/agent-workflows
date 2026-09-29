- Id: 3kr193
- Status: open
- Set: 3kr193
- Priority: low
- Work-Kind: chore
- Summary: Decide whether run-directory outcomes/ should be guaranteed by its writers, as sessions/ and prompts/ now are

## Workflow history
- 2026-09-29 created (aw backlog): Decide whether run-directory outcomes/ should be guaranteed by its writers, as sessions/ and prompts/ now are

Follow-on from plan z3ifg8 (backlog hblsqo), which made the two session-log and prompt writers create their own parent directory instead of obliging every caller to precreate it. That plan deliberately scoped outcomes/ OUT, and this item carries the open question.

WHY IT IS HARDER THAN ITS TWO SIBLINGS: 'the writer creates its own parent' resolved to a single site for both write_prompt and the two attempt-log opens, but does NOT for outcomes/. The paths are constructed in at least three distinct places with different owners: runner_shared computes 'run_dir / "outcomes" / f"{position:02d}-{id6}.json"' for READING; lane_containment builds three separate 'run_dir / "outcomes" / ...' paths for lane plumbing (prompt_outcome, lane_outcome, and a merge destination); and oc_runipd.handle_audit_command's verdict_path is written by the AGENT inside a lane rather than by the driver. So the correct owner of the mkdir differs per site and needs its own analysis.

WHY IT IS NOT URGENT: runner_shared.initialize_run_core still creates outcomes/ for every queued run, and oc_runipd.handle_audit_command creates it for the audit verb, so no known caller is currently broken. This is the symmetry question, not a live crash.

DECIDE: either guarantee it at each writing site (and then whether initialize_run_core's mkdir loop still earns its place), or record that outcomes/ is deliberately caller-created because an agent-written verdict has no single in-process writer.
