- Id: 7mmhlp
- Status: open
- Set: 7mmhlp
- Work-Kind: bug
- Priority: medium
- Summary: aw find drops migrated legacy research records whose minted filenames lack a research kind facet even when queried by minted id6
- Short-Description: aw find drops migrated legacy research records whose minted filenames lack a research kind facet even when queried by minted id6
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 created (aw backlog): aw find drops migrated legacy research records whose minted filenames lack a research kind facet even when queried by minted id6


## Problem

`agent_workflows/cli.py::_find_type_records` skips any file in the `research` tree whose filename returns `None` from `agent_workflows/research_contract.py::parse_name`. When `aw migrate metadata` mints an `id6` for a legacy research note whose filename lacks a `.<kind>.md` facet (such as `.agents/docs/research/20260708-survey-notes.md` in `tests/migration_corpus.py::legacy_agents_layout`), `m0001_renames` renames it to `research/20260708-<id6>-01-<id6>-survey-notes.md` without a kind facet.

After migration, querying `aw find <minted_id6> --agent` resolves the selector through `selectors` (so the command exits 0 instead of 2), but `_find_type_records` then drops the row because `research_contract.parse_name` returns `None`, emitting `total: 0` with zero items.

Measured during IPD `60mazt` execution on `legacy_agents_layout`: `aw find <minted_id6> --agent` for migrated `20260708-<id6>-01-<id6>-survey-notes.md` exited 0 with `total: 0, emitted: 0`, whereas `artifact_meta.query` returned the migrated research row cleanly.

## Fix direction

1. Decide whether `agent_workflows/cli.py::_find_type_records` (research branch) should fall back to `artifact_meta.State` metadata (`id6`, `set_id`, `order_nn`) when a migrated research record exists in `state_by_path` with `not st.id_derived` even if `research_contract.parse_name` returns `None`, or whether `m0001_renames` should assign a conformant research kind facet during legacy research renaming.
2. Add a behavioral test verifying `aw find <minted_id6> --agent` returns the migrated legacy research record with `total: 1`.
