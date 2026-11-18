- Id: 63v9ph
- Status: open
- Set: metastore
- Work-Kind: bug
- Priority: medium
- Summary: Skip README.md in artifact_meta.check_freshness records_root walk so README files are not indexed as id-less artifacts
- Short-Description: Skip README.md in artifact_meta.check_freshness records_root walk so README files are not indexed as id-less artifacts
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-18 created (aw backlog): Skip README.md in artifact_meta.check_freshness records_root walk so README files are not indexed as id-less artifacts

In agent_workflows/artifact_meta.py::check_freshness, the extra_root_dirs walk skips selectors._SKIP_NAMES (README.md, INDEX.md, STATUS.md), whereas the records_root walk skips only dotfiles, INDEX.*, and STATUS.md. When legacy_agents_layout migrates .agents/plans/README.md to .aw/records/plans/README.md, artifact_meta.query indexes plans/README.md as an ipd artifact with a derived id6 and status None. Add README.md to the records_root skip check in check_freshness.
