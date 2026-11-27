- Id: tjfc7p
- Status: blocked
- Gate-Kind: artifact
- Gate-Ref: ztvubn
- Set: metastore
- Work-Kind: bug
- Priority: high
- Summary: Driver graduation and spec-planning commit helpers exclude meta JSONL logs as out-of-scope or omit them from transition commits
- Short-Description: Driver graduation and spec-planning commit helpers exclude meta JSONL logs as out-of-scope or omit them from transition commits
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-27 blocked (aw set): Covered by Order 323 child plan ztvubn (single-valued From-Backlog carries 2zknl8).
- 2026-11-27 created (aw backlog): Driver graduation and spec-planning commit helpers exclude meta JSONL logs as out-of-scope or omit them from transition commits

In the metadata-store cutover code patch (.aw/system/cutover/metastore-code.cutover.patch), four path-scoped commit helpers in agent_workflows/runner_shared.py do not include companion .aw/records/meta/<id6>.jsonl event logs: commit_spec_production_output (line 4795) and commit_backlog_production_output (line 5024) allow only .ipd.md files under /plans/pending/ and classify sibling meta/<id6>.jsonl files as out_of_scope; commit_spec_transition_output (line 4932) allows only .spec.md; commit_backlog_transition_output (line 5161) allows only .backlog.md. This strands or drops event logs on lane branches during graduation and spec-planning runs. Discovered during IPD psm9ac; blocks tests/test_gradcover_end_to_end.py (test_e01_e06_e07_success_path_graduate_review_orchestrate and test_e03_resume_scenario).
