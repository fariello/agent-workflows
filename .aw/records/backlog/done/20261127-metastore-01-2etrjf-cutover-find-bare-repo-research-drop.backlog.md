- Id: 2etrjf
- Status: done
- Close-Evidence: .aw/records/plans/executed/20261127-metastore-322-6cltab-populate-cli-creator-log-fields-and-align-aw-find-bare-repo.ipd.md
- Set: metastore
- Work-Kind: bug
- Priority: high
- Summary: Post-cutover cli._find_type_records uses resolve_project_context instead of legacy_context, dropping research records in aw find on bare repos (see ggp2pf)
- Short-Description: Post-cutover cli._find_type_records uses resolve_project_context instead of legacy_context, dropping research records in aw find on bare repos (see ggp2pf)
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-27 done (aw set): Fixed and validated by executed Order 322 plan 6cltab (E-03/V-03, E-04/V-04).
- 2026-11-27 blocked (aw set): covered by Order 322 child plan 6cltab (single-valued From-Backlog carries 0b3ynm)
- 2026-11-27 created (aw backlog): Post-cutover cli._find_type_records uses resolve_project_context instead of legacy_context, dropping research records in aw find on bare repos (see ggp2pf)

In agent_workflows/cli.py::_find_type_records, resolve_project_context(target_repo=...) places logical_roots['records'] under AW_HOME instead of repo/.aw/records for bare repos without .aw/config/ (see ggp2pf). Post-cutover, artifact_meta.query marks in-repo records as orphans and the research branch (if st is None or st.id_derived: continue) drops them from aw find -p, breaking tests/test_record_builder_slow.py::test_visibility_find_attention_check.
