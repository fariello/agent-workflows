- Id: nwz9nd
- Status: done
- Close-Evidence: .aw/records/plans/executed/20261127-metastore-323-ztvubn-fix-post-cutover-status-set-selectors-and-runner-commit-log.ipd.md
- Set: metastore
- Work-Kind: bug
- Priority: high
- Summary: selectors._cached_states_by_path lacks in-tree meta fallback on unregistered repos, breaking setid resolution
- Short-Description: selectors._cached_states_by_path lacks in-tree meta fallback on unregistered repos, breaking setid resolution
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-28 done (aw set): Fixed and validated by executed Order 323 plan ztvubn.
- 2026-11-27 blocked (aw set): Covered by Order 323 child plan ztvubn (single-valued From-Backlog carries 2zknl8).
- 2026-11-27 created (aw backlog): selectors._cached_states_by_path lacks in-tree meta fallback on unregistered repos, breaking setid resolution

In the metadata-store cutover code patch (.aw/system/cutover/metastore-code.cutover.patch), agent_workflows/selectors.py::_cached_states_by_path (around lines 860-895) calls project_context.resolve_project_context without falling back to artifact_meta.legacy_context(repo_root) when repo_root/.aw/records/meta/ exists on a repository that has no AW_HOME project registration (unlike check_engine._meta_context_for_repo). On unregistered or newly cloned log-format repositories, records_root points to a nonexistent AW_HOME path, _cached_states_by_path returns {}, and selectors.resolve falls back to reading the two-field YAML mirror (which omits set), causing MATCH_SETID to miss and fall through to MATCH_SUBSTRING. This breaks runner_shared.read_set_membership and orchestrator_readiness.review_readiness. Discovered during IPD psm9ac; blocks tests/test_gradcover_end_to_end.py (test_e05_one_predicate_parity and test_e01_e06_e07_success_path_graduate_review_orchestrate).
