- Id: tg3v86
- Status: done
- Set: tg3v86
- Work-Kind: bug
- Priority: medium
- Summary: Live statusline StreamTracker resets spend and tokens to zero on driver restart/resume, causing misleading Spend and $/item
- Short-Description: Live statusline StreamTracker resets spend and tokens to zero on driver restart/resume, causing misleading Spend and $/item

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-23 done (aw set): Fixed directly per maintainer instruction (commit 83eaa979d): seeded StreamTracker on restart, fixed $/item denominator, split dep-blocked tally, full activity/IPD labels, unified OC col 5
- 2026-11-23 created (aw backlog): Live statusline StreamTracker resets spend and tokens to zero on driver restart/resume, causing misleading Spend and $/item

Observed on run-20261123T035302Z-2681364 (driver_restarts=14): live statusline displayed $2.75 / 4.2m tokens / $0.03/item at item 84/86 while persisted session logs summed to $124.44 / 217.55M tokens and aw runs reported $119.55 / 204.68M tokens. Root cause: agent_workflows/oc_runipd.py (run_queue, line 4121) and agent_workflows/agy_runipd.py (run_queue, line 3448) construct a fresh empty StreamTracker() on every restart/resume without seeding prior step usage from state['queue'] or persisted telemetry, and agent_workflows/statusline_layout.py (line 1256) divides that post-restart-only cost by cumulative current_idx (avg_cost = cost / max(1, current_idx)). Fix: seed StreamTracker from persisted run usage on run_queue entry in both drivers and add regression tests covering restart/resume continuity.
