- Id: ujxi56
- Status: graduated
- Graduated-To: ujxi56
- Set: pubrun-bugs
- Work-Kind: bug
- Priority: high
- Summary: Fix --to-aw layout migration moving workflow-artifacts/* and .agents/docs/README.md into uninventoried .aw/records/* trees
- Short-Description: Fix --to-aw layout migration moving workflow-artifacts/* and .agents/docs/README.md into uninventoried .aw/records/* trees
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 graduated (aw backlog): graduated by run run-20261122T002647Z-1444530: qpvem9
- 2026-11-22 created (aw backlog): Fix --to-aw layout migration moving workflow-artifacts/* and .agents/docs/README.md into uninventoried .aw/records/* trees


## Context and observed behavior

Running `aw install --to-aw` on a legacy `.agents/` repository containing `workflow-artifacts/` and `.agents/docs/README.md` (`pubrun`, commit `3f01e99f`) immediately broke `aw attention` with 11 `attention.uninventoried-tree` contract violations (`VIEW INVALID`):

1. `agent_workflows/layout_inventory.py` classifies `label == "workflow-artifacts"` with `expected_destination_class: "records"` and no `destination_relpath_override`, stripping the `workflow-artifacts/` prefix and moving every run subdirectory (`advise-architect`, `assess-bugs`, `plan-review`, etc.) directly into `.aw/records/<workflow>/` instead of `.aw/workflow-artifacts/<workflow>/`.
2. `.agents/docs/README.md` was moved to `.aw/records/docs/README.md` even though `.agents/docs/{specs,research,walkthroughs,roadmaps}` were flattened directly under `.aw/records/`, creating a stray uninventoried `.aw/records/docs/` directory.

## Acceptance criteria

- `aw install --to-aw` relocates legacy `workflow-artifacts/` under `.aw/workflow-artifacts/` (gitignored scratch home, outside `.aw/records/`) so no uninventoried directories are created under `.aw/records/`.
- `aw install --to-aw` does not create `.aw/records/docs/` from legacy `.agents/docs/README.md`.
- Behavioral tests verify `aw install --to-aw` on a legacy repo containing `workflow-artifacts/assess-bugs/...` and `.agents/docs/README.md` leaves `aw attention --check` valid with 0 `attention.uninventoried-tree` findings.
