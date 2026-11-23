- Id: vl3pvt
- Status: done
- Set: vl3pvt
- Work-Kind: bug
- Priority: high
- Summary: aw oc run lane turn starts the agent shell in the main checkout rather than the lane worktree, so edits made without an explicit workdir land in main (observed run-20261123T035302Z-2681364 item 145-mv0j4k)
- Short-Description: aw oc run lane turn starts the agent shell in the main checkout rather than the lane worktree, so edits made without an explicit workdir land in main (observed run-20261123T035302Z-2681364 item 145-mv0j4k)

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-23 done (aw set): Fixed vl3pvt in 1f192e7c0: strip inherited PWD/OLDPWD in oc_runipd.run_opencode, agy_runipd.run_agy_turn, runner_shared.run_checked, and runner_shared.ask_orchestrator_probe, and pass cwd=agent_dir to observe_opencode_policy; verified with 46 passed tests (incl. tests/test_lane_pwd_isolation.py), mypy clean, and live opencode v2 probe
- 2026-11-23 created (aw backlog): aw oc run lane turn starts the agent shell in the main checkout rather than the lane worktree, so edits made without an explicit workdir land in main (observed run-20261123T035302Z-2681364 item 145-mv0j4k)
