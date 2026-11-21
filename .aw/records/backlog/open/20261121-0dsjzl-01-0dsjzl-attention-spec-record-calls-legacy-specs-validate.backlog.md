- Id: 0dsjzl
- Status: open
- Set: 0dsjzl
- Work-Kind: bug
- Priority: high
- Summary: attention._spec_record calls legacy specs.validate_spec on v2 log-format specs causing false missing-status and history-missing violations
- Short-Description: attention._spec_record calls legacy specs.validate_spec on v2 log-format specs causing false missing-status and history-missing violations
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 created (aw backlog): attention._spec_record calls legacy specs.validate_spec on v2 log-format specs causing false missing-status and history-missing violations


## Problem

`agent_workflows/attention.py::_spec_record` calls `agent_workflows/specs.py::validate_spec(path, text)` unconditionally on every specification file, even when `state` comes from a migrated metadata-v2 event log (`meta/<id6>.jsonl`). `specs.validate_spec` parses legacy Markdown bullets (`- Status:`, `- Gate-Kind:`, `- Gate-Ref:`, `- Gate-Summary:`, `- Priority:`, `- Work-Kind:`) and `## Workflow history` directly from the Markdown body.

After `aw migrate metadata --apply` strips those metadata bullets and history lines into `meta/<id6>.jsonl`, `_spec_record` reads the migrated status, gate, priority, and `last_history_at` from `artifact_meta.State`, but `specs.validate_spec` still reports false violations on the stripped Markdown body:

- `attention.missing-status`: `no bare-enum \`- Status:\` bullet`
- `attention.history-missing`: `no conformant \`## Workflow history\` record`
- `attention.gate-missing` for any migrated `deferred` specification

Measured during IPD `60mazt` execution:

- On a disposable `git clone --no-hardlinks` of this repository: `aw attention --all --format json` had 0 violations (`valid: true`) before migration and gained 100 false violations (`50 attention.missing-status` and `50 attention.history-missing`) across all 50 migrated specifications after migration.
- On the `no_sidecar` corpus fixture (`qa1z06`): `aw attention --format json` exited 0 (`valid: true`) before migration and exited 1 (`valid: false`) after migration with both `attention.missing-status` and `attention.history-missing`, even while emitting `native_status: "approved"` and `last_history_at: "2026-08-20"` for `qa1z06`.
- On `mixed_layout` (`qa1z05`) and `legacy_agents_layout`: migrated specifications gained false `attention.missing-status` violations.

## Fix direction

1. Detect v2 log-backed specification state in `agent_workflows/attention.py::_spec_record` (matching the pattern used by `agent_workflows/attention.py::_research_record`, where `state.created_at` or `state.updated_at` is set) or add a state-aware validator in `agent_workflows/specs.py`.
2. For log-backed specifications, validate status enum membership, deferred gate rules (`gate_kind`, `gate_ref`, `gate_summary`), descriptive safety (`scope`, `summary`), optional `priority` and `work_kind` vocabularies, and workflow history presence against `artifact_meta.State` and `artifact_meta.history` instead of parsing stripped Markdown bullets.
3. Add behavioral regression tests confirming `aw attention --format json` returns `valid: true` with zero false `attention.missing-status`, `attention.history-missing`, or `attention.gate-missing` violations on migrated specifications, while preserving all legacy Markdown spec checks.
