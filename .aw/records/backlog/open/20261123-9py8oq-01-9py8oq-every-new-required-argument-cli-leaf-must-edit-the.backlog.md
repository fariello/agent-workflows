- Id: 9py8oq
- Status: open
- Set: 9py8oq
- Work-Kind: followup
- Priority: low
- Summary: Every new required-argument CLI leaf must edit the hardcoded REQUIRED_LEAVES count in tests/test_usage_refusal_agent_record.py, which plans never list in Scope-Paths (hit by h06gs7, a5ijjx, 724acb)
- Short-Description: Every new required-argument CLI leaf must edit the hardcoded REQUIRED_LEAVES count in tests/test_usage_refusal_agent_record.py, which plans never list in Scope-Paths (hit by h06gs7, a5ijjx, 724acb)

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-23 created (aw backlog): Every new required-argument CLI leaf must edit the hardcoded REQUIRED_LEAVES count in tests/test_usage_refusal_agent_record.py, which plans never list in Scope-Paths (hit by h06gs7, a5ijjx, 724acb)

## Problem

`tests/test_usage_refusal_agent_record.py::test_exclusion_set_size_and_members` asserts a hardcoded count of parser leaves that take a required argument (`assert len(REQUIRED_LEAVES) == 72`). The parametrized test beside it already checks every such leaf's agent and JSON refusal behavior. The count adds only one thing: any plan that adds a required-argument leaf fails the core tier unless it also edits this file. Plans rarely list the file in `- Scope-Paths:`, so the edit shows up as `check.scope-drift` and needs a `--scope-reason`, or it lands on `main` as a failing test.

Observed three times:

- `h06gs7` (`describe`, count 69 -> 70)
- `a5ijjx` (`meta repair`, count 69 -> 70; it reached `main` failing, see backlog `517n5n`)
- `724acb` (`reviews record` and `walkthrough new`, count 70 -> 72; justified with `--scope-reason`)

## Expected behavior

Choose one:

1. Drop the exact-count assertion. The per-leaf parametrized test already covers each leaf's behavior.
2. Keep the count visible, but derive the expected value from `command_surface` declarations rather than a literal.

Either way, adding a required-argument leaf should no longer need an out-of-scope test edit.

## Discovery context

Found while executing IPD `724acb` (run `run-20261123T035302Z-2681364`). The first conformance run failed with `assert 72 == 70`.
