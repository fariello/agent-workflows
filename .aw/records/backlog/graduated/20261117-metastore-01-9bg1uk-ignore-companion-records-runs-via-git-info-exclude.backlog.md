- Id: 9bg1uk
- Status: graduated
- Graduated-To: 9bg1uk
- Set: metastore
- Work-Kind: bug
- Priority: low
- Summary: Ignore companion records/runs/ via git info/exclude in m0001_metadata_v2._ensure_state_gitignored_via_exclude
- Short-Description: Ignore companion records/runs/ via git info/exclude in m0001_metadata_v2._ensure_state_gitignored_via_exclude
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-19 graduated (aw backlog): graduated by run run-20261119T154236Z-4175033: dvxh1p
- 2026-11-18 created (aw backlog): Ignore companion records/runs/ via git info/exclude in m0001_metadata_v2._ensure_state_gitignored_via_exclude

In agent_workflows/migrations/m0001_metadata_v2.py::_ensure_state_gitignored_via_exclude, apply=True checks only <repo>/.aw/records/runs for the integration lock directory. On a companion_backend repository whose companion repository lacks a .gitignore entry for records/runs/, acquiring the integration lock leaves an untracked records/runs/ directory in the companion repository after aw migrate metadata --apply. Resolve the git root of lock_path with project_context.record_git_root and exclude its relative path via info/exclude when unignored.
