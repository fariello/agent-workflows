- Id: 4uw2a6
- Status: done
- Graduated-To: cleantgt
- Blocks-Release: next
- Set: cleantgt
- Priority: medium
- Work-Kind: bug
- Summary: route record-file-to-root walkers for records living under AW_HOME

## Workflow history
- 2026-10-17 done (aw backlog): closed by aw agy run: IPD ki6t17 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261016-cleantgt-08-ki6t17-reverse-map-record-files-under-aw-home-to-their-owning-repos.ipd.md); evidence .aw/records/plans/executed/20261016-cleantgt-08-ki6t17-reverse-map-record-files-under-aw-home-to-their-owning-repos.ipd.md
- 2026-10-16 graduated (aw backlog): graduated by run run-20261016T145446Z-2140972: ki6t17
- 2026-10-16 created (aw backlog): route record-file-to-root walkers for records living under AW_HOME

Record-file-to-root walkers (`artifact_core.repo_root_of`, `specs._repo_root_of`, `status_set._repo_root_of`, `record_placement._find_repo_root`, `ipd_lint.lint_file`, `orchestrator_readiness.run_coverage`, `check_engine._identity_rename_hint`) climb parent directories looking for `.aw`, `.agents`, or `.git`. When records live under `AW_HOME/projects/<id>/records/` (e.g. clean-target mode with `records_backend: home`), climbing upward from a record file does not encounter the target repository root. They need a mechanism to reverse-map or resolve the owning repository root when starting from a record path under `AW_HOME`.
