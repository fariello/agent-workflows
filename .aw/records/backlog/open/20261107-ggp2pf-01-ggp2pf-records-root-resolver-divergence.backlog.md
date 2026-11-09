- Id: ggp2pf
- Status: open
- Blocks-Release: next
- Set: ggp2pf
- Priority: medium
- Work-Kind: bug
- Summary: For a bare repo, resolve_project_context puts the records root under the AW_HOME companion dir while record verbs read project_records_dir, so artifact_meta callers using the full resolver can read a different tree than aw find

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-09 note (aw backlog): proofread per the technical writing standard (spec ecmw83 R-08); meaning unchanged
- 2026-11-07 created (aw backlog): For a bare repo, resolve_project_context puts the records root under the AW_HOME companion dir while record verbs read project_records_dir, so artifact_meta callers using the full resolver can read a different tree than aw find
