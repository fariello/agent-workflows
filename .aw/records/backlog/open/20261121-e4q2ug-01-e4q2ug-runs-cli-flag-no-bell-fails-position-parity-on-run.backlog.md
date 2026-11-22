- Id: e4q2ug
- Status: open
- Set: e4q2ug
- Work-Kind: bug
- Priority: medium
- Summary: runs CLI flag --no-bell fails position parity on runs show subcommand
- Short-Description: runs CLI flag --no-bell fails position parity on runs show subcommand
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 created (aw backlog): runs CLI flag --no-bell fails position parity on runs show subcommand

Observed during aw suite --thorough (epsj2v validation): tests/test_runs_flag_position_parity.py::RunsFlagPositionParityTests::test_runs_leaf_flag_position_parity fails because ['runs', '--no-bell', 'show', 'run-1'] parses no_bell=False while ['runs', 'show', 'run-1', '--no-bell'] parses no_bell=True.
