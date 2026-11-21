- Id: 2biutm
- Status: graduated
- Graduated-To: 2biutm
- Set: 2biutm
- Work-Kind: bug
- Priority: high
- Summary: layout_inventory routes legacy workflow-artifacts/ into .aw/records/ instead of .aw/workflow-artifacts/
- Short-Description: layout_inventory routes legacy workflow-artifacts/ into .aw/records/ instead of .aw/workflow-artifacts/
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 graduated (aw backlog): graduated by run run-20261121T210815Z-1170144: 0hdqbw
- 2026-11-21 created (aw backlog): layout_inventory routes legacy workflow-artifacts/ into .aw/records/ instead of .aw/workflow-artifacts/

## Observed behavior

Migrating a legacy 1.2.1 repository that has tracked repo-root `workflow-artifacts/<workflow>/<run-id>/` directories to `.aw/` moves those directories directly into `.aw/records/<workflow>/` (e.g. `.aw/records/assess-bugs`, `.aw/records/advise-architect`, `.aw/records/plan-review`). Immediately afterward, `aw att` reports `attention.uninventoried-tree` for every migrated workflow directory under `.aw/records/`.

## Root cause

`agent_workflows/layout_inventory.py` (lines 175-181) classifies `label == 'workflow-artifacts'` with `ownership: 'records'`, `lifecycle_class: 'records'`, and `expected_destination_class: 'records'`. However, `agent_workflows/engine.py` (line 256, `ARTIFACTS_DIR = '.aw/workflow-artifacts/'`) and `agent_workflows/record_producers.py` (line 138) define run artifacts as living in the gitignored sibling directory `.aw/workflow-artifacts/<workflow>/<run-id>/`, not inside `.aw/records/`.

## Expected behavior

Layout migration should route legacy `workflow-artifacts/` to `.aw/workflow-artifacts/` (or untrack/archive it cleanly per the `.aw/workflow-artifacts/` contract), never into `.aw/records/`, so `aw att` is valid immediately after migration.
