- Id: hwaukk
- Status: open
- Blocks-Release: next
- Set: specaudit
- Priority: medium
- Work-Kind: bug
- Summary: Amend spec 77tr3o R-2 and AGENTS.md for terminal-child orchestrator retirement (31y86f)

## Workflow history
- 2026-10-25 created (aw backlog): Filed 2026-10-25 from the spec audit (session report).

Since backlog 31y86f (commit 65e51ec0, 2026-09-24) evaluate_set_retirement (runner_shared.py ~20399) retires an orchestrator when every child is executed, superseded or not-executed. Spec 77tr3o R-2 still says only executed qualifies, and AGENTS.md line 45 (generated from agent_workflows/engine.py, the managed aw:block) says retirement is gated on 'EVERY child being executed and on nothing else qualifying', which is false and misinforms agents about runner behavior. Amend R-2 citing 31y86f, fix the engine.py source text and regenerate AGENTS.md, then 77tr3o can move to implemented (R-1..R-13 otherwise verified 2026-10-25, 90 tests passed). User-perceptible: agents relying on AGENTS.md give wrong advice about which Sets retire.
