- Id: gzmr54
- Status: open
- Set: gzmr54
- Priority: medium
- Work-Kind: followup
- Summary: The six remaining test classes commit 19313eed deleted from tests/test_docs.py are unrestored, leaving agent_workflows/docs_check.py and docs_render.py with no test caller at all

## Workflow history
- 2026-09-28 created (aw backlog): Filed at authoring of plan fzueyy (wfartgrowth-01) as the carrier for its Deferred row. fzueyy restores only the run-scratch path guard from that file; the docs-exist, unicode-dash, support-table, model-profile, benchmark-threshold and analytics-privacy classes are a separate decision. rg 'docs_check|docs_render' tests/ returns nothing.
