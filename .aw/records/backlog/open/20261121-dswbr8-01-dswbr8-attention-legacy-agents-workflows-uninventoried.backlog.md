- Id: dswbr8
- Status: open
- Set: dswbr8
- Work-Kind: bug
- Priority: high
- Summary: attention.py legacy .agents/ fallback flags .agents/workflows as uninventoried-tree
- Short-Description: attention.py legacy .agents/ fallback flags .agents/workflows as uninventoried-tree
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 created (aw backlog): attention.py legacy .agents/ fallback flags .agents/workflows as uninventoried-tree

## Observed behavior

Running `aw att` (with agent-workflows 1.3.0rc2) on a target repository still on the legacy 1.2.1 `.agents/` layout reports:

```text
VIEW INVALID: contract violations must be resolved before this board is authoritative.
  ! .agents/workflows: attention.uninventoried-tree: tree directory under records root matching no policy
```

## Root cause

In `agent_workflows/attention.py` (lines 846-865), when `.aw/records` does not exist, shallow tree discovery falls back to `records_dir = repo_root / '.agents'` and checks every subdirectory against `TREE_POLICY` (`agent_workflows/attention_contract.py`). `TREE_POLICY` lists only records trees (`specs`, `plans`, `research`, `backlog`, `prompts`, etc.) and does not include the legacy framework system directory `.agents/workflows`.

## Expected behavior

When falling back to the legacy `.agents/` directory, `attention.py` should skip `.agents/workflows` (the legacy system tree) so legacy 1.2.1 target repositories do not fail `aw att` solely for still being on the legacy layout.
