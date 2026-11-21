- Id: 68ympf
- Status: open
- Set: 68ympf
- Work-Kind: bug
- Priority: low
- Summary: perform_coordinator_proposal_file truncates proposal summaries mid-word at 24 characters
- Short-Description: perform_coordinator_proposal_file truncates proposal summaries mid-word at 24 characters
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 created (aw backlog): perform_coordinator_proposal_file truncates proposal summaries mid-word at 24 characters

## Problem

`agent_workflows/runner_shared.py::perform_coordinator_proposal_file` builds the filed proposal summary and IPD title by slicing `proposed_change` at 24 characters (`[:24]`) without stopping at a word boundary. By contrast, `_write_fallback_record` in the same function uses a 60-character budget (`[:60]`).

## Observed evidence

In `run-20261121T014040Z-2638602`, proposal `735ium` from IPD `60mazt` received `- Summary: Proposal from 60mazt: Create and execute a sco` and filename slug `proposal-from-60mazt-create-and-execute-a-sco`.

## Fix direction

1. Update `agent_workflows/runner_shared.py::perform_coordinator_proposal_file` to use a word-boundary truncation helper with a budget consistent with `_write_fallback_record` so filed proposal summaries and slugs do not split words mid-token.
2. Add a behavioral test verifying that a multi-word `proposed_change` longer than 24 characters produces a filed proposal summary and slug that end on a complete word.
