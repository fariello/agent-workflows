- Id: 3pxjya
- Status: done
- Close-Evidence: .aw/records/plans/executed/20261127-metastore-322-6cltab-populate-cli-creator-log-fields-and-align-aw-find-bare-repo.ipd.md
- Set: metastore
- Work-Kind: bug
- Priority: high
- Summary: Post-cutover status_set and check_engine call resolve_project_context without in-tree fallback on bare repos (sibling of ggp2pf and 2etrjf)
- Short-Description: Post-cutover status_set and check_engine call resolve_project_context without in-tree fallback on bare repos (sibling of ggp2pf and 2etrjf)
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-27 done (aw set): Fixed and validated by executed Order 322 plan 6cltab (E-03/V-03, E-04/V-04).
- 2026-11-27 blocked (aw set): covered by Order 322 child plan 6cltab (single-valued From-Backlog carries 0b3ynm)
- 2026-11-27 created (aw backlog): Post-cutover status_set and check_engine call resolve_project_context without in-tree fallback on bare repos (sibling of ggp2pf and 2etrjf)

In the metastore cutover code patch, agent_workflows/status_set.py (_cached_states_by_path, _cached_state_for_path, _state_for_record) and agent_workflows/check_engine.py (_meta_state_for_path, graduation_artifact_index, _close_date_for_item, and sibling readers) call project_context.resolve_project_context(target_repo=str(repo_root)) without falling back to artifact_meta.legacy_context(repo_root) when records_root does not exist and repo_root/.aw/records exists (the fallback already added to check_engine._meta_state_map and ipd_lint._meta_context_and_state_map by hdwqex). On bare repositories without .aw/config/ (under AW_HOME), they miss companion logs under repo/.aw/records/meta/, fall back to read_text on the two-key YAML mirror, and read None for non-mirror fields (set_id, blocks_release, from_backlog, gate_summary). Observed blocking 5 tests in cugg3w batch A (test_artifact_meta_loader_parity.py and test_backlog.py).
