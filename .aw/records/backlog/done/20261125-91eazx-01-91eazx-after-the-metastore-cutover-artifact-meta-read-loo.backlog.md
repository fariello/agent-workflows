- Id: 91eazx
- Status: done
- Set: 91eazx
- Work-Kind: bug
- Priority: high
- Summary: After the metastore cutover, artifact_meta.read_loose_id returns None for a log-format record (YAML in-file mirror), so its callers (selectors._read_id, plans_refs, coverage_record, readiness_recheck, specs, oc/agy runipd _read_id, artifact_audit) lose the id6
- Short-Description: After the metastore cutover, artifact_meta.read_loose_id returns None for a log-format record (YAML in-file mirror), so its callers (selectors._read_id, plans_refs, coverage_record, readiness_recheck, specs, oc/agy runipd _read_id, artifact_audit) lose the id6

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-27 done (aw set): Fixed directly in commit 51219d981 (agent_workflows/artifact_meta.py::read_loose_id checks read_mirror_id6 first; verified with tests/test_read_loose_id_mirror.py and tests/test_metastore_cutover_code_patch.py).
- 2026-11-25 created (aw backlog): After the metastore cutover, artifact_meta.read_loose_id returns None for a log-format record (YAML in-file mirror), so its callers (selectors._read_id, plans_refs, coverage_record, readiness_recheck, specs, oc/agy runipd _read_id, artifact_audit) lose the id6

Found while executing plan g45vyv (attempt 2) on a scratch tree holding main 37be2b0f9 plus both cutover patches. perform_coordinator_proposal_file read the new scaffolded plan's id6 with read_loose_id, got None (the post-cutover file carries only the '---\nid: <id6>\nstatus: ...\n---' mirror), and fell back to the PROPOSING plan's id6, so the commit omitted the new plan's meta/<id6>.jsonl log. g45vyv fixed that one call site inside metastore-code.cutover.patch by trying artifact_meta.read_mirror_id6 first. The other callers listed in the summary were not checked behaviorally and still call read_loose_id alone on the switched tree. Fix direction: make read_loose_id (or a shared id reader) fall back to read_mirror_id6 inside the cutover code patch, with a behavioral test per caller class.
