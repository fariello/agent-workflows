- Id: 4j0eug
- Status: open
- Set: 4j0eug
- Work-Kind: bug
- Priority: high
- Summary: Cross-host review-sweep resume fails valid reviews with 'Review sweep changed session unexpectedly'
- Short-Description: Cross-host review-sweep resume fails valid reviews with 'Review sweep changed session unexpectedly'
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-26 created (aw backlog): Cross-host review-sweep resume fails valid reviews with 'Review sweep changed session unexpectedly'

When a review-sweep run starts on one host (for example OpenCode via aw oc run, recording an OpenCode ses_... ID in state[REVIEW_SWEEP_SESSION_KEY]) and is later resumed on a different host (for example Antigravity via aw agy run resume, which cannot resume a ses_... ID and creates a fresh UUID session), each resumed review turn runs to completion and commits valid hardened .ipd.md and .review.md files in the review-sweep worktree, and then runner_shared.py (around lines 48821-48848, REVIEW_SWEEP_SESSION_KEY check) raises DriverError: 'Review sweep changed session unexpectedly: ses_... -> <uuid>' BEFORE updating state[REVIEW_SWEEP_SESSION_KEY]. As a result, every subsequent item in the sweep also fails-safely and strands valid reviewed commits in the kept review-sweep worktree (observed in pubrun run-20261125T201949Z-2043121 on wjsccu, 77pdvl, and 2uwuiu, causing orchestrator 86cd17 to fail-depend). Note that runner_shared.py lines 47319-47332 reuse state[REVIEW_SWEEP_SESSION_KEY] without checking whether the recorded session belongs to the current host, and lines 48849-48862 have the same host-unaware check on set_sessions for non-isolated runs. Fix: track the owning host alongside review_sweep_session (and set_sessions), clear/rotate the stored session cleanly on a cross-host resume (recording a host-switch event rather than passing an incompatible foreign session ID or raising DriverError), and add a regression test covering OpenCode-to-Antigravity (and Antigravity-to-OpenCode) resume in a review sweep.
